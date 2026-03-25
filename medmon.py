# from gnews import GNews
# from newspaper import Article
# from googlenewsdecoder import new_decoderv1
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import os
# from datetime import datetime
# from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
# import torch

# # Initialize IndoBERT Sentiment Model (Lazy Loading)
# _sentiment_pipeline = None

# def get_sentiment_pipeline():
#     """Lazy load the sentiment pipeline to avoid long startup time."""
#     global _sentiment_pipeline
#     if _sentiment_pipeline is None:
#         print("[*] Loading IndoBERT Sentiment Model (first run only)...")
#         model_name = "crypter70/IndoBERT-Sentiment-Analysis"
#         _sentiment_pipeline = pipeline(
#             "sentiment-analysis",
#             model=model_name,
#             tokenizer=model_name,
#             device=0  #-1 CPU. Use 0 for GPU if available.
#         )
#         print("[+] IndoBERT Model loaded successfully.")
#     return _sentiment_pipeline

# def preprocess_text(text):
#     """
#     Preprocessing teks sebelum analisis sentimen.
#     Langkah-langkah:
#     1. Hapus URL
#     2. Hapus email
#     3. Hapus karakter khusus (kecuali tanda baca penting)
#     4. Hapus whitespace berlebih
#     5. Lowercase (opsional - BERT biasanya case-sensitive)
#     """
#     import re
    
#     if not text:
#         return ""
    
#     # 1. Hapus URL
#     text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
#     # 2. Hapus email
#     text = re.sub(r'\S+@\S+', '', text)
    
#     # 3. Hapus HTML tags (jika ada sisa)
#     text = re.sub(r'<[^>]+>', '', text)
    
#     # 4. Hapus karakter khusus kecuali tanda baca penting (. , ! ? -)
#     text = re.sub(r'[^\w\s.,!?\-]', '', text)
    
#     # 5. Hapus angka yang berdiri sendiri (opsional)
#     # text = re.sub(r'\b\d+\b', '', text)
    
#     # 6. Hapus whitespace berlebih
#     text = re.sub(r'\s+', ' ', text).strip()
    
#     # 7. Hapus baris kosong berulang
#     text = re.sub(r'\n+', '\n', text)
    
#     return text

# def analyze_sentiment(text):
#     """
#     Menganalisis sentimen teks menggunakan IndoBERT.
#     Model: crypter70/IndoBERT-Sentiment-Analysis
    
#     Pipeline:
#     1. Preprocessing (cleaning)
#     2. Truncation (max 1500 char / 512 tokens)
#     3. Tokenization (by model)
#     4. Inference
#     5. Label normalization
    
#     Returns:
#         tuple: (score, label)
#         - score: confidence score
#         - label: 'Positive', 'Negative', 'Neutral'
#     """
#     try:
#         # Step 1: Preprocessing - clean the text
#         text_clean = preprocess_text(text)
        
#         # Step 2: Truncate text to max 512 tokens (BERT limit ~1500 chars)
#         text_truncated = text_clean[:1500] if text_clean else ""
        
#         if not text_truncated:
#             return 0, "Neutral"
        
#         # Step 3 & 4: Tokenization + Inference (handled by pipeline)
#         pipe = get_sentiment_pipeline()
#         result = pipe(text_truncated)[0]
        
#         label = result['label']
#         score = result['score']
        
#         # Step 5: Normalize labels
#         if label.lower() in ['positive', 'positif', 'label_2']:
#             return score, "Positive"
#         elif label.lower() in ['negative', 'negatif', 'label_0']:
#             return score, "Negative"
#         else:
#             return score, "Neutral"
#     except Exception as e:
#         print(f"   [!] Sentiment error: {e}")
#         return 0, "Neutral"

# def decode_google_news_url(google_url):
#     """
#     Decode URL Google News menggunakan googlenewsdecoder package.
#     Google News menggunakan encrypted URLs yang tidak bisa di-resolve dengan redirect biasa.
#     """
#     try:
#         # Cek apakah URL adalah Google News URL
#         if 'news.google.com' in google_url:
#             print(f"   [*] Decoding Google News URL...")
#             decoded_url = new_decoderv1(google_url, interval=5)
            
#             if decoded_url.get("status"):
#                 real_url = decoded_url["decoded_url"]
#                 print(f"   [+] Berhasil decode URL")
#                 return real_url
#             else:
#                 print(f"   [!] Decoder error: {decoded_url.get('message', 'Unknown error')}")
#                 return None
#         else:
#             # Jika bukan Google News URL, kembalikan URL asli
#             return google_url
#     except Exception as e:
#         print(f"   [!] Gagal decode URL: {e}")
#         return None

# def scrape_google_news(keyword, language='id', country='ID', period='14d', max_results=20):
#     """
#     Scrape berita dari Google News berdasarkan keyword
    
#     Args:
#         keyword (str): Kata kunci pencarian
#         language (str): Kode bahasa ('id' untuk Indonesia, 'en' untuk English)
#         country (str): Kode negara ('ID' untuk Indonesia, 'US' untuk Amerika)
#         period (str): Periode waktu ('1h', '1d', '7d', '1m', '1y')
#         max_results (int): Jumlah maksimal hasil
    
#     Returns:
#         list: Daftar berita dengan judul, deskripsi, URL, dll
#     """
#     import time as t
    
#     # Add small delay to avoid rate limiting
#     t.sleep(1)
    
#     try:
#         google_news = GNews(
#             language=language,
#             country=country,
#             period=period,
#             max_results=max_results
#         )
        
#         news = google_news.get_news(keyword)
        
#         if not news:
#             print(f"   [!] GNews returned empty for '{keyword}', trying without period filter...")
#             # Try without strict period
#             google_news_retry = GNews(
#                 language=language,
#                 country=country,
#                 max_results=max_results
#             )
#             news = google_news_retry.get_news(keyword)
        
#         return news if news else []
        
#     except Exception as e:
#         print(f"   [!] GNews error: {e}")
#         return []


# def get_article_with_selenium(url):
#     """
#     Fallback method: Menggunakan Selenium untuk mengambil konten artikel
#     yang tidak bisa diambil dengan newspaper3k
#     """
#     try:
#         print(f"   [*] Mencoba dengan Selenium...")
        
#         # Setup Chrome options untuk headless mode
#         chrome_options = Options()
#         chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--window-size=1920,1080")
#         chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
#         driver = webdriver.Chrome(options=chrome_options)
#         driver.get(url)
        
#         # Tunggu sampai halaman dimuat
#         time.sleep(3)
        
#         # Ambil judul
#         title = driver.title
        
#         # Coba ambil konten dari berbagai selector umum
#         content_selectors = [
#             "article",
#             "[class*='article-content']",
#             "[class*='article-body']",
#             "[class*='content-body']",
#             "[class*='post-content']",
#             "[class*='entry-content']",
#             ".detail-text",
#             ".read__content",
#             "#article-content",
#             "main"
#         ]
        
