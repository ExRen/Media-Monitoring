# import streamlit as st
# import pandas as pd
# import time
# from datetime import datetime, timedelta
# import medmon
# import db
# import sys
# import io
# from concurrent.futures import ThreadPoolExecutor, as_completed
# # Visualization Libraries
# import matplotlib.pyplot as plt
# from wordcloud import WordCloud

# # Page Config
# st.set_page_config(
#     page_title="MedMon v3.0",
#     page_icon="🕵️‍♂️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS
# st.markdown("""
# <style>
#     .main { background-color: #0E1117; }
#     .stButton>button {
#         width: 100%;
#         border-radius: 8px;
#         height: 3em;
#         background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
#         color: white;
#         font-weight: bold;
#         border: none;
#     }
#     .stButton>button:hover {
#         background: linear-gradient(90deg, #FF914D 0%, #FF4B4B 100%);
#         box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
#     }
#     h1 {
#         background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#     }
#     .keyword-tag {
#         display: inline-block;
#         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 5px 12px;
#         border-radius: 15px;
#         margin: 3px;
#         font-size: 14px;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize Database on first run
# try:
#     db.init_database()
# except Exception as e:
#     st.error(f"Database Error: {e}. Pastikan MySQL/Laragon sudah running.")

# # Session State Initialization
# if 'results' not in st.session_state:
#     st.session_state.results = []
# if 'is_scraping' not in st.session_state:
#     st.session_state.is_scraping = False
# if 'terminal_logs' not in st.session_state:
#     st.session_state.terminal_logs = ""
# if 'active_keywords' not in st.session_state:
#     st.session_state.active_keywords = []

# # Auth Session State
# if 'logged_in' not in st.session_state:
#     st.session_state.logged_in = False
# if 'user' not in st.session_state:
#     st.session_state.user = None
# if 'role' not in st.session_state:
#     st.session_state.role = None

# def login():
#     st.title("Login MedMon v3.0")
#     with st.form("login_form"):
#         username = st.text_input("Username")
#         password = st.text_input("Password", type="password")
#         submit = st.form_submit_button("Login")
        
#         if submit:
#             user_data = db.authenticate_user(username, password)
#             if user_data:
#                 st.session_state.logged_in = True
#                 st.session_state.user = user_data['username']
#                 st.session_state.role = user_data['role']
#                 st.rerun()
#             else:
#                 st.error("Username atau password salah")
                
# def logout():
#     st.session_state.logged_in = False
#     st.session_state.user = None
#     st.session_state.role = None
#     st.rerun()

# if not st.session_state.logged_in:
#     login()
#     st.stop()
    
# # Layout for logged in users
# col_title, col_logout = st.columns([8, 1])
# with col_title:
#     st.markdown(f"Selamat datang, **{st.session_state.user}** ({st.session_state.role})")
# with col_logout:
#     if st.button("Logout"):
#         logout()

# def load_keywords():
#     try:
#         keywords = db.get_keywords()
#         st.session_state.active_keywords = [k['keyword'] for k in keywords]
#     except:
#         st.session_state.active_keywords = []

# load_keywords()

# # Logger class
# class StreamlitLogger:
#     def __init__(self):
#         self.log_buffer = []

#     def write(self, message):
#         self.log_buffer.append(message)

#     def flush(self):
#         pass
    
#     def get_logs(self):
#         return "".join(self.log_buffer)

# # Helper function for threading
# def process_single_article(news_item, keyword_id, keyword):
#     """
#     Returns tuple: (article_data, status) where status is:
#     - 'new': New article saved
#     - 'duplicate': Article already exists
#     - 'filtered': Title doesn't contain keyword
#     - 'failed': Extraction failed
#     """
#     try:
#         # Get the article title from news_item first to filter early
#         news_title = news_item.get('title', '')
        
#         # Check if keyword appears in title (case-insensitive)
#         # Split keyword to handle multi-word keywords like "PT ASABRI"
#         keyword_lower = keyword.lower()
#         title_lower = news_title.lower()
        
#         # Check for main keyword or any significant part
#         keyword_parts = [k.strip() for k in keyword_lower.split() if len(k.strip()) > 2]
#         keyword_found = any(part in title_lower for part in keyword_parts) or keyword_lower in title_lower
        
#         if not keyword_found:
#             return ({"title": news_title}, "filtered")
        
#         full_article = medmon.get_full_article(news_item['url'])
#         if full_article:
#             # Priority for publish_date:
#             # 1. From full article (Newspaper3k)
#             # 2. From Google News 'published date' field
#             # 3. Current time as fallback
#             publish_date = full_article.get('publish_date')
            
#             if not publish_date:
#                 # Try to get from Google News result
#                 gn_date = news_item.get('published date')
#                 if gn_date:
#                     publish_date = gn_date
            
#             full_article['publish_date'] = publish_date
#             full_article['publisher'] = news_item.get('publisher', {}).get('title', 'Unknown')
            
#             # Sentiment Analysis - menggunakan kombinasi title + content
#             title = full_article.get('title', '')
#             content = full_article.get('text', '')
            
#             # Kombinasikan title dan content untuk analisis yang lebih akurat
#             combined_text = f"{title}. {content}" if content else title
            
#             score, label = medmon.analyze_sentiment(combined_text)
#             full_article['sentiment_score'] = score
#             full_article['sentiment_label'] = label
            
#             # Save to database - returns article_id, 'duplicate', or None
#             save_result = db.save_article(full_article, keyword_id)
            
#             if save_result == "duplicate":
#                 return (full_article, "duplicate")
#             elif save_result:
#                 return (full_article, "new")
#             else:
#                 return (full_article, "failed")
#     except Exception as e:
#         print(f"[!] Error: {e}")
#     return (None, "failed")

# # Sidebar Configuration
# with st.sidebar:
#     st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=60)
#     st.title("MedMon v3.0")
#     st.markdown("---")
    
#     # Multi-Keyword Management
#     st.subheader("📌 Keyword Management")
    
#     # Display existing keywords
#     if st.session_state.active_keywords:
#         st.markdown("**Active Keywords:**")
#         keywords_html = "".join([f'<span class="keyword-tag">{k}</span>' for k in st.session_state.active_keywords])
#         st.markdown(keywords_html, unsafe_allow_html=True)
#     else:
#         st.info("Belum ada keyword. Tambahkan di bawah.")
    
#     # Add new keyword
#     new_keyword = st.text_input("Tambah Keyword Baru", placeholder="e.g. PT ASABRI", key="new_keyword_input")
#     if st.button("➕ Tambah Keyword"):
#         if new_keyword and new_keyword.strip():
#             keyword_clean = new_keyword.strip()
#             # Check if already exists
#             existing = [k.lower() for k in st.session_state.active_keywords]
#             if keyword_clean.lower() in existing:
#                 st.warning(f"Keyword '{keyword_clean}' sudah ada!")
#             else:
#                 try:
#                     db.add_keyword(keyword_clean)
#                     st.session_state.active_keywords.append(keyword_clean)
#                     st.success(f"✅ Keyword '{keyword_clean}' berhasil ditambahkan!")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Gagal menambahkan keyword: {e}")
#         else:
#             st.warning("Masukkan keyword terlebih dahulu!")
    
#     st.markdown("---")
    
#     # Scraping Config
#     st.subheader("⚙️ Scraping Config")
    
#     col_lang, col_country = st.columns(2)
#     with col_lang:
#         language = st.selectbox("Bahasa", options=['id', 'en'], index=0)
#     with col_country:
#         country = st.selectbox("Negara", options=['ID', 'US'], index=0)
        
