# 📡 MedMon — Media Monitoring & Sentiment Analysis

**Media Online Network and Tracking Research**
Sistem media monitoring otomatis untuk mengumpulkan, menganalisis sentimen, dan melaporkan pemberitaan secara real-time.

---

## 📋 Deskripsi

MedMon adalah platform **media monitoring** multi-sumber yang menggabungkan:

1. **Web Scraping Multi-Source** — Mengumpulkan berita dari Google News, 18+ RSS feeds media nasional, NewsData.io API, dan Berita Indo API secara paralel
2. **Ekstraksi Konten Cerdas** — Pipeline 4-tahap (trafilatura → readability-lxml → newspaper3k → Selenium) dengan anti-bot detection
3. **Analisis Sentimen AI** — Menggunakan model IndoBERT yang di-fine-tune khusus untuk konteks berita Indonesia
4. **Dashboard Interaktif** — Visualisasi via Streamlit dengan grafik, word cloud, tren, dan export laporan
5. **TypeScript Crawler** — Crawler alternatif menggunakan Crawlee + Playwright untuk scraping Tempo.co

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Multi-Source Scraping** | Google News (GNews), RSS Feeds (18 media), NewsData.io, Berita Indo API |
| **Smart Extraction** | Pipeline cascade: trafilatura → readability → newspaper3k → Selenium |
| **Anti-Bot Detection** | Rotasi User-Agent, browser headers realistis, HTTP/2, jeda acak |
| **Fuzzy Keyword Matching** | Exact, AND-logic, dan fuzzy matching via rapidfuzz |
| **Sentiment Analysis** | Model IndoBERT lokal (fine-tuned), batch processing terpisah dari scraping |
| **Dashboard Streamlit** | Grafik batang, pie chart, tren harian, word cloud, export CSV/Excel/PDF |
| **Review & Approval** | Workflow review berita: Pending → Analisis AI → Koreksi Manual → Publish |
| **Multi-User Auth** | Autentikasi berbasis peran (Super User, Level 1, Level 2) |
| **Laporan Periodik** | Triwulan, Semester, Tahunan dengan export Excel & PDF |
| **Crawlee Crawler** | TypeScript crawler dengan Cheerio dan Playwright untuk Tempo.co |

---

## 🛠️ Tech Stack

### Python (Backend Utama)
| Library | Fungsi |
|---------|--------|
| `streamlit` | Web dashboard & UI |
| `gnews` | Google News scraping |
| `feedparser` | RSS feed parser |
| `trafilatura` | Ekstraksi konten web |
| `readability-lxml` | Fallback ekstraksi (algoritma Firefox Reader) |
| `newspaper3k` | Fallback ekstraksi artikel |
| `selenium` | Last-resort browser automation |
| `googlenewsdecoder` | Decode URL terenkripsi Google News |
| `httpx` | HTTP client dengan HTTP/2 support |
| `rapidfuzz` | Fuzzy string matching |
| `transformers` | HuggingFace pipeline untuk IndoBERT |
| `pymysql` | MySQL database connector |
| `matplotlib` / `wordcloud` | Visualisasi data |
| `pandas` / `openpyxl` | Data processing & Excel export |

### TypeScript (Crawler Alternatif)
| Library | Fungsi |
|---------|--------|
| `crawlee` | Framework web crawling |
| `playwright` | Browser automation |
| `typescript` | Type-safe development |

### Database & Infrastruktur
| Teknologi | Fungsi |
|-----------|--------|
| **MySQL** (via Laragon) | Primary database |
| **Chrome/Chromium** | Headless browser untuk Selenium & Playwright |

---

## 📁 Struktur Projek

```
Crawlee-ASABRINews/
├── medmon.py                  # Engine utama: scraping, ekstraksi, sentimen
├── streamlit_app.py           # Dashboard Streamlit v3 (MedMon Analyzer)
├── claude_version.py          # Dashboard Streamlit v4 (MONITOR)
├── db.py                      # Database operations (MySQL)
├── db_tambahan.py             # Fungsi DB tambahan (auth, tone, attachments)
├── migrate.py                 # Database migration script
├── main.py                    # Standalone scraper (GNews + Selenium)
│
├── asabri_sentiment_model/    # Model IndoBERT fine-tuned (lokal)
│   ├── config.json
│   ├── model.safetensors      # ~497MB model weights
│   ├── vocab.txt
│   ├── tokenizer_config.json
│   ├── training_metadata.json
│   └── training_history.json
│
├── src/                       # TypeScript Crawlee crawlers
│   ├── main.ts                # Cheerio crawler entry
│   ├── playwright-crawler.ts  # Playwright crawler
│   ├── browser-crawler.ts     # Browser-based crawler
│   ├── simple-crawler.ts      # Simple crawler
│   ├── routes.ts              # URL routing & handlers
│   ├── types.ts               # TypeScript type definitions
│   └── utils.ts               # Utility functions
│
├── kaggle_version/            # Versi portabel untuk Kaggle
│   ├── medmon_kaggle.py
│   ├── db_kaggle.py           # SQLite version
│   ├── streamlit_kaggle.py
│   ├── main_kaggle_headless.py
│   └── medmon_unified.ipynb
│
├── output/                    # Hasil scraping (CSV/JSON)
├── uploads/                   # File bukti pemberitaan
├── storage/                   # Crawlee storage
│
├── package.json               # Node.js dependencies (Crawlee)
├── tsconfig.json              # TypeScript config
├── .env.example               # Template environment variables
└── .gitignore
```

