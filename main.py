from gnews import GNews
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import csv
import os
from datetime import datetime
import time

# Buat folder output jika belum ada
OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class NewsScraperWithSelenium:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def scrape_google_news(self, keyword, language='id', country='ID', period='7d', max_results=10):
        google_news = GNews(
            language=language,
            country=country,
            period=period,
            max_results=max_results
        )
        return google_news.get_news(keyword)
    
    def get_full_article(self, url):
        """Extract artikel menggunakan Selenium"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Wait for dynamic content
            
            # Get final URL after redirect
            final_url = self.driver.current_url
            
            # Skip if still Google News
            if 'google.com' in final_url:
                return None
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                tag.decompose()
            
            # Try multiple selectors
            content = None
            selectors = [
                'article',
                '[itemprop="articleBody"]',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main article',
                '.detail-content',
                '#article-content'
            ]
            
            for selector in selectors:
                try:
                    content = soup.select_one(selector)
                    if content and len(content.get_text().strip()) > 200:
                        break
                except:
                    continue
            
            if not content:
                content = soup.find('body')
            
            # Extract text
            paragraphs = content.find_all(['p', 'h1', 'h2', 'h3']) if content else []
            text = '\n\n'.join(
                p.get_text().strip() 
                for p in paragraphs 
                if len(p.get_text().strip()) > 30
            )
            
            # Get title
            title = soup.find('h1')
            if not title:
                title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            return {
                'title': title_text,
                'text': text,
                'url': final_url,
                'status': 'success'
            }
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def export_to_json(self, articles, filename=None):
        if filename is None:
            filename = f"{OUTPUT_DIR}/news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ JSON exported: {filename}")
        return filename
    
    def export_to_csv(self, articles, filename=None):
        if filename is None:
            filename = f"{OUTPUT_DIR}/news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'no', 'title', 'publisher', 'published_date', 
                'original_url', 'final_url', 'description', 'full_text'
            ])
            writer.writeheader()
            
            for i, article in enumerate(articles, 1):
                writer.writerow({
                    'no': i,
                    'title': article.get('title', ''),
                    'publisher': article.get('publisher', ''),
                    'published_date': article.get('published_date', ''),
                    'original_url': article.get('original_url', ''),
                    'final_url': article.get('final_url', ''),
                    'description': article.get('description', ''),
                    'full_text': article.get('full_text', '')
                })
        
        print(f"✓ CSV exported: {filename}")
        return filename
    
    def close(self):
        self.driver.quit()


# Main execution
if __name__ == "__main__":
    scraper = NewsScraperWithSelenium()
    
    try:
        keyword = "ASABRI"
        print(f"Mencari berita: {keyword}\n{'='*80}")
        
        results = scraper.scrape_google_news(
            keyword=keyword,
            language='id',
            country='ID',
            period='14d',  # 1 bulan untuk hasil lebih banyak
            max_results=20
        )
        
        all_articles = []
        
        for i, article in enumerate(results, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Publisher: {article['publisher']['title']}")
            print(f"   Published: {article['published date']}")
            
            # Extract full article
            print(f"   Extracting...")
            full = scraper.get_full_article(article['url'])
            
            article_data = {
                'title': article['title'],
                'publisher': article['publisher']['title'],
                'published_date': article['published date'],
                'original_url': article['url'],
                'description': article['description'],
                'full_text': '',
                'final_url': ''
            }
            
            if full and full.get('text'):
                article_data['full_text'] = full['text']
                article_data['final_url'] = full['url']
                print(f"   ✓ Extracted: {len(full['text'])} chars")
            else:
                print(f"   ✗ Failed to extract")
            
            all_articles.append(article_data)
            print("-"*80)
        
        # Export results
        print(f"\n{'='*80}\nEXPORTING...")
        scraper.export_to_json(all_articles)
        scraper.export_to_csv(all_articles)
        
        success_count = sum(1 for a in all_articles if a['full_text'])
        print(f"\n✓ Total: {len(all_articles)} articles")
        print(f"✓ Successfully extracted: {success_count} articles")
        
    finally:
        scraper.close()