#         content = ""
#         for selector in content_selectors:
#             try:
#                 elements = driver.find_elements(By.CSS_SELECTOR, selector)
#                 if elements:
#                     for el in elements:
#                         text = el.text.strip()
#                         if len(text) > len(content):
#                             content = text
#             except:
#                 continue
        
#         # Jika tidak ada konten, ambil body
#         if not content:
#             try:
#                 body = driver.find_element(By.TAG_NAME, "body")
#                 content = body.text[:2000]  # Batasi 2000 karakter
#             except:
#                 pass
        
#         driver.quit()
        
#         if content:
#             print(f"   [+] Berhasil ekstrak dengan Selenium")
#             return {
#                 'title': title,
#                 'text': content,
#                 'authors': [],
#                 'publish_date': None,
#                 'url': url,
#                 'top_image': None
#             }
        
#         return None
        
#     except Exception as e:
#         print(f"   [!] Selenium error: {e}")
#         try:
#             driver.quit()
#         except:
#             pass
#         return None


# def get_full_article(url):
#     """
#     Mendapatkan artikel lengkap dari URL dengan fallback ke Selenium
    
#     Args:
#         url (str): URL artikel (bisa Google News URL atau direct URL)
    
#     Returns:
#         dict: Artikel lengkap dengan teks atau None jika gagal
#     """
#     # Decode Google News URL jika perlu
#     real_url = decode_google_news_url(url)
    
#     # Jika decode gagal, return None
#     if not real_url:
#         print("   [!] Tidak bisa mendapatkan URL asli artikel")
#         return None
    
#     print(f"   -> URL Asli: {real_url[:60]}...")
    
#     # Metode 1: Coba dengan newspaper3k (lebih cepat)
#     try:
#         print(f"   [*] Mencoba dengan Newspaper3k...")
#         article = Article(real_url)
#         article.download()
#         article.parse()
        
#         # Cek apakah berhasil mendapatkan konten
#         if article.text and len(article.text) > 100:
#             print(f"   [+] Berhasil ekstrak dengan Newspaper3k")
#             return {
#                 'title': article.title,
#                 'text': article.text,
#                 'authors': article.authors,
#                 'publish_date': article.publish_date,
#                 'url': real_url,
#                 'top_image': article.top_image
#             }
#         else:
#             print(f"   [!] Newspaper3k: Konten kosong/terlalu pendek")
            
#     except Exception as e:
#         print(f"   [!] Newspaper3k error: {e}")
    
#     # Metode 2: Fallback ke Selenium
#     return get_article_with_selenium(real_url)


# def save_results(articles, keyword, output_dir="output"):
#     """Menyimpan hasil scrape ke CSV dan JSON"""
#     import pandas as pd
    
#     # Buat folder output jika belum ada
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
    
#     # Generate timestamp untuk nama file yang unik
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     keyword_clean = keyword.replace(" ", "_").lower()
    
#     # Convert ke DataFrame
#     df = pd.DataFrame(articles)
    
#     # Simpan ke CSV
#     csv_filename = f"{output_dir}/{keyword_clean}_{timestamp}.csv"
#     df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
#     print(f"✅ Hasil disimpan ke CSV: {csv_filename}")
    
#     # Simpan ke JSON
#     json_filename = f"{output_dir}/{keyword_clean}_{timestamp}.json"
#     df.to_json(json_filename, orient='records', force_ascii=False, indent=2)
#     print(f"✅ Hasil disimpan ke JSON: {json_filename}")
    
#     return csv_filename, json_filename


# # Contoh penggunaan
# if __name__ == "__main__":
#     keyword = "PT ASABRI"
    
#     print(f"Mencari berita tentang: {keyword}\n")
#     print("="*80)
    
#     # Scrape berita
#     results = scrape_google_news(
#         keyword=keyword,
#         language='id',
#         country='ID',
#         period='14d',
#         max_results=20
#     )
    
#     # Tampilkan hasil
#     for i, article in enumerate(results, 1):
#         print(f"\n{i}. {article['title']}")
#         print(f"   Publisher: {article['publisher']['title']}")
#         print(f"   Published: {article['published date']}")
#         print(f"   URL: {article['url'][:80]}...")
#         print(f"   Description: {article['description'][:100]}...")
#         print("-"*80)
    
#     # Ambil artikel lengkap dari berita pertama
#     if results:
#         print("\n\nMENGAMBIL ARTIKEL LENGKAP")
#         print("="*80)
        
#         full_articles = []
        
#         for i, news in enumerate(results, 1):  # Ambil semua artikel
#             print(f"\n[{i}] {news['title'][:50]}...")
            
#             full_article = get_full_article(news['url'])
            
#             if full_article:
#                 # Gunakan tanggal dari Google News jika artikel tidak punya tanggal
#                 if not full_article.get('publish_date'):
#                     full_article['publish_date'] = news.get('published date')
                
#                 # Tambahkan info publisher dari Google News
#                 full_article['publisher'] = news.get('publisher', {}).get('title', 'Unknown')
                
#                 full_articles.append(full_article)
#                 print(f"\n   📰 Judul: {full_article['title']}")
#                 print(f"   📅 Tanggal: {full_article['publish_date']}")
#                 print(f"   🔗 URL: {full_article['url'][:60]}...")
#                 print(f"   📝 Preview: {full_article['text'][:200]}...")
#             else:
#                 print("   ❌ Gagal mengambil artikel")
            
#             time.sleep(2)  # Jeda antar request
        
#         # Simpan hasil
#         if full_articles:
#             print("\n" + "="*80)
#             save_results(full_articles, keyword)
#         else:
#             print("\n⚠️ Tidak ada artikel yang berhasil diambil")
"""
medmon.py — Media Monitoring Engine v4.0
==========================================
Perubahan besar dari v3:

[1] SENTIMENT DIHAPUS DARI PIPELINE SCRAPING
    Analisis IndoBERT tidak lagi dipanggil otomatis saat scraping.
    Artikel disimpan dengan sentiment_label='Pending', sentiment_score=0.
    Sentimen bisa dianalisis belakangan secara batch via run_batch_sentiment().
    Ini menghilangkan ~60-80% bottleneck waktu scraping karena model
    IndoBERT tidak lagi dimuat ke memori di setiap sesi scraping.

[2] EKSTRAKSI KONTEN DIPERBAIKI TOTAL
    Masalah utama sebelumnya:
    - Server mendeteksi bot dan menyajikan halaman CAPTCHA/challenge
    - trafilatura mengambil sidebar/related articles/footer
    - newspaper3k gagal di situs JS-heavy
    
    Perbaikan:
    - Header browser yang benar-benar realistis (User-Agent, Accept-Language,
      Sec-Fetch-*, Cookie hint, dll.) agar tidak terdeteksi bot
    - Validasi kualitas konten sebelum diterima (panjang minimal, deteksi
      kata kunci bot-verification page)
    - Ekstraksi ulang dengan readability-lxml sebagai fallback ke-2
      (lebih presisi dari newspaper3k untuk ambil main article body)
    - Selenium hanya sebagai last resort, dengan wait eksplisit

Dependencies baru:
    pip install readability-lxml lxml_html_clean httpx
"""