---

## ⚙️ Instalasi & Setup

### Prasyarat
- **Python** ≥ 3.10
- **Node.js** ≥ 18.0 (untuk TypeScript crawler)
- **MySQL** (via Laragon, XAMPP, atau standalone)
- **Chrome/Chromium** (untuk Selenium)

### 1. Clone Repository
```bash
git clone https://github.com/<username>/Crawlee-ASABRINews.git
cd Crawlee-ASABRINews
```

### 2. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env dan isi semua variabel yang dibutuhkan
```

### 3. Install Python Dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install streamlit gnews feedparser trafilatura readability-lxml newspaper3k
pip install selenium googlenewsdecoder httpx rapidfuzz
pip install transformers torch pymysql pandas openpyxl
pip install matplotlib wordcloud lxml_html_clean
pip install python-dotenv
```

### 4. Install TypeScript Dependencies (Opsional)
```bash
npm install
npx playwright install chromium
```

### 5. Setup Database
```bash
# Pastikan MySQL sudah berjalan
# Database akan dibuat otomatis saat aplikasi pertama kali dijalankan
python -c "import db; db.init_database()"

# Jalankan migration jika perlu
python migrate.py
```

### 6. Download/Siapkan Model Sentiment (Opsional)
Letakkan model IndoBERT yang sudah di-fine-tune di folder `asabri_sentiment_model/`:
```
asabri_sentiment_model/
├── config.json
├── model.safetensors
├── vocab.txt
├── tokenizer_config.json
└── special_tokens_map.json
```

---

## 🚀 Cara Menjalankan

### Dashboard Streamlit (Utama)
```bash
# MedMon v3 (streamlit_app.py)
streamlit run streamlit_app.py

# MONITOR v4 (claude_version.py) — versi fitur lebih lengkap
streamlit run claude_version.py
```

### Standalone Scraper (Tanpa Dashboard)
```bash
python main.py
```

### TypeScript Crawler
```bash
# Build TypeScript
npm run build

# Jalankan Playwright crawler
npm start

# Jalankan Cheerio crawler
npm run start:cheerio
```

### Batch Sentiment Analysis
```bash
python -c "import medmon, db; medmon.run_batch_sentiment(db)"
```

---

## 🔐 Environment Variables

| Variable | Deskripsi | Contoh |
|----------|-----------|--------|
| `NEWSDATA_API_KEY` | API key dari [newsdata.io](https://newsdata.io) | `pub_xxxxxxxxxxxx` |
| `BERITA_API_URL` | URL Berita Indo API (Vercel) | `https://your-app.vercel.app` |
| `DB_HOST` | MySQL host | `localhost` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | *(kosong untuk Laragon)* |
| `DB_NAME` | Nama database | `medmon` |
| `DEFAULT_ADMIN_PASSWORD` | Password admin default | `changeme` |
| `SENTIMENT_MODEL_PATH` | Path ke folder model sentiment | `asabri_sentiment_model` |

---

## 📊 Arsitektur Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    SUMBER BERITA                         │
│  Google News │ RSS (18 media) │ NewsData.io │ Berita API│
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              KEYWORD MATCHING (rapidfuzz)                │
│     Exact → AND-logic → Fuzzy (threshold 85%)           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              EKSTRAKSI KONTEN (cascade)                  │
│  trafilatura → readability → newspaper3k → Selenium     │
│  + Anti-bot headers + Content validation                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  MySQL DATABASE                         │
│  articles │ keywords │ users │ scrape_history           │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
┌───────────────────┐  ┌───────────────────┐
│  SENTIMENT (batch)│  │ STREAMLIT DASHBOARD│
│  IndoBERT local   │  │ Grafik, Tren, WC  │
│  Fine-tuned model │  │ Review & Approval │
└───────────────────┘  │ Export CSV/Excel  │
                       └───────────────────┘
```

---

## 📜 Lisensi

MIT License