#     period = st.select_slider("Periode", options=['1h', '1d', '7d', '14d', '1m', '1y'], value='14d')
#     max_results = st.number_input("Maks Berita/Keyword", min_value=1, max_value=100, value=10)
#     workers = st.slider("Thread Speed", min_value=1, max_value=10, value=5)
    
#     st.markdown("---")
    
#     # Select keywords to scrape
#     keywords_to_scrape = st.multiselect(
#         "Pilih Keyword untuk Scrape",
#         options=st.session_state.active_keywords,
#         default=st.session_state.active_keywords
#     )
    
#     start_btn = st.button("🚀 Mulai Scraping", disabled=st.session_state.is_scraping or len(keywords_to_scrape) == 0)

# # Main Content
# st.title("MedMon Analyzer AI")
# st.markdown("Intelligence Media Monitoring Dashboard with Multi-Keyword Tracking")

# # Tabs Setup based on Role
# tabs_list = ["📊 Dashboard", "📈 Trend Analysis", "📝 List Berita", "☁️ Word Cloud", "🖥️ Logs"]
# if st.session_state.role in ['Admin', 'Super User']:
#     tabs_list.append("⚙️ Pengaturan")

# tabs = st.tabs(tabs_list)
# tab1, tab2, tab3, tab4, tab5 = tabs[:5]
# if len(tabs) > 5:
#     tab_settings = tabs[5]

# # Scraping Logic
# if start_btn:
#     st.session_state.is_scraping = True
#     st.session_state.results = []
#     st.session_state.terminal_logs = ""
    
#     with tab5:
#         progress_bar = st.progress(0)
#         status_text = st.empty()
#         terminal_placeholder = st.empty()
    
#     try:
#         capture = StreamlitLogger()
#         original_stdout = sys.stdout
#         sys.stdout = capture
        
#         all_articles = []
#         total_keywords = len(keywords_to_scrape)
        
#         for kw_idx, keyword in enumerate(keywords_to_scrape):
#             print(f"\n[{kw_idx+1}/{total_keywords}] Processing keyword: {keyword}")
#             status_text.markdown(f"### 🔍 Scraping: {keyword}...")
            
#             # Add delay between keywords to avoid rate limiting
#             if kw_idx > 0:
#                 print("   [*] Waiting 3 seconds to avoid rate limiting...")
#                 time.sleep(3)
            
#             # Get or create keyword in DB
#             keyword_id = db.add_keyword(keyword)
            
#             # Search news with retry
#             news_results = []
#             for attempt in range(2):  # Try up to 2 times
#                 news_results = medmon.scrape_google_news(
#                     keyword=keyword,
#                     language=language,
#                     country=country,
#                     period=period,
#                     max_results=max_results
#                 )
#                 if news_results:
#                     break
#                 elif attempt == 0:
#                     print(f"   [!] No results, retrying with simpler keyword...")
#                     time.sleep(2)
            
#             total_news = len(news_results)
#             print(f"   [+] Found {total_news} articles for '{keyword}'")
            
#             if total_news == 0:
#                 print(f"   [!] WARNING: Google News returned 0 results. Try shorter period or simpler keyword.")
            
#             keyword_articles = []
#             pos_count, neg_count, neu_count = 0, 0, 0
#             new_count, dup_count, fail_count, filter_count = 0, 0, 0, 0
            
#             # Process articles
#             with ThreadPoolExecutor(max_workers=workers) as executor:
#                 future_to_url = {executor.submit(process_single_article, news, keyword_id, keyword): news for news in news_results}
                
#                 for i, future in enumerate(as_completed(future_to_url)):
#                     progress = ((kw_idx * max_results) + i + 1) / (total_keywords * max_results)
#                     progress_bar.progress(min(progress, 1.0))
                    
#                     try:
#                         data, status = future.result()
                        
#                         if status == "new" and data:
#                             new_count += 1
#                             data['keyword'] = keyword
#                             keyword_articles.append(data)
#                             all_articles.append(data)
                            
#                             if data['sentiment_label'] == 'Positive':
#                                 pos_count += 1
#                             elif data['sentiment_label'] == 'Negative':
#                                 neg_count += 1
#                             else:
#                                 neu_count += 1
                                
#                             print(f"   [+] NEW: {data['title'][:40]}... ({data['sentiment_label']})")
#                         elif status == "duplicate":
#                             dup_count += 1
#                             print(f"   [=] DUP: {data['title'][:40] if data else 'Unknown'}...")
#                         elif status == "filtered":
#                             filter_count += 1
#                             print(f"   [~] SKIP: Title no keyword: {data['title'][:35] if data else 'Unknown'}...")
#                         else:
#                             fail_count += 1
#                             print(f"   [X] FAIL: Could not extract article")
#                     except Exception as exc:
#                         fail_count += 1
#                         print(f"   [X] Error: {exc}")
                    
#                     st.session_state.terminal_logs = capture.get_logs()
#                     terminal_placeholder.code(st.session_state.terminal_logs, language="bash")
            
#             # Print stats for this keyword
#             print(f"\n   📊 Stats for '{keyword}':")
#             print(f"      • New articles saved: {new_count}")
#             print(f"      • Duplicates skipped: {dup_count}")
#             print(f"      • Filtered (no keyword in title): {filter_count}")
#             print(f"      • Failed extractions: {fail_count}")
            
#             # Save scrape history
#             db.save_scrape_history(keyword_id, total_news, len(keyword_articles), pos_count, neg_count, neu_count)
        
#         st.session_state.results = all_articles
#         st.session_state.is_scraping = False
#         status_text.success(f"🎉 Selesai! Total {len(all_articles)} artikel dari {total_keywords} keyword.")
#         progress_bar.progress(100)
        
#         print(f"\n[+] FINISHED. Total: {len(all_articles)} articles")
#         st.session_state.terminal_logs = capture.get_logs()
#         terminal_placeholder.code(st.session_state.terminal_logs, language="bash")
        
#     except Exception as e:
#         st.error(f"Error: {e}")
#         print(f"[!] FATAL: {e}")
#         st.session_state.terminal_logs = capture.get_logs()
#         st.session_state.is_scraping = False
#     finally:
#         sys.stdout = original_stdout

# # Tab 1: Dashboard
# with tab1:
#     st.subheader("📊 Overview Dashboard")
    
#     # Load data from database
#     try:
#         all_db_articles = db.get_articles(limit=500)
#         if all_db_articles:
#             df = pd.DataFrame(all_db_articles)
            
#             # Metrics
#             m1, m2, m3, m4 = st.columns(4)
#             with m1:
#                 st.metric("Total Artikel Publikasi", len(df))
#             with m2:
#                 pos = len(df[df['sentiment_label'] == 'Positive']) if 'sentiment_label' in df.columns else 0
#                 st.metric("Positif", pos)
#             with m3:
#                 neg = len(df[df['sentiment_label'] == 'Negative']) if 'sentiment_label' in df.columns else 0
#                 st.metric("Negatif", neg)
#             with m4:
#                 unique_kw = df['keyword'].nunique() if 'keyword' in df.columns else 0
#                 st.metric("Keywords", unique_kw)
            
#             # Additional Charts based on BRS
#             col_chart1, col_chart2 = st.columns(2)
            
#             with col_chart1:
#                 st.markdown("### 📊 Perbandingan Keyword")
#                 comparison = db.get_keyword_comparison()
#                 if comparison:
#                     comp_df = pd.DataFrame(comparison)
#                     st.bar_chart(comp_df.set_index('keyword')[['positive', 'negative']])
                    