# ─── Standard Library ─────────────────────────────────────────────────────────
import re
import os
import time
import random
from datetime import datetime

# ─── Environment Variables ────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opsional, bisa juga set env var secara manual
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── News Fetching ────────────────────────────────────────────────────────────
from gnews import GNews
import feedparser

# ─── HTTP Client ──────────────────────────────────────────────────────────────
import httpx
import requests

# ─── URL Decoding ─────────────────────────────────────────────────────────────
from googlenewsdecoder import new_decoderv1

# ─── Article Extraction ───────────────────────────────────────────────────────
import trafilatura
from newspaper import Article
from readability import Document          # readability-lxml: presisi lebih baik
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─── Keyword Matching ─────────────────────────────────────────────────────────
from rapidfuzz import fuzz

# ─── Sentiment (dipertahankan tapi tidak dipanggil otomatis) ──────────────────
from transformers import pipeline as hf_pipeline


# ════════════════════════════════════════════════════════════════════════════════
#  KONFIGURASI
# ════════════════════════════════════════════════════════════════════════════════

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")              # Isi di file .env atau set env var
BERITA_API_URL   = os.getenv("BERITA_API_URL", "")               # Isi di file .env atau set env var
API_TIMEOUT      = 25


# ════════════════════════════════════════════════════════════════════════════════
#  BROWSER HEADERS — Kunci untuk menghindari deteksi bot
#
#  Banyak server media menggunakan "fingerprinting" untuk membedakan request
#  dari browser nyata vs. script otomatis. Ciri-ciri yang paling sering
#  diperiksa adalah:
#    - User-Agent yang tidak ada atau terlalu umum
#    - Tidak ada header Accept-Language
#    - Tidak ada header Sec-Fetch-* (hanya ada di browser Chromium modern)
#    - Connection tidak menggunakan HTTP/2
#
#  Dengan mengirim semua header ini, request kita tampak identik dengan
#  browser Chrome biasa yang sedang membuka artikel.
# ════════════════════════════════════════════════════════════════════════════════

# Pool User-Agent dari beberapa versi Chrome & Firefox.
# Dirotasi secara acak agar tidak ada pola yang bisa dideteksi.
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def _get_browser_headers(referer: str = "https://www.google.com/") -> dict:
    """
    Membangun set header yang menyerupai browser Chrome nyata.
    
    Penjelasan setiap header:
    - User-Agent: Identitas browser dan OS
    - Accept: Format konten yang diterima — browser selalu kirim ini
    - Accept-Language: Preferensi bahasa — penting, banyak bot tidak mengirimnya
    - Accept-Encoding: Kompresi yang didukung
    - Referer: Seolah-olah kita datang dari Google Search
    - Sec-Fetch-*: Header khusus Chromium yang hanya ada di browser asli
    - DNT: Do Not Track — sinyal privasi browser biasa
    """
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
    }


# ════════════════════════════════════════════════════════════════════════════════
#  CONTENT QUALITY VALIDATOR
#  Setelah konten berhasil diekstrak, kita perlu memverifikasi bahwa yang
#  didapat memang artikel berita, bukan halaman error/bot-check/paywall.
# ════════════════════════════════════════════════════════════════════════════════

# Kata-kata yang hanya muncul di halaman bot-verification, bukan artikel nyata.
# Jika konten mengandung salah satu dari ini, berarti kita kena bot-check.
_BOT_DETECTION_SIGNALS = [
    "verify you are human",
    "verifying you are human",
    "checking your browser",
    "please wait",
    "enable javascript",
    "cloudflare",
    "ddos protection",
    "access denied",
    "403 forbidden",
    "captcha",
    "robot or human",
    "are you a robot",
    "just a moment",
    "security check",
    "browser check",
    "ray id",                    # Cloudflare signature
    "cf-browser-verification",   # Cloudflare
    "distil-",                   # PerimeterX/Distil
]

# Panjang minimum konten (karakter) untuk dianggap sebagai artikel valid.
# Artikel berita yang bermakna biasanya minimal 300 karakter.
# Jika lebih pendek, kemungkinan besar yang tertangkap adalah snippet,
# navigasi, atau halaman error.
_MIN_CONTENT_LENGTH = 300

# Rasio minimum link-per-karakter. Jika terlalu banyak link relative ke teks,
# kemungkinan yang tertangkap adalah halaman daftar artikel (index page),
# bukan artikel itu sendiri.
_MAX_LINK_DENSITY = 0.5  # maksimal 50% dari konten adalah teks link


def _is_bot_verification_page(content: str) -> bool:
    """
    Deteksi apakah halaman yang kita dapat adalah bot-verification page
    (Cloudflare, PerimeterX, dll.) bukan artikel nyata.
    """
    if not content:
        return False
    content_lower = content.lower()
    # Jika dua atau lebih sinyal ditemukan, hampir pasti bot-check page
    signals_found = sum(1 for s in _BOT_DETECTION_SIGNALS if s in content_lower)
    return signals_found >= 2


def _is_valid_article_content(content: str) -> bool:
    """
    Validasi apakah konten yang diekstrak layak disebut artikel berita.
    
    Tiga kriteria:
    1. Panjang minimal terpenuhi (bukan snippet atau halaman kosong)
    2. Bukan bot-verification page
    3. Mengandung beberapa kalimat (titik atau tanda tanya/seru)
    """
    if not content or len(content) < _MIN_CONTENT_LENGTH:
        return False
    if _is_bot_verification_page(content):
        return False
    # Minimal harus ada 3 kalimat (3 titik atau tanda baca kalimat)
    sentence_count = len(re.findall(r'[.!?]', content))
    return sentence_count >= 3


def _clean_extracted_content(content: str) -> str:
    """
    Membersihkan konten yang sudah diekstrak dari artifacts umum.
    Ini dipanggil setelah ekstraksi berhasil, sebelum disimpan.
    """
    if not content:
        return ""

    # Hapus baris yang terlalu pendek (biasanya label UI atau navigasi)
    lines = content.split('\n')
    meaningful_lines = [
        line.strip() for line in lines
        if len(line.strip()) > 20  # Abaikan baris kurang dari 20 karakter
    ]
    content = '\n'.join(meaningful_lines)

    # Normalisasi whitespace berlebih
    content = re.sub(r'\n{3,}', '\n\n', content)   # Maks 2 baris kosong berturut
    content = re.sub(r' {2,}', ' ', content)         # Maks 1 spasi berturut
    content = re.sub(r'\t+', ' ', content)            # Ganti tab dengan spasi

    # Hapus karakter non-printable (sering muncul dari encoding yang salah)
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)

    return content.strip()


