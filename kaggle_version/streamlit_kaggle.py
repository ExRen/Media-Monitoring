import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import medmon_kaggle as medmon # Import Kaggle version
import db_kaggle as db          # Import Kaggle version
import sys
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
# Visualization Libraries
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# PageConfig must be the first Streamlit command
st.set_page_config(
    page_title="MedMon v3.0 (Kaggle Edition)",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #FF914D 0%, #FF4B4B 100%);
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .keyword-tag {
        display: inline-block;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 12px;
        border-radius: 15px;
        margin: 3px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database on first run
try:
    db.init_database()
except Exception as e:
    st.error(f"Database Error: {e}")

# Session State Initialization
if 'results' not in st.session_state:
    st.session_state.results = []
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False
if 'terminal_logs' not in st.session_state:
    st.session_state.terminal_logs = ""
if 'active_keywords' not in st.session_state:
    st.session_state.active_keywords = []

# Load keywords from database
def load_keywords():
    try:
        keywords = db.get_keywords()
        st.session_state.active_keywords = [k['keyword'] for k in keywords]
    except:
        st.session_state.active_keywords = []

load_keywords()

# Logger class
class StreamlitLogger:
    def __init__(self):
        self.log_buffer = []

    def write(self, message):
        self.log_buffer.append(message)

    def flush(self):
        pass
    
    def get_logs(self):
        return "".join(self.log_buffer)

# Helper function for threading
def process_single_article(news_item, keyword_id, keyword):
    """
    Returns tuple: (article_data, status)
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
        print(f"[!] Error: {e}")
    return (None, "failed")

# Sidebar Configuration
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=60)
    st.title("MedMon Kaggle")
    st.markdown("---")
    
    # Multi-Keyword Management
    st.subheader("📌 Keyword Management")
    
    # Display existing keywords
    if st.session_state.active_keywords:
        st.markdown("**Active Keywords:**")
        keywords_html = "".join([f'<span class="keyword-tag">{k}</span>' for k in st.session_state.active_keywords])
        st.markdown(keywords_html, unsafe_allow_html=True)
    else:
        st.info("Belum ada keyword. Tambahkan di bawah.")
    
    # Add new keyword
    new_keyword = st.text_input("Tambah Keyword Baru", placeholder="e.g. PT ASABRI", key="new_keyword_input")
    if st.button("➕ Tambah Keyword"):
        if new_keyword and new_keyword.strip():
            keyword_clean = new_keyword.strip()
            # Check if already exists
            existing = [k.lower() for k in st.session_state.active_keywords]
            if keyword_clean.lower() in existing:
                st.warning(f"Keyword '{keyword_clean}' sudah ada!")
            else:
                try:
                    db.add_keyword(keyword_clean)
                    st.session_state.active_keywords.append(keyword_clean)
                    st.success(f"✅ Keyword '{keyword_clean}' berhasil ditambahkan!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menambahkan keyword: {e}")
        else:
            st.warning("Masukkan keyword terlebih dahulu!")
    
    st.markdown("---")
    
    # Scraping Config
    st.subheader("⚙️ Scraping Config")
    
    col_lang, col_country = st.columns(2)
    with col_lang:
        language = st.selectbox("Bahasa", options=['id', 'en'], index=0)
    with col_country:
        country = st.selectbox("Negara", options=['ID', 'US'], index=0)
        
    period = st.select_slider("Periode", options=['1h', '1d', '7d', '14d', '1m', '1y'], value='14d')
    max_results = st.number_input("Maks Berita/Keyword", min_value=1, max_value=100, value=10)
    workers = st.slider("Thread Speed", min_value=1, max_value=10, value=5)
    
    st.markdown("---")
    
    # Select keywords to scrape
    keywords_to_scrape = st.multiselect(
        "Pilih Keyword untuk Scrape",
        options=st.session_state.active_keywords,
        default=st.session_state.active_keywords
    )
    
    start_btn = st.button("🚀 Mulai Scraping", disabled=st.session_state.is_scraping or len(keywords_to_scrape) == 0)

# Main Content
st.title("MedMon Analyzer AI (Kaggle)")
st.markdown("Intelligence Media Monitoring Dashboard with Multi-Keyword Tracking")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📈 Trend Analysis", "📝 List Berita", "☁️ Word Cloud", "🖥️ Logs"])

# Scraping Logic
if start_btn:
    st.session_state.is_scraping = True
    st.session_state.results = []
    st.session_state.terminal_logs = ""
    
    with tab5:
        progress_bar = st.progress(0)
        status_text = st.empty()
        terminal_placeholder = st.empty()
    
    try:
        capture = StreamlitLogger()
        original_stdout = sys.stdout
        sys.stdout = capture
        
        all_articles = []
        total_keywords = len(keywords_to_scrape)
        
        for kw_idx, keyword in enumerate(keywords_to_scrape):
            print(f"\n[{kw_idx+1}/{total_keywords}] Processing keyword: {keyword}")
            status_text.markdown(f"### 🔍 Scraping: {keyword}...")
            
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
                    language=language,
                    country=country,
                    period=period,
                    max_results=max_results
                )
                if news_results:
                    break
                elif attempt == 0:
                    print(f"   [!] No results, retrying with simpler keyword...")
                    time.sleep(2)
            
            total_news = len(news_results)
            print(f"   [+] Found {total_news} articles for '{keyword}'")
            
            if total_news == 0:
                print(f"   [!] WARNING: Google News returned 0 results. Try shorter period or simpler keyword.")
            
            keyword_articles = []
            pos_count, neg_count, neu_count = 0, 0, 0
            new_count, dup_count, fail_count, filter_count = 0, 0, 0, 0
            
            # Process articles
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_url = {executor.submit(process_single_article, news, keyword_id, keyword): news for news in news_results}
                
                for i, future in enumerate(as_completed(future_to_url)):
                    progress = ((kw_idx * max_results) + i + 1) / (total_keywords * max_results) if total_keywords * max_results > 0 else 0
                    progress_bar.progress(min(progress, 1.0))
                    
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
                                
                            print(f"   [+] NEW: {data['title'][:40]}... ({data['sentiment_label']})")
                        elif status == "duplicate":
                            dup_count += 1
                            print(f"   [=] DUP: {data['title'][:40] if data else 'Unknown'}...")
                        elif status == "filtered":
                            filter_count += 1
                            print(f"   [~] SKIP: Title no keyword: {data['title'][:35] if data else 'Unknown'}...")
                        else:
                            fail_count += 1
                            print(f"   [X] FAIL: Could not extract article")
                    except Exception as exc:
                        fail_count += 1
                        print(f"   [X] Error: {exc}")
                    
                    st.session_state.terminal_logs = capture.get_logs()
                    terminal_placeholder.code(st.session_state.terminal_logs, language="bash")
            
            # Print stats
            print(f"\n   📊 Stats for '{keyword}':")
            print(f"      • New articles saved: {new_count}")
            print(f"      • Duplicates skipped: {dup_count}")
            print(f"      • Filtered: {filter_count}")
            print(f"      • Failed extractions: {fail_count}")
            
            db.save_scrape_history(keyword_id, total_news, len(keyword_articles), pos_count, neg_count, neu_count)
        
        st.session_state.results = all_articles
        st.session_state.is_scraping = False
        status_text.success(f"🎉 Selesai! Total {len(all_articles)} artikel.")
        progress_bar.progress(100)
        
        print(f"\n[+] FINISHED. Total: {len(all_articles)} articles")
        st.session_state.terminal_logs = capture.get_logs()
        terminal_placeholder.code(st.session_state.terminal_logs, language="bash")
        
    except Exception as e:
        st.error(f"Error: {e}")
        print(f"[!] FATAL: {e}")
        st.session_state.terminal_logs = capture.get_logs()
        st.session_state.is_scraping = False
    finally:
        sys.stdout = original_stdout

# Tab 1: Dashboard
with tab1:
    st.subheader("📊 Overview Dashboard")
    try:
        all_db_articles = db.get_articles(limit=500)
        if all_db_articles:
            df = pd.DataFrame(all_db_articles)
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Artikel", len(df))
            with m2:
                pos = len(df[df['sentiment_label'] == 'Positive']) if 'sentiment_label' in df.columns else 0
                st.metric("Positif", pos)
            with m3:
                neg = len(df[df['sentiment_label'] == 'Negative']) if 'sentiment_label' in df.columns else 0
                st.metric("Negatif", neg)
            with m4:
                unique_kw = df['keyword'].nunique() if 'keyword' in df.columns else 0
                st.metric("Keywords", unique_kw)
            
            st.markdown("### 📊 Perbandingan Keyword")
            comparison = db.get_keyword_comparison()
            if comparison:
                comp_df = pd.DataFrame(comparison)
                st.bar_chart(comp_df.set_index('keyword')[['positive', 'negative']])
        else:
            st.info("Belum ada data. Lakukan scraping terlebih dahulu.")
    except Exception as e:
        st.warning(f"Gagal load data: {e}")

# Tab 2: Trend Analysis
with tab2:
    st.subheader("📈 Trend Analysis")
    try:
        col1, col2 = st.columns(2)
        with col1:
            days_range = st.selectbox("Rentang Waktu", options=[7, 14, 30, 60, 90], index=1)
        with col2:
            trend_keyword = st.selectbox("Filter Keyword", options=["Semua"] + st.session_state.active_keywords)
        
        kw_id = None
        if trend_keyword != "Semua":
            for k in db.get_keywords():
                if k['keyword'] == trend_keyword:
                    kw_id = k['id']
                    break
        
        trend_data = db.get_trend_data(keyword_id=kw_id, days=days_range)
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data)
            trend_df['date'] = pd.to_datetime(trend_df['date'])
            trend_df = trend_df.set_index('date')
            
            st.markdown("#### 📰 Jumlah Artikel per Hari")
            st.line_chart(trend_df['total'])
            
            st.markdown("#### 🎭 Tren Sentimen")
            st.area_chart(trend_df[['positive', 'negative', 'neutral']])
        else:
            st.info("Belum ada data trend.")
    except Exception as e:
        st.warning(f"Error: {e}")

# Tab 3: List Berita
with tab3:
    st.subheader("📝 Daftar Berita")
    try:
        articles = db.get_articles(limit=200)
        if articles:
            df = pd.DataFrame(articles)
            
            filter_kw = st.selectbox("Filter by Keyword", options=["Semua"] + st.session_state.active_keywords, key="filter_list")
            if filter_kw != "Semua":
                df = df[df['keyword'] == filter_kw]
            
            display_cols = ['title', 'keyword', 'publisher', 'publish_date', 'sentiment_label', 'sentiment_score', 'url']
            final_df = df[[c for c in display_cols if c in df.columns]]
            
            st.dataframe(
                final_df,
                column_config={
                    "url": st.column_config.LinkColumn("Link"),
                    "sentiment_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1)
                },
                use_container_width=True
            )
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, f"medmon_kaggle_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("Belum ada data.")
    except Exception as e:
        st.warning(f"Error: {e}")

# Tab 4: Word Cloud
with tab4:
    st.subheader("☁️ Word Cloud")
    try:
        articles = db.get_articles(limit=100)
        if articles:
            # Safely get content, handle different column names if schema changed slightly or just to be safe
            text_combined = " ".join([str(a.get('content', '') or '') for a in articles])
            if text_combined.strip():
                wc = WordCloud(width=800, height=400, background_color='#0E1117', colormap='Reds').generate(text_combined)
                
                fig, ax = plt.subplots(figsize=(10, 5), facecolor='#0E1117')
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.info("Tidak cukup teks untuk Word Cloud.")
        else:
            st.info("Belum ada data.")
    except Exception as e:
        st.warning(f"Error: {e}")

# Tab 5: Logs
with tab5:
    st.subheader("🖥️ Terminal Logs")
    st.code(st.session_state.terminal_logs if st.session_state.terminal_logs else "No logs yet.", language="bash")
