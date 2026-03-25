from gnews import GNews
from newspaper import Article
from googlenewsdecoder import new_decoderv1
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import shutil
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# Initialize IndoBERT Sentiment Model (Lazy Loading)
_sentiment_pipeline = None

def get_sentiment_pipeline():
    """Lazy load the sentiment pipeline to avoid long startup time."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        print("[*] Loading IndoBERT Sentiment Model (first run only)...")
        model_name = "crypter70/IndoBERT-Sentiment-Analysis"
        try:
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            print("[+] IndoBERT Model loaded successfully.")
        except Exception as e:
            print(f"[!] Log warning: Failed to load sentiment model: {e}")
            return None
    return _sentiment_pipeline

def preprocess_text(text):
    """
    Preprocessing teks sebelum analisis sentimen.
    """
    import re
    
    if not text:
        return ""
    
    # 1. Hapus URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 2. Hapus email
    text = re.sub(r'\S+@\S+', '', text)
    
    # 3. Hapus HTML tags (jika ada sisa)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 4. Hapus karakter khusus kecuali tanda baca penting (. , ! ? -)
    text = re.sub(r'[^\w\s.,!?\-]', '', text)
    
    # 5. Hapus whitespace berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 6. Hapus baris kosong berulang
    text = re.sub(r'\n+', '\n', text)
    
    return text

def analyze_sentiment(text):
    """
    Menganalisis sentimen teks menggunakan IndoBERT.
    """
    try:
        # Step 1: Preprocessing - clean the text
        text_clean = preprocess_text(text)
        
        # Step 2: Truncate text to max 512 tokens (BERT limit ~1500 chars)
        text_truncated = text_clean[:1500] if text_clean else ""
        
        if not text_truncated:
            return 0, "Neutral"
        
        # Step 3 & 4: Tokenization + Inference (handled by pipeline)
        pipe = get_sentiment_pipeline()
        if not pipe:
             return 0, "Neutral" # Fallback if model failed to load

        result = pipe(text_truncated)[0]
        
        label = result['label']
        score = result['score']
        
        # Step 5: Normalize labels
        if label.lower() in ['positive', 'positif', 'label_2']:
            return score, "Positive"
        elif label.lower() in ['negative', 'negatif', 'label_0']:
            return score, "Negative"
        else:
            return score, "Neutral"
    except Exception as e:
        print(f"   [!] Sentiment error: {e}")
        return 0, "Neutral"

def decode_google_news_url(google_url):
    """
    Decode URL Google News menggunakan googlenewsdecoder package.
    """
    try:
        # Cek apakah URL adalah Google News URL
        if 'news.google.com' in google_url:
            print(f"   [*] Decoding Google News URL...")
            decoded_url = new_decoderv1(google_url, interval=5)
            
            if decoded_url.get("status"):
                real_url = decoded_url["decoded_url"]
                print(f"   [+] Berhasil decode URL")
                return real_url
            else:
                print(f"   [!] Decoder error: {decoded_url.get('message', 'Unknown error')}")
                return None
        else:
            # Jika bukan Google News URL, kembalikan URL asli
            return google_url
    except Exception as e:
        print(f"   [!] Gagal decode URL: {e}")
        return None

def scrape_google_news(keyword, language='id', country='ID', period='14d', max_results=20):
    """
    Scrape berita dari Google News berdasarkan keyword
    """
    import time as t
    
    # Add small delay to avoid rate limiting
    t.sleep(1)
    
    try:
        google_news = GNews(
            language=language,
            country=country,
            period=period,
            max_results=max_results
        )
        
        news = google_news.get_news(keyword)
        
        if not news:
            print(f"   [!] GNews returned empty for '{keyword}', trying without period filter...")
            # Try without strict period
            google_news_retry = GNews(
                language=language,
                country=country,
                max_results=max_results
            )
            news = google_news_retry.get_news(keyword)
        
        return news if news else []
        
    except Exception as e:
        print(f"   [!] GNews error: {e}")
        return []


def get_article_with_selenium(url):
    """
    Fallback method: Menggunakan Selenium untuk mengambil konten artikel
    yang tidak bisa diambil dengan newspaper3k
    """
    driver = None
    try:
        print(f"   [*] Mencoba dengan Selenium (Kaggle Mode)...")
        
        # Setup Chrome options untuk headless mode di Kaggle
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Try to find chrome binary if needed (Kaggle usually has it in path)
        # chrome_options.binary_location = "/usr/bin/google-chrome" # Uncomment if needed on specific envs

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Tunggu sampai halaman dimuat
        time.sleep(3)
        
        # Ambil judul
        title = driver.title
        
        # Coba ambil konten dari berbagai selector umum
        content_selectors = [
            "article",
            "[class*='article-content']",
            "[class*='article-body']",
            "[class*='content-body']",
            "[class*='post-content']",
            "[class*='entry-content']",
            ".detail-text",
            ".read__content",
            "#article-content",
            "main"
        ]
        
        content = ""
        for selector in content_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for el in elements:
                        text = el.text.strip()
                        if len(text) > len(content):
                            content = text
            except:
                continue
        
        # Jika tidak ada konten, ambil body
        if not content:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                content = body.text[:2000]  # Batasi 2000 karakter
            except:
                pass
        
        if content:
            print(f"   [+] Berhasil ekstrak dengan Selenium")
            return {
                'title': title,
                'text': content,
                'authors': [],
                'publish_date': None,
                'url': url,
                'top_image': None
            }
        
        return None
        
    except Exception as e:
        print(f"   [!] Selenium error: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def get_full_article(url):
    """
    Mendapatkan artikel lengkap dari URL dengan fallback ke Selenium
    """
    # Decode Google News URL jika perlu
    real_url = decode_google_news_url(url)
    
    # Jika decode gagal, return None
    if not real_url:
        print("   [!] Tidak bisa mendapatkan URL asli artikel")
        return None
    
    print(f"   -> URL Asli: {real_url[:60]}...")
    
    # Metode 1: Coba dengan newspaper3k (lebih cepat)
    try:
        print(f"   [*] Mencoba dengan Newspaper3k...")
        article = Article(real_url)
        article.download()
        article.parse()
        
        # Cek apakah berhasil mendapatkan konten
        if article.text and len(article.text) > 100:
            print(f"   [+] Berhasil ekstrak dengan Newspaper3k")
            return {
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'url': real_url,
                'top_image': article.top_image
            }
        else:
            print(f"   [!] Newspaper3k: Konten kosong/terlalu pendek")
            
    except Exception as e:
        print(f"   [!] Newspaper3k error: {e}")
    
    # Metode 2: Fallback ke Selenium
    return get_article_with_selenium(real_url)


def save_results(articles, keyword, output_dir="output"):
    """Menyimpan hasil scrape ke CSV dan JSON"""
    import pandas as pd
    
    # Buat folder output jika belum ada
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate timestamp untuk nama file yang unik
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keyword_clean = keyword.replace(" ", "_").lower()
    
    # Convert ke DataFrame
    df = pd.DataFrame(articles)
    
    # Simpan ke CSV
    csv_filename = f"{output_dir}/{keyword_clean}_{timestamp}.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"✅ Hasil disimpan ke CSV: {csv_filename}")
    
    # Simpan ke JSON
    json_filename = f"{output_dir}/{keyword_clean}_{timestamp}.json"
    df.to_json(json_filename, orient='records', force_ascii=False, indent=2)
    print(f"✅ Hasil disimpan ke JSON: {json_filename}")
    
    return csv_filename, json_filename