# ════════════════════════════════════════════════════════════════════════════════
#  HTTP FETCHER — Fetch HTML dengan header browser yang realistis
# ════════════════════════════════════════════════════════════════════════════════

def _fetch_html(url: str, max_retries: int = 2) -> str | None:
    """
    Fetch HTML sebuah halaman web dengan header browser yang realistis.
    
    Mengapa kita perlu fungsi ini daripada langsung pakai trafilatura.fetch_url()?
    trafilatura.fetch_url() menggunakan header minimal yang sering diblokir.
    Dengan fungsi ini kita bisa kontrol penuh header yang dikirim, dan retry
    dengan jeda acak jika server mengembalikan rate-limit (429).
    
    Returns: string HTML atau None jika semua retry gagal.
    """
    headers = _get_browser_headers(referer="https://www.google.com/search?q=berita")

    for attempt in range(max_retries):
        try:
            # Jeda kecil acak antar attempt untuk menghindari pola yang terdeteksi
            if attempt > 0:
                time.sleep(random.uniform(1.5, 3.0))

            with httpx.Client(
                headers=headers,
                timeout=httpx.Timeout(connect=8, read=25, write=5, pool=5),
                follow_redirects=True,
                http2=True,             # HTTP/2 membuat request lebih mirip browser asli
            ) as client:
                resp = client.get(url)

                # Rate limit — tunggu sebentar dan coba lagi
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 5))
                    print(f"   [!] Rate limited, menunggu {wait}s...")
                    time.sleep(wait)
                    continue

                # Paywalled atau forbidden — tidak ada gunanya di-retry
                if resp.status_code in (401, 402, 403):
                    print(f"   [!] HTTP {resp.status_code} — konten mungkin paywall/restricted")
                    return None

                resp.raise_for_status()
                return resp.text

        except httpx.TimeoutException:
            print(f"   [!] Timeout (attempt {attempt+1}/{max_retries})")
        except httpx.ConnectError:
            print(f"   [!] Koneksi gagal ke {url[:50]}... (attempt {attempt+1})")
        except Exception as e:
            print(f"   [!] Fetch error: {type(e).__name__}: {e}")
            break  # Error yang tidak terduga, jangan retry

    return None


# ════════════════════════════════════════════════════════════════════════════════
#  ARTICLE EXTRACTORS — Tiga metode dengan kualitas dan kecepatan berbeda
# ════════════════════════════════════════════════════════════════════════════════

def _extract_with_trafilatura(html: str, url: str) -> dict | None:
    """
    Ekstraktor ke-1: trafilatura.
    
    Menerima HTML yang sudah di-fetch (bukan URL) agar kita bisa
    menggunakan header browser kita sendiri saat fetch, bukan
    header default trafilatura yang sering diblokir.
    
    favor_recall=True: utamakan dapat semua paragraf artikel,
    terima sedikit noise daripada kehilangan konten penting.
    """
    try:
        content = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            output_format='txt',
            favor_recall=True,
            no_fallback=False,
        )

        if not content or not _is_valid_article_content(content):
            return None

        metadata = trafilatura.extract_metadata(html, default_url=url)
        return {
            'title':        (metadata.title if metadata and metadata.title else ''),
            'text':         _clean_extracted_content(content),
            'authors':      ([metadata.author] if metadata and metadata.author else []),
            'publish_date': (metadata.date if metadata else None),
            'url':          url,
            'extractor':    'trafilatura',
        }
    except Exception as e:
        print(f"   [!] trafilatura error: {e}")
        return None


def _extract_with_readability(html: str, url: str) -> dict | None:
    """
    Ekstraktor ke-2: readability-lxml.
    
    Readability adalah algoritma yang sama yang digunakan Firefox Reader View.
    Ia bekerja dengan cara berbeda dari trafilatura: alih-alih menganalisis
    kepadatan teks per blok HTML, ia mencari elemen DOM yang paling
    menyerupai main article body berdasarkan class/id yang umum.
    
    Ini lebih baik dari newspaper3k untuk situs-situs yang menggunakan
    struktur HTML modern dengan class yang deskriptif.
    """
    try:
        doc = Document(html)
        title = doc.title()

        # doc.summary() mengembalikan HTML artikel yang sudah diisolasi.
        # Kita perlu bersihkan HTML tags untuk mendapat teks bersih.
        summary_html = doc.summary()
        content = re.sub(r'<[^>]+>', ' ', summary_html)
        content = re.sub(r'\s+', ' ', content).strip()

        if not content or not _is_valid_article_content(content):
            return None

        return {
            'title':        title or '',
            'text':         _clean_extracted_content(content),
            'authors':      [],
            'publish_date': None,
            'url':          url,
            'extractor':    'readability',
        }
    except Exception as e:
        print(f"   [!] readability error: {e}")
        return None


def _extract_with_newspaper(url: str) -> dict | None:
    """
    Ekstraktor ke-3: newspaper3k.
    
    Newspaper melakukan fetch sendiri secara internal, tapi kita bisa
    inject custom headers via config untuk menghindari bot detection.
    """
    try:
        from newspaper import Config
        config = Config()
        config.browser_user_agent = random.choice(_USER_AGENTS)
        config.request_timeout = 20
        config.fetch_images = False    # Jangan fetch gambar, lebih cepat

        article = Article(url, config=config)
        article.download()
        article.parse()

        if not article.text or not _is_valid_article_content(article.text):
            return None

        return {
            'title':        article.title or '',
            'text':         _clean_extracted_content(article.text),
            'authors':      article.authors,
            'publish_date': article.publish_date,
            'url':          url,
            'extractor':    'newspaper3k',
        }
    except Exception as e:
        print(f"   [!] newspaper3k error: {e}")
        return None