#             with col_chart2:
#                 st.markdown("### 🥧 Sumber Media (Pie Chart)")
#                 if 'publisher' in df.columns:
#                     publisher_counts = df['publisher'].value_counts()
#                     fig1, ax1 = plt.subplots(figsize=(6,4), facecolor='#0E1117')
#                     ax1.pie(publisher_counts, labels=publisher_counts.index, autopct='%1.1f%%', textprops={'color':"w"})
#                     st.pyplot(fig1)
                    
#             st.markdown("### 📊 Jenis Rilis (Internal vs Eksternal)")
#             if 'is_internal' in df.columns:
#                 internal_counts = df['is_internal'].map({1: 'Internal', 0: 'Eksternal'}).value_counts()
#                 st.bar_chart(internal_counts)
                
#             st.markdown("### 📑 Tabel Rekapitulasi Berita Publikasi")
#             # Show summary table with export option
#             st.dataframe(df[['title', 'publisher', 'sentiment_label', 'publish_date', 'is_internal', 'url']].head(50), use_container_width=True)
            
#         else:
#             st.info("Belum ada data berita yang berstatus 'published'.")
#     except Exception as e:
#         st.warning(f"Gagal load data: {e}")

# # Tab 2: Trend Analysis
# with tab2:
#     st.subheader("📈 Trend Analysis")
    
#     try:
#         # Date range selector
#         col1, col2 = st.columns(2)
#         with col1:
#             days_range = st.selectbox("Rentang Waktu", options=[7, 14, 30, 60, 90], index=1)
#         with col2:
#             trend_keyword = st.selectbox("Filter Keyword", options=["Semua"] + st.session_state.active_keywords)
        
#         # Get trend data
#         kw_id = None
#         if trend_keyword != "Semua":
#             for k in db.get_keywords():
#                 if k['keyword'] == trend_keyword:
#                     kw_id = k['id']
#                     break
        
#         trend_data = db.get_trend_data(keyword_id=kw_id, days=days_range)
        
#         if trend_data:
#             trend_df = pd.DataFrame(trend_data)
#             trend_df['date'] = pd.to_datetime(trend_df['date'])
#             trend_df = trend_df.set_index('date')
            
#             # Line Chart - Total Articles
#             st.markdown("#### 📰 Jumlah Artikel per Hari")
#             st.line_chart(trend_df['total'])
            
#             # Stacked Area Chart - Sentiment
#             st.markdown("#### 🎭 Tren Sentimen")
#             st.area_chart(trend_df[['positive', 'negative', 'neutral']])
#         else:
#             st.info("Belum ada data trend. Lakukan beberapa kali scraping untuk melihat tren.")
#     except Exception as e:
#         st.warning(f"Error: {e}")

# # Tab 3: List Berita
# with tab3:
#     st.subheader("📝 Daftar Berita & Review")
    
#     view_mode = st.radio("Mode Tampilan:", ["Berita Terpublikasi", "Review Tertunda (Pending)"], horizontal=True)
    
#     if view_mode == "Berita Terpublikasi":
#         try:
#             articles = db.get_articles(limit=200)
#             if articles:
#                 df = pd.DataFrame(articles)
                
#                 # Filter by keyword
#                 filter_kw = st.selectbox("Filter by Keyword", options=["Semua"] + st.session_state.active_keywords, key="filter_list")
#                 if filter_kw != "Semua":
#                     df = df[df['keyword'] == filter_kw]
                
#                 # Display
#                 display_cols = ['title', 'keyword', 'publisher', 'publish_date', 'sentiment_label', 'sentiment_score', 'url', 'proof_file_path']
#                 final_df = df[[c for c in display_cols if c in df.columns]]
                
#                 st.dataframe(
#                     final_df,
#                     column_config={
#                         "url": st.column_config.LinkColumn("Link"),
#                         "sentiment_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1)
#                     },
#                     use_container_width=True
#                 )
                
#                 # Export Buttons
#                 csv = df.to_csv(index=False).encode('utf-8')
#                 excel_buffer = io.BytesIO()
#                 with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
#                     df.to_excel(writer, index=False, sheet_name='List Berita')
#                 excel_data = excel_buffer.getvalue()
                
#                 dl_col1, dl_col2 = st.columns(2)
#                 with dl_col1:
#                     st.download_button("⬇️ Download CSV", csv, f"medmon_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
#                 with dl_col2:
#                     st.download_button("⬇️ Download Excel", excel_data, f"medmon_{datetime.now().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
#             else:
#                 st.info("Belum ada data terpublikasi.")
#         except Exception as e:
#             st.warning(f"Error: {e}")
            
#     elif view_mode == "Review Tertunda (Pending)":
#         if st.session_state.role not in ['Admin', 'Super User', 'Staff']:
#             st.error("Anda tidak memiliki akses untuk melakukan review pemberitaan.")
#         else:
#             try:
#                 pending_articles = db.get_pending_articles()
#                 if pending_articles:
#                     st.info(f"Terdapat {len(pending_articles)} berita menunggu review.")
#                     for article in pending_articles:
#                         with st.expander(f"Review: {article['title']} ({article['sentiment_label']})", expanded=False):
#                             st.write(f"**Sumber:** {article['publisher']}")
#                             st.write(f"**Link:** [Buka Berita]({article['url']})")
#                             st.write(f"**Tone Mesin:** {article['sentiment_label']} ({article['sentiment_score']:.2f})")
                            
#                             with st.form(f"review_form_{article['id']}"):
#                                 new_tone = st.selectbox("Update Tone Berita:", ["Positive", "Negative", "Neutral"], index=["Positive", "Negative", "Neutral"].index(article['sentiment_label']))
#                                 is_internal = st.checkbox("Berita Rilis Internal Perusahaan?", value=False)
                                
#                                 st.write("Opsional: Upload File Bukti (PDF/JPG/PNG)")
#                                 proof_file = st.file_uploader("Upload Bukti", type=['pdf', 'jpg', 'png'], key=f"file_{article['id']}")
                                
#                                 submit_review = st.form_submit_button("✅ Approve & Publish")
                                
#                                 if submit_review:
#                                     proof_path = None
#                                     if proof_file:
#                                         # Minimalist saving logic, normally save to static folder
#                                         proof_path = f"uploads/{proof_file.name}"
#                                         with open(proof_path, "wb") as f:
#                                             f.write(proof_file.getbuffer())
                                            
#                                     db.update_article_status(article['id'], status='published', new_tone=new_tone, proof_path=proof_path, is_internal=is_internal)
#                                     st.success("Berita berhasil di-publish!")
#                                     st.rerun()
#                 else:
#                     st.success("Tidak ada berita pending. Semua sudah di-review.")
#             except Exception as e:
#                 import os
#                 if not os.path.exists("uploads"):
#                     os.makedirs("uploads")
#                 st.warning(f"Error: {e}")

# # Tab 4: Word Cloud
# with tab4:
#     st.subheader("☁️ Word Cloud")
    
#     try:
#         articles = db.get_articles(limit=100)
#         if articles:
#             text_combined = " ".join([a.get('content', '') or '' for a in articles])
#             if text_combined.strip():
#                 wc = WordCloud(width=800, height=400, background_color='#0E1117', colormap='Reds').generate(text_combined)
                
#                 fig, ax = plt.subplots(figsize=(10, 5), facecolor='#0E1117')
#                 ax.imshow(wc, interpolation='bilinear')
#                 ax.axis('off')
#                 st.pyplot(fig)
#             else:
#                 st.info("Tidak cukup teks untuk Word Cloud.")
#         else:
#             st.info("Belum ada data.")
#     except Exception as e:
#         st.warning(f"Error: {e}")

