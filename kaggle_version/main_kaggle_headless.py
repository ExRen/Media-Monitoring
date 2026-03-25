import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import medmon_kaggle as medmon
import db_kaggle as db
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# List of keywords to scrape
KEYWORDS = [
    "PT ASABRI",
    "Korupsi ASABRI",
    "Asuransi Sosial Angkatan Bersenjata"
]

# Scraping settings
SCRAPING_CONFIG = {
    "language": "id",     # 'id' for Indonesia, 'en' for English
    "country": "ID",      # 'ID' for Indonesia, 'US' for USA
    "period": "14d",      # '1h', '1d', '7d', '14d', '1m', '1y' (Time range)
    "max_results": 20,    # Max articles per keyword
    "workers": 5          # Number of parallel threads (higher = faster, but risk of rate limit)
}

# Database settings
RESET_DATABASE = False    # Set to True to wipe all data before scraping
# ==========================================

def process_single_article(news_item, keyword_id, keyword):
    """
    Process a single news item: extract content, analyze sentiment, save to DB.
    """
    try:
        # Get the article title from news_item first to filter early
        news_title = news_item.get('title', '')
        
        # Check if keyword appears in title (case-insensitive)
        keyword_lower = keyword.lower()
        title_lower = news_title.lower()
        
        # Check for main keyword or any significant part
        keyword_parts = [k.strip() for k in keyword_lower.split() if len(k.strip()) > 2]
        keyword_found = any(part in title_lower for part in keyword_parts) or keyword_lower in title_lower
        
        if not keyword_found:
            return ({"title": news_title}, "filtered")
        
        full_article = medmon.get_full_article(news_item['url'])
        if full_article:
            # Priority for publish_date
            publish_date = full_article.get('publish_date')
            
            if not publish_date:
                gn_date = news_item.get('published date')
                if gn_date:
                    publish_date = gn_date
            
            full_article['publish_date'] = publish_date
            full_article['publisher'] = news_item.get('publisher', {}).get('title', 'Unknown')
            
            # Sentiment Analysis
            title = full_article.get('title', '')
            content = full_article.get('text', '')
            combined_text = f"{title}. {content}" if content else title
            
            score, label = medmon.analyze_sentiment(combined_text)
            full_article['sentiment_score'] = score
            full_article['sentiment_label'] = label
            
            # Save to database
            save_result = db.save_article(full_article, keyword_id)
            
            if save_result == "duplicate":
                return (full_article, "duplicate")
            elif save_result:
                return (full_article, "new")
            else:
                return (full_article, "failed")
    except Exception as e:
        print(f"[!] Error processing article: {e}")
    return (None, "failed")

def main():
    print("="*60)
    print("   MedMon Headless Scraper (Kaggle Version)")
    print("="*60)
    
    # Initialize Database
    try:
        if RESET_DATABASE:
            try:
                # Close connection if open (handled by context manager usually)
                pass
            except:
                pass
            
            # Simple way to reset: just call clear_all_articles or re-init
            # But db.py doesn't have drop table in init.
            # Let's use db.clear_all_articles() if tables exist
            db.init_database() # Ensure tables exist first
            db.clear_all_articles() # Then clear them
            print("[!] Database CLEARED (RESET_DATABASE=True)")
        else:
            db.init_database()
            print("[+] Database initialized (Appending to existing data).")
    except Exception as e:
        print(f"[!] Database Error: {e}")
        return

    all_articles = []
    total_keywords = len(KEYWORDS)
    
    for kw_idx, keyword in enumerate(KEYWORDS):
        print(f"\n[{kw_idx+1}/{total_keywords}] Processing keyword: {keyword}")
        
        if kw_idx > 0:
            print("   [*] Waiting 3 seconds to avoid rate limiting...")
            time.sleep(3)
        
        # Get or create keyword in DB
        keyword_id = db.add_keyword(keyword)
        
        # Search news with retry
        news_results = []
        for attempt in range(2):
            news_results = medmon.scrape_google_news(
                keyword=keyword,
                language=SCRAPING_CONFIG["language"],
                country=SCRAPING_CONFIG["country"],
                period=SCRAPING_CONFIG["period"],
                max_results=SCRAPING_CONFIG["max_results"]
            )
            if news_results:
                break
            elif attempt == 0:
                print(f"   [!] No results, retrying with simpler keyword...")
                time.sleep(2)
        
        total_news = len(news_results)
        print(f"   [+] Found {total_news} articles for '{keyword}'")
        
        if total_news == 0:
            print(f"   [!] WARNING: Google News returned 0 results.")
            continue
        
        keyword_articles = []
        pos_count, neg_count, neu_count = 0, 0, 0
        new_count, dup_count, fail_count, filter_count = 0, 0, 0, 0
        
        # Process articles
        with ThreadPoolExecutor(max_workers=SCRAPING_CONFIG["workers"]) as executor:
            future_to_url = {executor.submit(process_single_article, news, keyword_id, keyword): news for news in news_results}
            
            for future in as_completed(future_to_url):
                try:
                    data, status = future.result()
                    
                    if status == "new" and data:
                        new_count += 1
                        data['keyword'] = keyword
                        keyword_articles.append(data)
                        all_articles.append(data)
                        
                        if data['sentiment_label'] == 'Positive':
                            pos_count += 1
                        elif data['sentiment_label'] == 'Negative':
                            neg_count += 1
                        else:
                            neu_count += 1
                            
                        print(f"   [+] NEW: {data['title'][:50]}... ({data['sentiment_label']})")
                    elif status == "duplicate":
                        dup_count += 1
                        print(f"   [=] DUP: {data['title'][:50] if data else 'Unknown'}...")
                    elif status == "filtered":
                        filter_count += 1
                        print(f"   [~] SKIP: No keyword in title")
                    else:
                        fail_count += 1
                        print(f"   [X] FAIL: Extraction failed")
                except Exception as exc:
                    fail_count += 1
                    print(f"   [X] Error: {exc}")
        
        # Print stats
        print(f"\n   📊 Stats for '{keyword}':")
        print(f"      • New articles: {new_count}")
        print(f"      • Duplicates: {dup_count}")
        print(f"      • Filtered: {filter_count}")
        print(f"      • Failed: {fail_count}")
        
        db.save_scrape_history(keyword_id, total_news, len(keyword_articles), pos_count, neg_count, neu_count)
        
        # Save per-keyword results to JSON/CSV using medmon_kaggle's helper
        if keyword_articles:
            medmon.save_results(keyword_articles, keyword, output_dir="output")

    print("\n" + "="*60)
    print(f"🎉 FINISHED! Total new articles: {len(all_articles)}")
    print("="*60)

if __name__ == "__main__":
    main()