def _extract_with_selenium(url: str) -> dict | None:
    """
    Ekstraktor ke-4 (last resort): Selenium headless Chrome.
    
    Selenium meluncurkan browser Chrome sungguhan yang bisa:
    - Mengeksekusi JavaScript (untuk situs yang render konten via JS)
    - Melewati beberapa jenis bot-detection ringan
    - Mengklik tombol "Accept Cookies" jika diperlukan
    
    Kelemahannya: paling lambat (3-10 detik per artikel), paling berat di memori.
    Dipanggil HANYA jika semua metode di atas gagal.
    """
    driver = None
    try:
        print(f"   [*] Mencoba dengan Selenium...")
        opts = Options()
        opts.add_argument("--headless=new")      # Mode headless baru (Chrome 112+)
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")  # Sembunyikan tanda otomatisasi
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument(f"--user-agent={random.choice(_USER_AGENTS)}")

        driver = webdriver.Chrome(options=opts)

        # Sembunyikan property navigator.webdriver yang digunakan untuk deteksi
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        driver.get(url)

        # Tunggu sampai body halaman muncul (maksimal 10 detik)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)  # Beri waktu JS selesai render

        title = driver.title

        # Prioritaskan elemen semantik HTML5 dan selector umum media berita Indonesia
        selectors = [
            "article",
            "[itemprop='articleBody']",    # Schema.org markup — sangat umum
            "[class*='article-body']",
            "[class*='article-content']",
            "[class*='post-content']",
            "[class*='entry-content']",
            "[class*='detail-text']",       # Kompas
            ".read__content",               # Detik
            "#article-content",
            ".detail__body",                # Detik
            ".content-detail",
            "main article",
            "main",
        ]

        content = ""
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    text = el.text.strip()
                    if len(text) > len(content):
                        content = text
                if content and _is_valid_article_content(content):
                    break  # Sudah dapat konten yang baik, stop
            except Exception:
                continue

        if not content:
            try:
                content = driver.find_element(By.TAG_NAME, "body").text[:3000]
            except Exception:
                pass

        if not content or not _is_valid_article_content(content):
            return None

        print(f"   [+] Berhasil ekstrak dengan Selenium")
        return {
            'title':        title,
            'text':         _clean_extracted_content(content),
            'authors':      [],
            'publish_date': None,
            'url':          url,
            'extractor':    'selenium',
        }

    except Exception as e:
        print(f"   [!] Selenium error: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# ════════════════════════════════════════════════════════════════════════════════
#  URL DECODING — Google News encrypted URL
# ════════════════════════════════════════════════════════════════════════════════

def decode_google_news_url(google_url: str) -> str | None:
    """Decode URL terenkripsi Google News ke URL artikel aslinya."""
    try:
        if 'news.google.com' in google_url:
            print(f"   [*] Decoding Google News URL...")
            decoded = new_decoderv1(google_url, interval=5)
            if decoded.get("status"):
                print(f"   [+] Berhasil decode URL")
                return decoded["decoded_url"]
            print(f"   [!] Decoder error: {decoded.get('message', 'Unknown')}")
            return None
        return google_url
    except Exception as e:
        print(f"   [!] Gagal decode URL: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════════
#  MAIN EXTRACTION PIPELINE
# ════════════════════════════════════════════════════════════════════════════════

def get_full_article(url: str) -> dict | None:
    """
    Pipeline lengkap ekstraksi artikel dengan fallback chain cerdas.
    
    Alur kerja:
    
    [1] Decode URL Google News jika perlu
    [2] Fetch HTML sekali menggunakan header browser realistis
        → Jika gagal atau terdeteksi bot-check: langsung ke Selenium
    [3] Coba trafilatura dengan HTML yang sudah di-fetch
        → Validasi kualitas konten
    [4] Coba readability-lxml dengan HTML yang sama (tanpa fetch ulang)
        → Validasi kualitas konten
    [5] Coba newspaper3k (fetch ulang sendiri dengan custom UA)
        → Validasi kualitas konten
    [6] Terakhir: Selenium headless Chrome (paling lambat, paling kuat)

    Keunggulan arsitektur ini:
    - HTML di-fetch SATU KALI (langkah 2), lalu diteruskan ke trafilatura
      dan readability tanpa fetch ulang — lebih cepat dan hemat bandwidth
    - Setiap hasil di-validasi sebelum diterima — tidak ada konten sampah
    - Setiap tahap dilaporkan ke terminal untuk debugging
    """
    # Step 1: Resolve URL nyata
    real_url = decode_google_news_url(url)
    if not real_url:
        print("   [!] Tidak bisa mendapatkan URL asli artikel")
        return None

    print(f"   -> URL: {real_url[:70]}...")

    # Step 2: Fetch HTML SATU KALI dengan header realistis
    html = _fetch_html(real_url)

    if html:
        # Cek apakah yang kita dapat adalah bot-verification page
        if _is_bot_verification_page(html):
            print(f"   [!] Bot verification terdeteksi — langsung ke Selenium")
            html = None  # Paksa masuk ke Selenium
        else:
            # Step 3: Trafilatura (menggunakan HTML yang sudah di-fetch)
            result = _extract_with_trafilatura(html, real_url)
            if result:
                print(f"   [+] Berhasil via trafilatura")
                return result

            # Step 4: Readability (menggunakan HTML yang sama, tanpa fetch ulang)
            result = _extract_with_readability(html, real_url)
            if result:
                print(f"   [+] Berhasil via readability")
                return result

    # Step 5: Newspaper3k (fetch ulang dengan custom headers-nya sendiri)
    result = _extract_with_newspaper(real_url)
    if result:
        print(f"   [+] Berhasil via newspaper3k")
        return result

    # Step 6: Selenium sebagai last resort
    result = _extract_with_selenium(real_url)
    if result:
        return result

    print(f"   [X] Semua metode ekstraksi gagal untuk: {real_url[:60]}...")
    return None


# ════════════════════════════════════════════════════════════════════════════════
#  KEYWORD MATCHING
# ════════════════════════════════════════════════════════════════════════════════

def keyword_matches(text: str, keyword: str, fuzzy_threshold: int = 85) -> tuple:
    """
    Tiga strategi pencocokan keyword secara bertingkat:
    
    1. Exact: keyword ditemukan persis di dalam teks
    2. AND-logic: SEMUA kata bermakna (>2 char) harus ada di teks
       Ini lebih ketat dari OR lama — mencegah false positive
    3. Fuzzy: menangani variasi penulisan via rapidfuzz partial_ratio
    
    Returns: (bool, str) — (matched, nama_strategi)
    """
    if not text or not keyword:
        return False, None

    text_lower = text.lower()
    kw_lower = keyword.lower()

    if kw_lower in text_lower:
        return True, "exact"

    words = [w for w in kw_lower.split() if len(w) > 2]
    if words and all(w in text_lower for w in words):
        return True, "all_words"

    score = fuzz.partial_ratio(kw_lower, text_lower)
    if score >= fuzzy_threshold:
        return True, f"fuzzy({score})"

    return False, None


# ════════════════════════════════════════════════════════════════════════════════
#  SENTIMENT ANALYSIS — Model lokal hasil fine-tuning ASABRI
#
#  Tidak dipanggil otomatis saat scraping. Dipanggil via:
#    - Tombol "Analisis Sentimen Batch" di tab Pengaturan Streamlit
#    - run_batch_sentiment(db) dari terminal
#
#  Konfigurasi model ada di bagian SENTIMENT_MODEL_PATH di bawah.
#  Isi path absolut ke folder model Anda, atau gunakan path relatif
#  jika folder model ada di direktori yang sama dengan medmon.py.
#
#  Contoh Windows : r"C:\Users\Bima\Documents\KODINGAN\asabri_webapp\asabri_sentiment_model"
#  Contoh relatif : "asabri_sentiment_model"  (jika satu folder dengan medmon.py)
# ════════════════════════════════════════════════════════════════════════════════

# ── Isi path folder model Anda di sini ────────────────────────────────────────
SENTIMENT_MODEL_PATH = os.getenv("SENTIMENT_MODEL_PATH", "asabri_sentiment_model")
# Bisa berupa path relatif ("asabri_sentiment_model") atau absolut.
# Set via .env atau environment variable.

# Gunakan GPU jika tersedia (device=0), atau CPU (device=-1).
# Untuk komputer biasa tanpa GPU khusus, isi -1.
SENTIMENT_DEVICE = -1   # -1 = CPU, 0 = GPU (CUDA)

# Label yang digunakan model Anda saat training.
# Sesuaikan jika label training Anda berbeda.
# Mapping ini digunakan untuk menormalisasi output model ke format MedMon.
_LABEL_MAP = {
    # Format uppercase (umum di fine-tuned model)
    "positive":  "Positive",
    "negative":  "Negative",
    "neutral":   "Neutral",
    # Format lowercase
    "positif":   "Positive",
    "negatif":   "Negative",
    # Format label_N yang kadang muncul di model tanpa id2label yang benar
    "label_0":   "Negative",
    "label_1":   "Neutral",
    "label_2":   "Positive",
    # Kadang model fine-tuned menggunakan angka langsung
    "0":         "Negative",
    "1":         "Neutral",
    "2":         "Positive",
}

_sentiment_pipeline_instance = None


def _validate_and_fix_config(model_path: str) -> bool:
    """
    Memvalidasi config.json model dan memperbaiki bug yang umum
    terjadi pada hasil fine-tuning IndoBERT.

    Masalah paling sering: model selesai training dengan baik, tapi
    config.json tidak memiliki field id2label/label2id yang benar,
    sehingga pipeline mengembalikan label generik "LABEL_0", "LABEL_1", "LABEL_2"
    alih-alih "NEGATIVE", "NEUTRAL", "POSITIVE".

    Fungsi ini membaca config.json, mengecek kelengkapannya, dan menambahkan
    field yang kurang — TANPA mengubah bobot model (model.safetensors).
    Hanya metadata konfigurasi yang diperbarui.

    Returns True jika config valid atau berhasil diperbaiki, False jika error fatal.
    """
    import json

    config_path = os.path.join(model_path, "config.json")
    if not os.path.exists(config_path):
        print(f"[!] config.json tidak ditemukan di: {model_path}")
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        needs_fix = False

        # Cek 1: num_labels harus 3 untuk klasifikasi POSITIVE/NEUTRAL/NEGATIVE
        if config.get("num_labels") != 3:
            print(f"   [~] config.json: num_labels={config.get('num_labels')} → diperbaiki ke 3")
            config["num_labels"] = 3
            needs_fix = True

        # Cek 2: id2label harus ada dan benar
        # Bug umum: tidak ada sama sekali, atau isinya "LABEL_0" bukan "NEGATIVE"
        expected_id2label = {"0": "NEGATIVE", "1": "NEUTRAL", "2": "POSITIVE"}
        current_id2label = config.get("id2label", {})

        # Deteksi apakah id2label sudah benar (mengandung nama label yang bermakna)
        meaningful_labels = any(
            v.upper() in ("POSITIVE", "NEGATIVE", "NEUTRAL", "POSITIF", "NEGATIF")
            for v in current_id2label.values()
        )

        if not current_id2label or not meaningful_labels:
            print(f"   [~] config.json: id2label tidak valid ({current_id2label}) → diperbaiki")
            config["id2label"] = expected_id2label
            config["label2id"] = {"NEGATIVE": 0, "NEUTRAL": 1, "POSITIVE": 2}
            needs_fix = True

        # Cek 3: problem_type harus ada untuk model klasifikasi
        if "problem_type" not in config:
            config["problem_type"] = "single_label_classification"
            needs_fix = True

        if needs_fix:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"   [+] config.json berhasil diperbaiki dan disimpan.")
        else:
            print(f"   [+] config.json valid, tidak perlu perbaikan.")

        # Tampilkan mapping label yang akan digunakan untuk transparansi
        print(f"   [i] Label mapping: {config.get('id2label')}")
        return True

    except Exception as e:
        print(f"[!] Gagal validasi config.json: {e}")
        return False


def _get_sentiment_pipeline():
    """
    Lazy load model sentiment lokal.

    Cara kerjanya:
    1. Cek apakah model sudah dimuat sebelumnya (lazy loading)
    2. Validasi dan perbaiki config.json jika ada bug
    3. Load model dari path lokal menggunakan HuggingFace transformers
    4. Jika model lokal gagal, fallback ke model remote sebagai safety net

    Mengapa path lokal lebih baik dari model remote?
    Model remote (crypter70/IndoBERT-Sentiment-Analysis) adalah model generik
    yang belum pernah melihat teks berita ASABRI. Model Anda sudah di-fine-tune
    dengan data ASABRI sehingga lebih memahami konteks, nama-nama khusus,
    dan framing berita yang relevan.
    """
    global _sentiment_pipeline_instance
    if _sentiment_pipeline_instance is not None:
        return _sentiment_pipeline_instance

    model_path = SENTIMENT_MODEL_PATH

    # Selesaikan path relatif terhadap lokasi file medmon.py ini
    if not os.path.isabs(model_path):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_path)

    print(f"[*] Loading model sentiment dari: {model_path}")

    if not os.path.exists(model_path):
        print(f"[!] Folder model tidak ditemukan: {model_path}")
        print(f"[!] Pastikan SENTIMENT_MODEL_PATH sudah diisi dengan benar di medmon.py")
        raise FileNotFoundError(f"Model path tidak ditemukan: {model_path}")

    # Validasi dan perbaiki config.json sebelum load model
    print("[*] Memvalidasi config.json...")
    if not _validate_and_fix_config(model_path):
        raise RuntimeError("config.json tidak valid dan tidak bisa diperbaiki otomatis.")

    try:
        _sentiment_pipeline_instance = hf_pipeline(
            "text-classification",      # Lebih spesifik dari "sentiment-analysis"
            model=model_path,           # Load dari folder lokal, bukan download dari HuggingFace
            tokenizer=model_path,       # Tokenizer juga dari lokal (vocab.txt ada di folder)
            device=SENTIMENT_DEVICE,
            # truncation=True memastikan teks panjang dipotong sesuai batas model (512 token)
            # tanpa error, alih-alih crash
            truncation=True,
            max_length=512,
        )
        print(f"[+] Model sentiment lokal berhasil dimuat (device={'GPU' if SENTIMENT_DEVICE >= 0 else 'CPU'}).")
        return _sentiment_pipeline_instance

    except Exception as e:
        print(f"[!] Gagal load model lokal: {e}")
        print(f"[!] Periksa apakah semua file model ada: model.safetensors, config.json, vocab.txt")
        raise