# # Tab 5: Logs
# with tab5:
#     st.subheader("🖥️ Terminal Logs")
#     st.code(st.session_state.terminal_logs if st.session_state.terminal_logs else "No logs yet.", language="bash")

# # Settings Tab
# if 'tab_settings' in locals():
#     with tab_settings:
#         st.subheader("⚙️ Pengaturan Sistem")
        
#         set_tab1, set_tab2 = st.tabs(["Kustomisasi Tone", "Manajemen User"])
        
#         with set_tab1:
#             st.markdown("#### Atur Keyword Tone Custom")
#             st.info("Tambahkan kata-kata spesifik yang akan diprioritaskan oleh engine sebagai nilai Positif/Negatif (Pisahkan dengan koma).")
            
#             try:
#                 kw_data = db.get_keywords() # returns id, keyword, tone_p, tone_n
#                 if kw_data:
#                     for kw_item in kw_data:
#                         k_id = kw_item['id']
#                         k_name = kw_item['keyword']
#                         k_pos = kw_item.get('tone_positive', '') or ''
#                         k_neg = kw_item.get('tone_negative', '') or ''
                        
#                         with st.expander(f"Keyword: {k_name}"):
#                             with st.form(f"tone_form_{k_id}"):
#                                 t_pos = st.text_input("Keywords Positif (contoh: anugerah, meningkat, kinerja)", value=k_pos)
#                                 t_neg = st.text_input("Keywords Negatif (contoh: korupsi, krisis, rugi)", value=k_neg)
                                
#                                 if st.form_submit_button("Simpan Aturan"):
#                                     db.update_keyword_tones(k_id, t_pos, t_neg)
#                                     st.success("Aturan tone berhasil disimpan.")
#                 else:
#                     st.warning("Belum ada keyword.")
#             except Exception as e:
#                 st.error(f"Error load keyword data: {e}")
                
#         with set_tab2:
#             st.markdown("#### Role User Management")
#             if st.session_state.role != 'Super User':
#                 st.error("Hanya Super User yang dapat mengakses menu ini.")
#             else:
#                 with st.form("add_user_form"):
#                     st.write("**Tambah Karyawan / User Baru**")
#                     u_name = st.text_input("Username")
#                     u_pass = st.text_input("Password", type="password")
#                     u_role = st.selectbox("Pilih Role Akses", ["Sesper", "Karyawan Staf", "Admin", "Super User"])
                    
#                     if st.form_submit_button("Buat User"):
#                         if u_name and u_pass:
#                             map_role = "Staff" if u_role == "Karyawan Staf" else u_role
#                             res = db.create_user(u_name, u_pass, map_role)
#                             if res:
#                                 st.success(f"User {u_name} berhasil dibuat.")
#                             else:
#                                 st.error("Gagal membuat user. Username mungkin sudah ada.")
                                