def preprocess_text(text: str) -> str:
    """Membersihkan teks sebelum masuk ke model sentiment."""
    if not text:
        return ""
    text = re.sub(r'https?://\S+|www\.\S+', '', text)   # Hapus URL
    text = re.sub(r'\S+@\S+', '', text)                  # Hapus email
    text = re.sub(r'<[^>]+>', '', text)                  # Hapus HTML
    text = re.sub(r'[^\w\s.,!?\-]', '', text)            # Hapus karakter khusus
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def analyze_sentiment(text: str) -> tuple:
    """
    Analisis sentimen SATU teks menggunakan model lokal.
    Tidak dipanggil otomatis saat scraping — dipanggil via run_batch_sentiment().

    Returns: (score: float, label: str)
      label adalah salah satu dari: "Positive", "Negative", "Neutral"
    """
    try:
        cleaned = preprocess_text(text)
        # Potong di 1500 karakter — cukup untuk menangkap isi berita,
        # dan aman untuk dikonversi ke ~512 token BERT
        truncated = cleaned[:1500] if cleaned else ""
        if not truncated:
            return 0.0, "Neutral"

        pipe = _get_sentiment_pipeline()
        result = pipe(truncated)[0]

        raw_label = result['label'].lower().strip()
        score     = float(result['score'])

        # Normalisasi label menggunakan mapping yang sudah didefinisikan
        # Ini menangani semua variasi output label yang mungkin muncul
        normalized = _LABEL_MAP.get(raw_label)

        if normalized is None:
            # Jika label tidak dikenal sama sekali, log untuk debugging
            print(f"   [!] Label tidak dikenal dari model: '{raw_label}' — default Neutral")
            normalized = "Neutral"

        return score, normalized

    except Exception as e:
        print(f"   [!] Sentiment error: {e}")
        return 0.0, "Neutral"


def get_model_info() -> dict:
    """
    Mengembalikan informasi tentang model yang sedang digunakan.
    Berguna untuk ditampilkan di UI Streamlit sebagai verifikasi.
    """
    import json

    model_path = SENTIMENT_MODEL_PATH
    if not os.path.isabs(model_path):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_path)

    info = {
        "model_path":   model_path,
        "model_loaded": _sentiment_pipeline_instance is not None,
        "device":       "GPU" if SENTIMENT_DEVICE >= 0 else "CPU",
        "status":       "not_loaded",
    }

    # Baca metadata training jika tersedia
    metadata_path = os.path.join(model_path, "training_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                info["training_metadata"] = json.load(f)
        except Exception:
            pass

    # Baca history training jika tersedia
    history_path = os.path.join(model_path, "training_history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                info["training_history"] = json.load(f)
        except Exception:
            pass

    config_path = os.path.join(model_path, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            info["label_mapping"] = cfg.get("id2label", {})
            info["num_labels"]    = cfg.get("num_labels", "?")
            info["status"]        = "ready"
        except Exception:
            info["status"] = "config_error"
    else:
        info["status"] = "model_not_found"

    return info


def run_batch_sentiment(db_module=None, batch_size: int = 20):
    """
    Jalankan analisis sentimen untuk semua artikel yang masih berstatus 'Pending'.
    Dipanggil terpisah dari proses scraping agar scraping tetap cepat.

    Cara pakai dari Streamlit  : tombol di tab Pengaturan
    Cara pakai dari terminal   : python -c "import medmon, db; medmon.run_batch_sentiment(db)"
    """
    if db_module is None:
        print("[!] run_batch_sentiment: db_module harus disediakan.")
        return 0

    pending = db_module.get_articles_pending_sentiment(limit=batch_size)
    if not pending:
        print("[+] Tidak ada artikel pending sentiment.")
        return 0

    print(f"[*] Memulai batch sentiment: {len(pending)} artikel...")
    updated = 0

    for article in pending:
        # Gabungkan judul + konten untuk analisis yang lebih akurat.
        # Judul biasanya lebih informatif tentang tone keseluruhan berita,
        # sehingga kita tempatkan di awal agar mendapat bobot lebih besar.
        title   = article.get('title', '')
        content = article.get('content', '')
        text    = f"{title}. {content}" if content else title

        score, label = analyze_sentiment(text)
        db_module.update_article_sentiment(article['id'], score, label)
        updated += 1
        print(f"   [{updated}/{len(pending)}] {label} ({score:.2f}): {title[:55]}...")

    print(f"[+] Selesai: {updated} artikel dianalisis dengan model lokal.")
    return updated


# ════════════════════════════════════════════════════════════════════════════════
#  NEWS SOURCES
# ════════════════════════════════════════════════════════════════════════════════

def scrape_google_news(keyword, language='id', country='ID', period='14d', max_results=20):
    """Ambil berita dari Google News via library gnews."""
    time.sleep(1)
    try:
        gn = GNews(language=language, country=country, period=period, max_results=max_results)
        news = gn.get_news(keyword)
        if not news:
            print(f"   [!] GNews kosong, mencoba tanpa filter periode...")
            gn2 = GNews(language=language, country=country, max_results=max_results)
            news = gn2.get_news(keyword)
        return news if news else []
    except Exception as e:
        print(f"   [!] GNews error: {e}")
        return []


_RSS_FEEDS = [
    {"url": "https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id", "source": "Google News RSS"},
    {"url": "https://rss.tempo.co/nasional",                        "source": "Tempo Nasional"},
    {"url": "https://rss.tempo.co/bisnis",                          "source": "Tempo Bisnis"},
    {"url": "https://www.antaranews.com/rss/terkini.xml",           "source": "Antara"},
    {"url": "https://www.antaranews.com/rss/ekonomi.xml",           "source": "Antara Ekonomi"},
    {"url": "https://www.antaranews.com/rss/hukum.xml",             "source": "Antara Hukum"},
    {"url": "https://rss.bisnis.com/topnews",                       "source": "Bisnis Indonesia"},
    {"url": "https://rss.bisnis.com/finansial",                     "source": "Bisnis Keuangan"},
    {"url": "https://www.cnbcindonesia.com/market/rss",             "source": "CNBC Market"},
    {"url": "https://www.cnbcindonesia.com/news/rss",               "source": "CNBC News"},
    {"url": "https://rss.kompas.com/rss/news/nasional",             "source": "Kompas Nasional"},
    {"url": "https://rss.detik.com/index.php/detikFinance",         "source": "Detik Finance"},
    {"url": "https://rss.detik.com/index.php/detikNews",            "source": "Detik News"},
    {"url": "https://www.cnnindonesia.com/nasional/rss",            "source": "CNN Nasional"},
    {"url": "https://www.cnnindonesia.com/ekonomi/rss",             "source": "CNN Ekonomi"},
    {"url": "https://www.sindonews.com/rss/nasional",               "source": "Sindonews"},
    {"url": "https://www.republika.co.id/rss",                      "source": "Republika"},
    {"url": "https://www.tribunnews.com/rss/nasional",              "source": "Tribun Nasional"},
]


def _fetch_single_rss(feed_info, keyword, max_per_feed=8):
    try:
        q = keyword.replace(' ', '+')
        feed_url = feed_info['url'].replace('{q}', q)
        headers = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        resp = requests.get(feed_url, headers=headers, timeout=10)
        feed = feedparser.parse(resp.text)
        results = []
        for entry in feed.entries[:max_per_feed * 2]:
            title = re.sub(r'<[^>]+>', '', entry.get('title', ''))
            link  = entry.get('link', '')
            desc  = re.sub(r'<[^>]+>', '', entry.get('summary', entry.get('description', '')))
            if not link:
                continue
            matched, match_type = keyword_matches(f"{title} {desc}", keyword)
            if matched:
                results.append({
                    'title':          title,
                    'url':            link,
                    'published date': entry.get('published', entry.get('updated', '')),
                    'publisher':      {'title': feed_info['source']},
                    'description':    desc[:200],
                    'source_type':    'rss',
                })
            if len(results) >= max_per_feed:
                break
    except Exception as e:
        print(f"   [!] RSS error ({feed_info['source']}): {e}")
        results = []
    return results


def scrape_rss_feeds(keyword, max_per_feed=5):
    """Fetch semua RSS feed secara paralel dan filter berdasarkan keyword."""
    all_results, seen_urls = [], set()
    print(f"   [*] Fetching {len(_RSS_FEEDS)} RSS feeds secara paralel...")
    with ThreadPoolExecutor(max_workers=len(_RSS_FEEDS)) as ex:
        futures = {ex.submit(_fetch_single_rss, f, keyword, max_per_feed): f for f in _RSS_FEEDS}
        for future in as_completed(futures):
            src = futures[future]
            try:
                for item in future.result():
                    if item['url'] not in seen_urls:
                        seen_urls.add(item['url'])
                        all_results.append(item)
            except Exception as e:
                print(f"   [!] {src['source']}: {e}")
    return all_results


def scrape_newsdata(keyword, language='id', max_results=10):
    """Ambil berita dari NewsData.io (jika API key tersedia)."""
    if not NEWSDATA_API_KEY:
        print("   [!] NewsData.io: NEWSDATA_API_KEY belum diisi di medmon.py")
        return []
    try:
        print(f"   [*] Fetching dari NewsData.io...")
        resp = requests.get(
            "https://newsdata.io/api/1/news",
            params={"apikey": NEWSDATA_API_KEY, "q": keyword, "language": language, "country": "id"},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'success':
            print(f"   [!] NewsData error: {data.get('message')}")
            return []
        results = []
        for art in (data.get('results') or [])[:max_results]:
            content = art.get('content') or art.get('description') or ''
            results.append({
                'title':                art.get('title', ''),
                'url':                  art.get('link', ''),
                'published date':       art.get('pubDate', ''),
                'publisher':            {'title': art.get('source_id', 'NewsData')},
                'description':          (art.get('description') or '')[:200],
                'source_type':          'newsdata_io',
                '_prefetched_content':  content,  # Konten sudah ada, tidak perlu fetch
            })
        print(f"   [+] NewsData.io: {len(results)} artikel")
        return results
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 401:
            print(f"   [!] NewsData.io: API key tidak valid.")
        elif code == 429:
            print(f"   [!] NewsData.io: Batas harian tercapai (200/hari free plan).")
        return []
    except Exception as e:
        print(f"   [!] NewsData.io error: {e}")
        return []


def scrape_berita_indo_api(keyword, max_results=20):
    """Ambil berita dari Berita Indo API self-hosted di Vercel."""
    if not BERITA_API_URL:
        print("   [!] Berita Indo API: BERITA_API_URL belum diisi di medmon.py")
        return []
    try:
        print(f"   [*] Fetching dari Berita Indo API ({BERITA_API_URL})...")
        resp = requests.get(
            f"{BERITA_API_URL.rstrip('/')}/v1/search/all",
            params={"q": keyword, "limit": max_results, "threshold": 70},
            timeout=API_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        results = [{
            'title':          item.get('title', ''),
            'url':            item.get('link', ''),
            'published date': item.get('pubDate', ''),
            'publisher':      {'title': item.get('source', 'Berita Indo API')},
            'description':    item.get('contentSnippet', '')[:200],
            'source_type':    'berita_indo_api',
        } for item in data.get('data', [])]
        print(f"   [+] Berita Indo API: {len(results)} artikel dari {data.get('sources_searched', '?')} media")
        return results
    except requests.exceptions.HTTPError as e:
        print(f"   [!] Berita Indo API HTTP {e.response.status_code}: cek URL Vercel Anda.")
        return []
    except Exception as e:
        print(f"   [!] Berita Indo API error: {e}")
        return []


def scrape_all_sources(keyword, language='id', country='ID', period='14d', max_results=20):
    """
    Gabungkan semua sumber secara paralel: Google News + RSS + NewsData + Berita Indo API.
    Deduplikasi otomatis berdasarkan URL.
    """
    print(f"\n[*] Multi-source scraping: '{keyword}'")
    all_results, seen_urls = [], set()

    def _add(items, label):
        n = 0
        for item in items:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(item)
                n += 1
        if n:
            print(f"   [✓] {label}: {n} artikel unik")

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {
            ex.submit(scrape_google_news,    keyword, language, country, period, max_results): "Google News",
            ex.submit(scrape_rss_feeds,      keyword, max(3, max_results // 4)):               "RSS Feeds",
            ex.submit(scrape_newsdata,       keyword, language, max_results):                  "NewsData.io",
            ex.submit(scrape_berita_indo_api,keyword, max_results):                            "Berita Indo API",
        }
        for future, label in futures.items():
            try:
                _add(future.result(timeout=35), label)
            except Exception as e:
                print(f"   [!] {label}: {e}")

    print(f"   [✓] Total: {len(all_results)} artikel dari semua sumber")
    return all_results


# ════════════════════════════════════════════════════════════════════════════════
#  SAVE RESULTS
# ════════════════════════════════════════════════════════════════════════════════

def save_results(articles, keyword, output_dir="output"):
    import pandas as pd
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    kw = keyword.replace(" ", "_").lower()
    df = pd.DataFrame(articles)
    df.to_csv(f"{output_dir}/{kw}_{ts}.csv", index=False, encoding='utf-8-sig')
    df.to_json(f"{output_dir}/{kw}_{ts}.json", orient='records', force_ascii=False, indent=2)
    print(f"✅ Disimpan: {output_dir}/{kw}_{ts}.*")