#                 st.markdown("---")
#                 try:
#                     users = db.get_all_users()
#                     if users:
#                         st.table(pd.DataFrame(users)[['id', 'username', 'role', 'created_at']])
#                 except:
#                     pass

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import medmon
import db
import sys
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
# Visualization Libraries
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Page Config
st.set_page_config(
    page_title="MedMon v3.0",
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
    st.error(f"Database Error: {e}. Pastikan MySQL/Laragon sudah running.")

# Session State Initialization
if 'results' not in st.session_state:
    st.session_state.results = []
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False
if 'terminal_logs' not in st.session_state:
    st.session_state.terminal_logs = ""
if 'active_keywords' not in st.session_state:
    st.session_state.active_keywords = []

# Auth Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None

def login():
    st.title("Login MedMon v3.0")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            user_data = db.authenticate_user(username, password)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user = user_data['username']
                st.session_state.role = user_data['role']
                st.rerun()
            else:
                st.error("Username atau password salah")
                
def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop()
    
# Layout for logged in users
col_title, col_logout = st.columns([8, 1])
with col_title:
    st.markdown(f"Selamat datang, **{st.session_state.user}** ({st.session_state.role})")
with col_logout:
    if st.button("Logout"):
        logout()

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
    Returns tuple: (article_data, status) where status is:
    - 'new': New article saved
    - 'duplicate': Article already exists
    - 'filtered': Title doesn't contain keyword
    - 'failed': Extraction failed

    Perubahan v4.0:
    - Sentiment TIDAK lagi dianalisis di sini. Artikel disimpan dengan
      sentiment_label='Pending' dan sentiment_score=0.
      Analisis sentimen dilakukan terpisah via tombol "Analisis Sentimen"
      di tab Pengaturan, agar proses scraping jauh lebih cepat.
    - Keyword matching menggunakan medmon.keyword_matches() yang lebih akurat.
    - Artikel dari NewsData.io menggunakan konten yang sudah di-prefetch
      sehingga tidak perlu fetch ulang ke URL artikel.
    """
    try:
        news_title = news_item.get('title', '')
        news_url   = news_item.get('url', '')
        news_desc  = news_item.get('description', '')

        # Filter relevansi menggunakan keyword_matches() yang mendukung
        # exact, AND-logic, dan fuzzy matching — jauh lebih akurat dari
        # logika OR per-kata yang sebelumnya.
        search_text = f"{news_title} {news_url} {news_desc}"
        matched, match_type = medmon.keyword_matches(search_text, keyword)
        if not matched:
            return ({"title": news_title}, "filtered")

        print(f"   [✓] Match ({match_type}): {news_title[:50]}...")

        # Artikel dari NewsData.io sudah punya konten — tidak perlu fetch ulang
        prefetched = news_item.get('_prefetched_content', '')
        if prefetched and len(prefetched) > 150:
            full_article = {
                'title':        news_title,
                'text':         prefetched,
                'url':          news_url,
                'publish_date': news_item.get('published date'),
                'authors':      [],
                'top_image':    None,
            }
        else:
            full_article = medmon.get_full_article(news_url)

        if full_article:
            # Resolve tanggal: prioritas dari artikel > dari sumber RSS/GNews
            publish_date = full_article.get('publish_date')
            if not publish_date:
                publish_date = news_item.get('published date')
            full_article['publish_date'] = publish_date
            full_article['publisher']    = news_item.get('publisher', {}).get('title', 'Unknown')

            # Sentiment TIDAK dianalisis otomatis — disimpan sebagai Pending
            # agar scraping tidak terbebani model IndoBERT.
            full_article['sentiment_score'] = 0.0
            full_article['sentiment_label'] = 'Pending'

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
    st.title("MedMon v3.0")
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
    
    # ── Status Model Sentiment ─────────────────────────────────────────────
    # Widget ini selalu terlihat di sidebar terlepas dari tab yang sedang dibuka.
    # Ini menjawab pertanyaan "apakah model sudah terhubung?" secara langsung
    # tanpa harus masuk ke tab Pengaturan.
    st.subheader("🧠 Model Sentiment")

    try:
        model_info = medmon.get_model_info()
        m_status   = model_info.get("status", "unknown")
        m_loaded   = model_info.get("model_loaded", False)

        if m_status == "ready" and m_loaded:
            # Model sudah di-load ke memori — siap analisis
            st.success("● Model aktif di memori")
            label_map = model_info.get("label_mapping", {})
            if label_map:
                labels_str = " / ".join(label_map.values())
                st.caption(f"Label: **{labels_str}**")

        elif m_status == "ready" and not m_loaded:
            # File model ada dan valid, tapi belum di-load ke memori
            # (normal — lazy load, akan dimuat saat batch analysis pertama dijalankan)
            st.info("● Model tersedia, belum dimuat")
            st.caption("Akan dimuat otomatis saat batch analysis dijalankan.")

            # Tombol untuk pre-load model ke memori sekarang
            # supaya analisis batch pertama tidak terasa lambat karena harus load dulu
            if st.button("⚡ Muat Model Sekarang", use_container_width=True):
                with st.spinner("Memuat model ke memori..."):
                    try:
                        medmon._get_sentiment_pipeline()
                        st.success("✅ Model berhasil dimuat!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal memuat: {e}")

        elif m_status == "model_not_found":
            st.error("● Model tidak ditemukan")
            st.caption("Isi `SENTIMENT_MODEL_PATH` di `medmon.py`")

        else:
            st.warning(f"● Status: {m_status}")

    except Exception as e:
        st.error(f"● Error membaca model: {e}")

    st.markdown("---")
    
    # Select keywords to scrape
    keywords_to_scrape = st.multiselect(
        "Pilih Keyword untuk Scrape",
        options=st.session_state.active_keywords,
        default=st.session_state.active_keywords
    )
    
    start_btn = st.button("🚀 Mulai Scraping", disabled=st.session_state.is_scraping or len(keywords_to_scrape) == 0)

# Main Content
st.title("MedMon Analyzer AI")
st.markdown("Intelligence Media Monitoring Dashboard with Multi-Keyword Tracking")

# Tabs Setup based on Role
tabs_list = ["📊 Dashboard", "📈 Trend Analysis", "📝 List Berita", "☁️ Word Cloud", "🖥️ Logs"]
if st.session_state.role in ['Admin', 'Super User']:
    tabs_list.append("⚙️ Pengaturan")

tabs = st.tabs(tabs_list)
tab1, tab2, tab3, tab4, tab5 = tabs[:5]
if len(tabs) > 5:
    tab_settings = tabs[5]

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
            
            # Add delay between keywords to avoid rate limiting
            if kw_idx > 0:
                print("   [*] Waiting 3 seconds to avoid rate limiting...")
                time.sleep(3)
            
            # Get or create keyword in DB
            keyword_id = db.add_keyword(keyword)
            
            # Gunakan scrape_all_sources() — menggabungkan semua sumber secara paralel
            news_results = []
            for attempt in range(2):
                news_results = medmon.scrape_all_sources(
                    keyword=keyword,
                    language=language,
                    country=country,
                    period=period,
                    max_results=max_results
                )
                if news_results:
                    break
                elif attempt == 0:
                    print(f"   [!] No results, retrying...")
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
                    progress = ((kw_idx * max_results) + i + 1) / (total_keywords * max_results)
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
            
            # Print stats for this keyword
            print(f"\n   📊 Stats for '{keyword}':")
            print(f"      • New articles saved: {new_count}")
            print(f"      • Duplicates skipped: {dup_count}")
            print(f"      • Filtered (no keyword in title): {filter_count}")
            print(f"      • Failed extractions: {fail_count}")
            
            # Save scrape history
            db.save_scrape_history(keyword_id, total_news, len(keyword_articles), pos_count, neg_count, neu_count)
        
        st.session_state.results = all_articles
        st.session_state.is_scraping = False
        status_text.success(f"🎉 Selesai! Total {len(all_articles)} artikel dari {total_keywords} keyword.")
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
    
    # Load data from database
    try:
        all_db_articles = db.get_articles(limit=500)
        if all_db_articles:
            df = pd.DataFrame(all_db_articles)
            
            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Artikel Publikasi", len(df))
            with m2:
                pos = len(df[df['sentiment_label'] == 'Positive']) if 'sentiment_label' in df.columns else 0
                st.metric("Positif", pos)
            with m3:
                neg = len(df[df['sentiment_label'] == 'Negative']) if 'sentiment_label' in df.columns else 0
                st.metric("Negatif", neg)
            with m4:
                unique_kw = df['keyword'].nunique() if 'keyword' in df.columns else 0
                st.metric("Keywords", unique_kw)
            
            # Additional Charts based on BRS
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("### 📊 Perbandingan Keyword")
                comparison = db.get_keyword_comparison()
                if comparison:
                    comp_df = pd.DataFrame(comparison)
                    st.bar_chart(comp_df.set_index('keyword')[['positive', 'negative']])
                    
            with col_chart2:
                st.markdown("### 🥧 Sumber Media (Pie Chart)")
                if 'publisher' in df.columns:
                    publisher_counts = df['publisher'].value_counts()
                    fig1, ax1 = plt.subplots(figsize=(6,4), facecolor='#0E1117')
                    ax1.pie(publisher_counts, labels=publisher_counts.index, autopct='%1.1f%%', textprops={'color':"w"})
                    st.pyplot(fig1)
                    
            st.markdown("### 📊 Jenis Rilis (Internal vs Eksternal)")
            if 'is_internal' in df.columns:
                internal_counts = df['is_internal'].map({1: 'Internal', 0: 'Eksternal'}).value_counts()
                st.bar_chart(internal_counts)
                
            st.markdown("### 📑 Tabel Rekapitulasi Berita Publikasi")
            # Show summary table with export option
            st.dataframe(df[['title', 'publisher', 'sentiment_label', 'publish_date', 'is_internal', 'url']].head(50), use_container_width=True)
            
        else:
            st.info("Belum ada data berita yang berstatus 'published'.")
    except Exception as e:
        st.warning(f"Gagal load data: {e}")

# Tab 2: Trend Analysis
with tab2:
    st.subheader("📈 Trend Analysis")
    
    try:
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            days_range = st.selectbox("Rentang Waktu", options=[7, 14, 30, 60, 90], index=1)
        with col2:
            trend_keyword = st.selectbox("Filter Keyword", options=["Semua"] + st.session_state.active_keywords)
        
        # Get trend data
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
            
            # Line Chart - Total Articles
            st.markdown("#### 📰 Jumlah Artikel per Hari")
            st.line_chart(trend_df['total'])
            
            # Stacked Area Chart - Sentiment
            st.markdown("#### 🎭 Tren Sentimen")
            st.area_chart(trend_df[['positive', 'negative', 'neutral']])
        else:
            st.info("Belum ada data trend. Lakukan beberapa kali scraping untuk melihat tren.")
    except Exception as e:
        st.warning(f"Error: {e}")

# Tab 3: List Berita
with tab3:
    st.subheader("📝 Daftar Berita & Review")
    
    view_mode = st.radio("Mode Tampilan:", ["Berita Terpublikasi", "Review Tertunda (Pending)"], horizontal=True)
    
    if view_mode == "Berita Terpublikasi":
        try:
            articles = db.get_articles(limit=200)
            if articles:
                df = pd.DataFrame(articles)
                
                # Pastikan scraped_at dalam format datetime untuk sorting
                if 'scraped_at' in df.columns:
                    df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')
                if 'publish_date' in df.columns:
                    df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce')

                # Filter dan sorting controls dalam satu baris
                ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 2])
                with ctrl_col1:
                    filter_kw = st.selectbox("Filter Keyword", options=["Semua"] + st.session_state.active_keywords, key="filter_list")
                with ctrl_col2:
                    sort_by = st.selectbox(
                        "Urutkan berdasarkan",
                        options=["Waktu Crawl (Terbaru)", "Tanggal Publikasi (Terbaru)", "Sentimen"],
                        key="sort_list"
                    )
                with ctrl_col3:
                    filter_sentiment = st.selectbox(
                        "Filter Sentimen",
                        options=["Semua", "Positive", "Neutral", "Negative", "Pending"],
                        key="filter_sent"
                    )

                # Terapkan filter keyword
                if filter_kw != "Semua":
                    df = df[df['keyword'] == filter_kw]

                # Terapkan filter sentimen
                if filter_sentiment != "Semua" and 'sentiment_label' in df.columns:
                    df = df[df['sentiment_label'] == filter_sentiment]

                # Terapkan sorting
                if sort_by == "Waktu Crawl (Terbaru)" and 'scraped_at' in df.columns:
                    df = df.sort_values('scraped_at', ascending=False)
                elif sort_by == "Tanggal Publikasi (Terbaru)" and 'publish_date' in df.columns:
                    df = df.sort_values('publish_date', ascending=False, na_position='last')
                elif sort_by == "Sentimen" and 'sentiment_label' in df.columns:
                    sentiment_order = {'Negative': 0, 'Neutral': 1, 'Positive': 2, 'Pending': 3}
                    df['_sort_key'] = df['sentiment_label'].map(sentiment_order).fillna(4)
                    df = df.sort_values('_sort_key').drop(columns=['_sort_key'])

                # Tampilkan kolom scraped_at agar pengguna bisa tahu kapan artikel di-crawl
                # Ini adalah kolom paling penting untuk memantau hasil scraping terbaru
                display_cols = ['scraped_at', 'title', 'keyword', 'publisher', 'publish_date', 'sentiment_label', 'sentiment_score', 'url']
                final_df = df[[c for c in display_cols if c in df.columns]]

                st.caption(f"Menampilkan **{len(final_df)}** artikel · diurutkan: **{sort_by}**")
                st.dataframe(
                    final_df,
                    column_config={
                        "scraped_at":      st.column_config.DatetimeColumn("⏱ Waktu Crawl", format="DD/MM/YY HH:mm"),
                        "publish_date":    st.column_config.DatetimeColumn("📅 Tgl Publikasi", format="DD/MM/YY"),
                        "url":             st.column_config.LinkColumn("🔗 Link"),
                        "sentiment_label": st.column_config.TextColumn("Sentimen"),
                        "sentiment_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1),
                        "title":           st.column_config.TextColumn("Judul", width="large"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
                
                # Export Buttons
                csv = df.to_csv(index=False).encode('utf-8')
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='List Berita')
                excel_data = excel_buffer.getvalue()
                
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button("⬇️ Download CSV", csv, f"medmon_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
                with dl_col2:
                    st.download_button("⬇️ Download Excel", excel_data, f"medmon_{datetime.now().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.info("Belum ada data terpublikasi.")
        except Exception as e:
            st.warning(f"Error: {e}")
            
    elif view_mode == "Review Tertunda (Pending)":
        if st.session_state.role not in ['Admin', 'Super User', 'Staff']:
            st.error("Anda tidak memiliki akses untuk melakukan review pemberitaan.")
        else:
            try:
                pending_articles = db.get_pending_articles()
                if pending_articles:
                    st.info(f"Terdapat {len(pending_articles)} berita menunggu review.")

                    # Kelompokkan artikel
                    pending_no_sentiment = [a for a in pending_articles if a['sentiment_label'] == 'Pending']
                    pending_with_sentiment = [a for a in pending_articles if a['sentiment_label'] != 'Pending']

                    # ═══════════════════════════════════════════════════════════
                    # BARIS AKSI UTAMA
                    # ═══════════════════════════════════════════════════════════
                    act_col1, act_col2, act_col3 = st.columns(3)

                    # ── Tombol 1: Analisis Sentimen AI (batch) ────────────────
                    with act_col1:
                        if pending_no_sentiment:
                            st.caption(f"🤖 **{len(pending_no_sentiment)}** belum dianalisis")
                            if st.button("🤖 Analisis Sentimen Semua", key="batch_sentiment_review", type="primary", use_container_width=True):
                                with st.spinner("Memuat model dan menganalisis..."):
                                    try:
                                        updated = 0
                                        progress = st.progress(0, text="Memproses...")
                                        for idx, art in enumerate(pending_no_sentiment):
                                            title = art.get('title', '')
                                            content = art.get('content', '')
                                            text = f"{title}. {content}" if content else title
                                            score, label = medmon.analyze_sentiment(text)
                                            db.update_article_sentiment(art['id'], score, label)
                                            updated += 1
                                            progress.progress(int((updated / len(pending_no_sentiment)) * 100), text=f"{updated}/{len(pending_no_sentiment)}")
                                        st.success(f"✅ {updated} artikel berhasil dianalisis!")
                                        st.rerun()
                                    except Exception as batch_err:
                                        st.error(f"Gagal analisis batch: {batch_err}")
                        else:
                            st.caption("✅ Semua sudah dianalisis AI")

                    # ── Tombol 2: Approve Semua yang sudah ada sentimen ───────
                    with act_col2:
                        if pending_with_sentiment:
                            st.caption(f"📋 **{len(pending_with_sentiment)}** siap di-approve")
                            if st.button("✅ Approve Semua", key="bulk_approve_all", type="primary", use_container_width=True):
                                with st.spinner("Meng-approve semua berita..."):
                                    approved = 0
                                    for art in pending_with_sentiment:
                                        db.update_article_status(
                                            art['id'],
                                            status='published',
                                            new_tone=art['sentiment_label'],
                                            is_internal=False
                                        )
                                        approved += 1
                                    st.success(f"✅ {approved} berita berhasil di-approve & publish!")
                                    st.rerun()
                        else:
                            st.caption("⏳ Belum ada yang siap di-approve")

                    # ── Tombol 3: Re-Analisis ulang semua ─────────────────────
                    with act_col3:
                        if pending_with_sentiment:
                            st.caption("🔄 Analisis ulang semua")
                            if st.button("🔄 Re-Analisis Sentimen", key="re_analyze_all", use_container_width=True):
                                with st.spinner("Menganalisis ulang semua..."):
                                    try:
                                        updated = 0
                                        progress = st.progress(0, text="Memproses...")
                                        total = len(pending_articles)
                                        for idx, art in enumerate(pending_articles):
                                            title = art.get('title', '')
                                            content = art.get('content', '')
                                            text = f"{title}. {content}" if content else title
                                            score, label = medmon.analyze_sentiment(text)
                                            db.update_article_sentiment(art['id'], score, label)
                                            updated += 1
                                            progress.progress(int((updated / total) * 100), text=f"{updated}/{total}")
                                        st.success(f"✅ {updated} artikel berhasil di-analisis ulang!")
                                        st.rerun()
                                    except Exception as re_err:
                                        st.error(f"Gagal re-analisis: {re_err}")

                    st.markdown("---")

                    # ═══════════════════════════════════════════════════════════
                    # KOREKSI SENTIMEN MASSAL (editable)
                    # ═══════════════════════════════════════════════════════════
                    if pending_with_sentiment:
                        st.markdown("#### ✏️ Koreksi Sentimen & Approve Massal")
                        st.caption("Ubah sentimen yang dihasilkan model jika perlu, lalu klik **Simpan Koreksi** atau langsung **Approve Semua**.")

                        with st.form("bulk_correction_form"):
                            corrected_tones = {}
                            corrected_internal = {}

                            for art in pending_with_sentiment:
                                c1, c2, c3, c4 = st.columns([5, 2, 1, 1])
                                with c1:
                                    st.markdown(f"**{art['title'][:80]}{'...' if len(art['title']) > 80 else ''}**")
                                    st.caption(f"Sumber: {art['publisher']} · [Buka Link]({art['url']})")
                                with c2:
                                    tone_options = ["Positive", "Negative", "Neutral"]
                                    current_label = art['sentiment_label']
                                    tone_idx = tone_options.index(current_label) if current_label in tone_options else 2
                                    corrected_tones[art['id']] = st.selectbox(
                                        "Tone",
                                        tone_options,
                                        index=tone_idx,
                                        key=f"corr_tone_{art['id']}",
                                        label_visibility="collapsed"
                                    )
                                with c3:
                                    score_val = float(art['sentiment_score']) if art['sentiment_score'] else 0.0
                                    st.metric("Score", f"{score_val:.2f}", label_visibility="collapsed")
                                with c4:
                                    corrected_internal[art['id']] = st.checkbox("Int.", key=f"corr_int_{art['id']}", value=False)

                            st.markdown("---")
                            form_col1, form_col2 = st.columns(2)
                            with form_col1:
                                save_corrections = st.form_submit_button("💾 Simpan Koreksi Saja", use_container_width=True)
                            with form_col2:
                                approve_corrected = st.form_submit_button("✅ Simpan & Approve Semua", use_container_width=True, type="primary")

                            if save_corrections:
                                for art_id, tone in corrected_tones.items():
                                    db.update_article_sentiment(art_id, None, tone)
                                st.success(f"✅ Koreksi sentimen untuk {len(corrected_tones)} artikel berhasil disimpan!")
                                st.rerun()

                            if approve_corrected:
                                for art in pending_with_sentiment:
                                    art_id = art['id']
                                    new_tone = corrected_tones.get(art_id, art['sentiment_label'])
                                    is_int = corrected_internal.get(art_id, False)
                                    db.update_article_status(art_id, status='published', new_tone=new_tone, is_internal=is_int)
                                st.success(f"✅ {len(pending_with_sentiment)} berita berhasil dikoreksi & di-publish!")
                                st.rerun()

                    st.markdown("---")

                    # ═══════════════════════════════════════════════════════════
                    # DETAIL PER-ARTIKEL (expander)
                    # ═══════════════════════════════════════════════════════════
                    st.markdown("#### 📰 Detail Per-Artikel")
                    for article in pending_articles:
                        with st.expander(f"Review: {article['title']} ({article['sentiment_label']})", expanded=False):
                            st.write(f"**Sumber:** {article['publisher']}")
                            st.write(f"**Link:** [Buka Berita]({article['url']})")

                            if article['sentiment_label'] != 'Pending':
                                st.write(f"**Tone Mesin:** {article['sentiment_label']} ({article['sentiment_score']:.2f})")
                            else:
                                st.write("**Tone Mesin:** ⏳ Belum dianalisis")

                            # Tombol AI per-artikel
                            if article['sentiment_label'] == 'Pending':
                                if st.button("🤖 Analisis Sentimen AI", key=f"ai_sent_{article['id']}"):
                                    with st.spinner("Menganalisis sentimen..."):
                                        try:
                                            title = article.get('title', '')
                                            content = article.get('content', '')
                                            text = f"{title}. {content}" if content else title
                                            score, label = medmon.analyze_sentiment(text)
                                            db.update_article_sentiment(article['id'], score, label)
                                            st.success(f"✅ Hasil: **{label}** (skor: {score:.2f})")
                                            st.rerun()
                                        except Exception as ai_err:
                                            st.error(f"Gagal analisis: {ai_err}")

                            with st.form(f"review_form_{article['id']}"):
                                tone_options = ["Positive", "Negative", "Neutral"]
                                current_label = article['sentiment_label']
                                tone_idx = tone_options.index(current_label) if current_label in tone_options else 2
                                new_tone = st.selectbox("Update Tone Berita:", tone_options, index=tone_idx,
                                                        help="Pilih tone secara manual, atau gunakan hasil AI di atas sebagai acuan.")
                                is_internal = st.checkbox("Berita Rilis Internal Perusahaan?", value=False)
                                
                                st.write("Opsional: Upload File Bukti (PDF/JPG/PNG)")
                                proof_file = st.file_uploader("Upload Bukti", type=['pdf', 'jpg', 'png'], key=f"file_{article['id']}")
                                
                                submit_review = st.form_submit_button("✅ Approve & Publish")
                                
                                if submit_review:
                                    proof_path = None
                                    if proof_file:
                                        import os as _os
                                        if not _os.path.exists("uploads"):
                                            _os.makedirs("uploads")
                                        proof_path = f"uploads/{proof_file.name}"
                                        with open(proof_path, "wb") as f:
                                            f.write(proof_file.getbuffer())
                                            
                                    db.update_article_status(article['id'], status='published', new_tone=new_tone, proof_path=proof_path, is_internal=is_internal)
                                    st.success("Berita berhasil di-publish!")
                                    st.rerun()
                else:
                    st.success("Tidak ada berita pending. Semua sudah di-review.")
            except Exception as e:
                import os
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                st.warning(f"Error: {e}")

# Tab 4: Word Cloud
with tab4:
    st.subheader("☁️ Word Cloud")
    
    try:
        articles = db.get_articles(limit=100)
        if articles:
            text_combined = " ".join([a.get('content', '') or '' for a in articles])
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

# Settings Tab
if 'tab_settings' in locals():
    with tab_settings:
        st.subheader("⚙️ Pengaturan Sistem")
        
        set_tab1, set_tab2 = st.tabs(["Kustomisasi Tone", "Manajemen User"])
        
        with set_tab1:
            # ── Informasi Model Sentiment ─────────────────────────────────────
            st.markdown("#### 🧠 Model Sentiment")

            # Tampilkan info model lokal yang sedang terkonfigurasi
            try:
                model_info = medmon.get_model_info()
                status = model_info.get("status", "unknown")

                if status == "ready":
                    # Model ditemukan dan config valid — tampilkan detail
                    st.success(f"✅ Model lokal ditemukan dan siap digunakan")
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    
                    # Tampilkan label mapping — ini krusial untuk verifikasi
                    # bahwa model output-nya sesuai ekspektasi (Positive/Neutral/Negative)
                    label_map = model_info.get("label_mapping", {})
                    col_m1.metric("Jumlah Label", model_info.get("num_labels", "?"))
                    col_m2.metric("Device", model_info.get("device", "CPU"))
                    col_m3.metric(
                        "Status Load",
                        "Sudah dimuat" if model_info.get("model_loaded") else "Belum dimuat"
                    )

                    if label_map:
                        st.caption(f"**Label mapping:** {' · '.join([f'{k}→{v}' for k, v in label_map.items()])}")

                    # Tampilkan metadata training jika tersedia di training_metadata.json
                    train_meta = model_info.get("training_metadata", {})
                    if train_meta:
                        with st.expander("📊 Detail Training Model", expanded=False):
                            meta_cols = st.columns(3)
                            if "f1_macro" in train_meta:
                                meta_cols[0].metric("F1 Macro", f"{train_meta['f1_macro']:.4f}")
                            if "accuracy" in train_meta:
                                meta_cols[1].metric("Accuracy", f"{train_meta['accuracy']:.4f}")
                            if "training_date" in train_meta:
                                meta_cols[2].metric("Tanggal Training", train_meta["training_date"])
                            st.json(train_meta)

                elif status == "model_not_found":
                    st.error(
                        f"❌ Folder model tidak ditemukan di path yang dikonfigurasi.\n\n"
                        f"Buka `medmon.py` dan isi `SENTIMENT_MODEL_PATH` dengan path "
                        f"absolut ke folder `asabri_sentiment_model`."
                    )
                    st.code(
                        r'SENTIMENT_MODEL_PATH = r"C:\Users\Bima\Documents\KODINGAN\asabri_webapp\asabri_sentiment_model"',
                        language="python"
                    )
                elif status == "config_error":
                    st.warning("⚠️ config.json bermasalah. Akan diperbaiki otomatis saat analisis dijalankan.")
                else:
                    st.info("ℹ️ Model belum dimuat. Akan dimuat otomatis saat analisis pertama dijalankan.")

            except Exception as e:
                st.warning(f"Tidak bisa membaca info model: {e}")

            st.markdown("---")

            # ── Batch Sentiment Analysis ──────────────────────────────────────
            st.markdown("#### 🤖 Analisis Sentimen Batch")
            st.info(
                "Sentimen tidak dianalisis otomatis saat scraping supaya proses crawl tetap cepat. "
                "Jalankan analisis batch di bawah setelah scraping selesai — model akan memproses "
                "semua artikel yang masih berstatus **Pending** sekaligus."
            )

            try:
                pending_articles_all = db.get_articles_pending_sentiment(limit=500)
                pending_count = len(pending_articles_all)
            except Exception:
                pending_count        = 0
                pending_articles_all = []

            col_s1, col_s2 = st.columns([1, 2])
            col_s1.metric("Artikel Pending Sentimen", pending_count)
            batch_size = col_s2.slider(
                "Jumlah artikel per batch",
                min_value=5, max_value=200, value=20,
                help="Mulai dari angka kecil (20-30) untuk memastikan model berjalan dengan baik."
            )

            if st.button(
                "▶️ Jalankan Analisis Sentimen",
                disabled=(pending_count == 0),
                type="primary"
            ):
                # Container log — menampilkan setiap langkah secara real-time
                # di UI Streamlit (bukan hanya di terminal server)
                log_container = st.container(border=True)

                def ui_log(msg: str, level: str = "info"):
                    """Tulis pesan ke log container di UI, bukan hanya terminal."""
                    icons = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "error": "❌", "step": "⏳"}
                    icon  = icons.get(level, "•")
                    with log_container:
                        st.caption(f"{icon} {msg}")

                progress_bar = st.progress(0, text="Mempersiapkan...")
                result_slot  = st.empty()

                try:
                    pending_articles = pending_articles_all[:batch_size]
                    total = len(pending_articles)

                    if total == 0:
                        st.success("✅ Tidak ada artikel yang perlu dianalisis.")
                    else:
                        # Step 1: Muat model (ini yang paling lambat di pertama kali)
                        # Dengan menampilkan log ini di UI, pengguna tahu model sedang dimuat
                        # dan tidak mengira aplikasi hang
                        m_info = medmon.get_model_info()
                        if not m_info.get("model_loaded"):
                            ui_log("Model belum dimuat ke memori — memuat sekarang (mungkin 10–30 detik)...", "step")
                        else:
                            ui_log("Model sudah ada di memori, langsung mulai analisis.", "ok")

                        progress_bar.progress(0, text="Memuat model sentiment...")

                        # Pre-load model — panggil sekali di sini agar ada feedback jelas
                        # Jika sudah dimuat sebelumnya, fungsi ini langsung return tanpa delay
                        try:
                            medmon._get_sentiment_pipeline()
                            ui_log(f"Model berhasil dimuat dari: {m_info.get('model_path', 'path tidak diketahui')}", "ok")
                        except FileNotFoundError:
                            ui_log("Folder model tidak ditemukan — periksa SENTIMENT_MODEL_PATH di medmon.py", "error")
                            st.stop()
                        except Exception as load_err:
                            ui_log(f"Gagal memuat model: {load_err}", "error")
                            st.stop()

                        # Step 2: Analisis artikel satu per satu dengan progress bar
                        ui_log(f"Mulai menganalisis {total} artikel...", "step")
                        updated = 0
                        results_summary = {"Positive": 0, "Neutral": 0, "Negative": 0}

                        for article in pending_articles:
                            title   = article.get('title', '')
                            content = article.get('content', '')
                            text    = f"{title}. {content}" if content else title

                            score, label = medmon.analyze_sentiment(text)
                            db.update_article_sentiment(article['id'], score, label)
                            updated += 1
                            results_summary[label] = results_summary.get(label, 0) + 1

                            pct = int((updated / total) * 100)
                            progress_bar.progress(pct, text=f"Menganalisis artikel {updated}/{total}...")

                            # Tampilkan log setiap artikel di UI agar pengguna bisa
                            # melihat model benar-benar bekerja (bukan hanya di terminal)
                            ui_log(f"[{updated}/{total}] **{label}** ({score:.2f}) — {title[:55]}...", "ok")

                        # Step 3: Ringkasan hasil
                        progress_bar.progress(100, text="Selesai!")
                        ui_log(
                            f"Selesai! Positive: {results_summary['Positive']} · "
                            f"Neutral: {results_summary['Neutral']} · "
                            f"Negative: {results_summary['Negative']}", "ok"
                        )
                        result_slot.success(f"✅ {updated} artikel berhasil dianalisis.")
                        st.rerun()

                except Exception as e:
                    ui_log(f"Error tidak terduga: {e}", "error")
                    st.error(f"❌ {e}")

            st.markdown("---")
            st.markdown("#### 🎛️ Atur Keyword Tone Custom")
            st.info("Tambahkan kata-kata spesifik yang akan diprioritaskan oleh engine sebagai nilai Positif/Negatif (Pisahkan dengan koma).")
            
            try:
                kw_data = db.get_keywords() # returns id, keyword, tone_p, tone_n
                if kw_data:
                    for kw_item in kw_data:
                        k_id = kw_item['id']
                        k_name = kw_item['keyword']
                        k_pos = kw_item.get('tone_positive', '') or ''
                        k_neg = kw_item.get('tone_negative', '') or ''
                        
                        with st.expander(f"Keyword: {k_name}"):
                            with st.form(f"tone_form_{k_id}"):
                                t_pos = st.text_input("Keywords Positif (contoh: anugerah, meningkat, kinerja)", value=k_pos)
                                t_neg = st.text_input("Keywords Negatif (contoh: korupsi, krisis, rugi)", value=k_neg)
                                
                                if st.form_submit_button("Simpan Aturan"):
                                    db.update_keyword_tones(k_id, t_pos, t_neg)
                                    st.success("Aturan tone berhasil disimpan.")
                else:
                    st.warning("Belum ada keyword.")
            except Exception as e:
                st.error(f"Error load keyword data: {e}")
                
        with set_tab2:
            st.markdown("#### Role User Management")
            if st.session_state.role != 'Super User':
                st.error("Hanya Super User yang dapat mengakses menu ini.")
            else:
                with st.form("add_user_form"):
                    st.write("**Tambah Karyawan / User Baru**")
                    u_name = st.text_input("Username")
                    u_pass = st.text_input("Password", type="password")
                    u_role = st.selectbox("Pilih Role Akses", ["Sesper", "Karyawan Staf", "Admin", "Super User"])
                    
                    if st.form_submit_button("Buat User"):
                        if u_name and u_pass:
                            map_role = "Staff" if u_role == "Karyawan Staf" else u_role
                            res = db.create_user(u_name, u_pass, map_role)
                            if res:
                                st.success(f"User {u_name} berhasil dibuat.")
                            else:
                                st.error("Gagal membuat user. Username mungkin sudah ada.")
                                
                st.markdown("---")
                try:
                    users = db.get_all_users()
                    if users:
                        st.table(pd.DataFrame(users)[['id', 'username', 'role', 'created_at']])
                except:
                    pass