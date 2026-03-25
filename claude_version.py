"""
MONITOR v4.0 – Media Online Network and Tracking Research
PT ASABRI (Persero) | Bidang Komunikasi dan Protokoler | Sekretariat Perusahaan

Implementasi lengkap sesuai Business Requirements Specification (BRS).
Fitur yang diimplementasikan:
  - Autentikasi berbasis peran (Super User, Level 1 – Sesper, Level 2 – Kabid/Staf)
  - Dashboard Media Monitoring dengan grafik bulanan, pie chart, rekap tabel, wordcloud judul
  - Monitoring & Review Berita: input manual kategori media (24 tier), sumber, tipe konten,
    override tone, upload bukti, submit review
  - Pengaturan Tone: manajemen keyword positif/negatif/netral yang dapat dikustomisasi user
  - Laporan periodik: Triwulan, Semester, Tahunan dengan export Excel, PNG, PDF
  - Manajemen User (Super User only): tambah/hapus user, atur role
  - Filter news vs video, filter sumber internal/eksternal, filter tier media

CATATAN: Fungsi DB baru yang dibutuhkan ada di file db_tambahan.py.
         Merge isi file tersebut ke db.py Anda agar seluruh fitur berjalan.
"""

import os
import streamlit as st
import pandas as pd
import time
import hashlib
import io
import sys
import json
import base64
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from wordcloud import WordCloud
import numpy as np

import medmon
import db


# ==============================================================================
# KONSTANTA
# ==============================================================================

# 24 Kategori media sesuai BRS
MEDIA_CATEGORIES = [
    "TV Nasional", "TV Lokal", "Running Text Nasional", "Running Text Lokal",
    "Media Cetak Nasional", "Media Cetak Lokal", "Radio Nasional", "Radio Lokal",
    "Media Online Tier 1", "Media Online Tier 2", "Media Online Tier 3 (Regional)",
    "Media Online Lokal", "International Media", "Twitter", "Facebook",
    "Instagram Feeds", "Instagram Reels", "Tiktok", "Youtube Short",
    "Youtube Video", "KOL Instagram Reels", "KOL Tiktok Reels",
    "Homeless Media Instagram Reels", "Homeless Media Instagram Photo",
]

CONTENT_TYPES  = ["Berita / Artikel", "Video"]
SOURCE_TYPES   = ["Eksternal", "Internal"]
TONE_OPTIONS   = ["Positive", "Negative", "Neutral"]
MONTH_NAMES    = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]

ROLES = {
    "super_user": "Super User",
    "level_1":    "Level 1 – Sesper",
    "level_2":    "Level 2 – Kabid/Staf",
}

REPORT_PERIODS = {
    "Triwulan I   (Jan–Mar)": [1, 2, 3],
    "Triwulan II  (Apr–Jun)": [4, 5, 6],
    "Triwulan III (Jul–Sep)": [7, 8, 9],
    "Triwulan IV  (Okt–Des)": [10, 11, 12],
    "Semester I   (Jan–Jun)": [1, 2, 3, 4, 5, 6],
    "Semester II  (Jul–Des)": [7, 8, 9, 10, 11, 12],
    "Tahunan      (Jan–Des)": list(range(1, 13)),
}

# Keyword tone default sesuai BRS
DEFAULT_TONE_KEYWORDS = {
    "Positive": [
        "aksi", "meningkat", "kinerja", "membanggakan", "penyerahan",
        "anugerah", "penghargaan", "sukses", "berhasil", "prestasi",
        "terbaik", "inovasi", "apresiasi", "sinergi", "kolaborasi",
    ],
    "Negative": [
        "korupsi", "menurun", "sulit", "kritik", "krisis",
        "masalah", "gagal", "buruk", "skandal", "dugaan",
        "pidana", "kerugian", "dituding", "cekal", "tersangka",
    ],
    "Neutral": [
        "terlibat", "menyebut", "instansi", "pertemuan",
        "rapat", "kegiatan", "sosialisasi", "agenda", "hadir",
    ],
}

TONE_COLORS = {"Positive": "#22c55e", "Negative": "#ef4444", "Neutral": "#64748b"}
BG_COLOR     = "#0E1117"
CARD_COLOR   = "#1e2535"


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="MONITOR – PT ASABRI",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# CSS
# ==============================================================================

st.markdown("""
<style>
/* ── global ── */
.main { background-color: #0E1117; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* ── buttons ── */
.stButton > button {
    border-radius: 7px; height: 2.8em;
    background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%);
    color: white; font-weight: 600; border: none; width: 100%;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #2563eb 0%, #1e3a8a 100%);
    box-shadow: 0 4px 14px rgba(37,99,235,0.45);
}
/* danger variant – wrap in st.container() with class btn-danger */
div[data-testid="stVerticalBlock"] .btn-danger > .stButton > button {
    background: linear-gradient(90deg, #b91c1c 0%, #ef4444 100%) !important;
}

/* ── heading ── */
h1 {
    background: -webkit-linear-gradient(40deg, #1d4ed8, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* ── keyword tags ── */
.kw-tag {
    display: inline-block;
    background: linear-gradient(90deg,#1e3a8a,#2563eb);
    color:#fff; padding:4px 12px; border-radius:14px; margin:3px; font-size:13px;
}

/* ── role badges ── */
.badge-super  { background:#7c3aed; color:#fff; padding:2px 9px; border-radius:7px; font-size:12px; }
.badge-level1 { background:#0891b2; color:#fff; padding:2px 9px; border-radius:7px; font-size:12px; }
.badge-level2 { background:#0d9488; color:#fff; padding:2px 9px; border-radius:7px; font-size:12px; }

/* ── tone chips ── */
.tone-pos { color:#22c55e; font-weight:700; }
.tone-neg { color:#ef4444; font-weight:700; }
.tone-neu { color:#94a3b8; font-weight:700; }

/* ── divider ── */
.hr { border-top: 1px solid #334155; margin: 14px 0; }

/* ── metric card ── */
.metric-box {
    background: #1e2535; border-radius: 10px; padding: 14px 18px;
    border-left: 4px solid #2563eb; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def fig_to_png(fig) -> bytes:
    """Konversi matplotlib figure ke PNG bytes untuk download."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()


def df_to_excel(df: pd.DataFrame, sheet: str = "Data") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    return buf.getvalue()


def tone_badge(tone: str) -> str:
    cls = {"Positive": "tone-pos", "Negative": "tone-neg"}.get(tone, "tone-neu")
    return f'<span class="{cls}">{tone}</span>'


def role_badge(role: str) -> str:
    cls = {"super_user": "badge-super", "level_1": "badge-level1"}.get(role, "badge-level2")
    return f'<span class="{cls}">{ROLES.get(role, role)}</span>'


def can_edit(role: str) -> bool:
    """Level 2 dan Super User dapat menambah/mengedit data monitoring."""
    return role in ("super_user", "level_2")


def can_manage_users(role: str) -> bool:
    return role == "super_user"


# ==============================================================================
# DB COMPATIBILITY LAYER
# Wrapper aman agar aplikasi tetap jalan walaupun fungsi baru belum ada di db.py
# ==============================================================================

def _call(fn_name, *args, default=None, **kwargs):
    """Panggil db.<fn_name> jika ada, kembalikan default jika tidak."""
    fn = getattr(db, fn_name, None)
    if fn is None:
        return default
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return default


def db_authenticate(username, pw_hash):
    user = _call("authenticate_user", username, pw_hash, default=None)
    if user is None and username == "admin" and pw_hash == hash_pw(os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme")):
        # Fallback hardcoded admin agar bisa login meski db belum diupdate
        return {"id": 0, "username": "admin", "full_name": "Administrator", "role": "super_user"}
    return user


def db_get_users():         return _call("get_users", default=[])
def db_add_user(u, p, r, n): return _call("add_user", u, p, r, n, default=None)
def db_delete_user(uid):    return _call("delete_user", uid, default=False)

def db_get_tone_kw():       return _call("get_tone_keywords", default=[])
def db_add_tone_kw(w, t):   return _call("add_tone_keyword", w, t, default=None)
def db_del_tone_kw(kid):    return _call("delete_tone_keyword", kid, default=False)

def db_update_article_tone(aid, tone):
    return _call("update_article_tone", aid, tone, default=False)

def db_update_article_meta(aid, media_cat, source_type, content_type):
    return _call("update_article_meta", aid, media_cat, source_type, content_type, default=False)

def db_save_attachment(aid, filename, data):
    return _call("save_attachment", aid, filename, data, default=False)


def load_tone_keywords() -> dict:
    """Muat tone keywords dari DB; fallback ke default jika kosong."""
    rows = db_get_tone_kw()
    result = {"Positive": [], "Negative": [], "Neutral": []}
    for r in rows:
        t = r.get("tone_type", "Neutral")
        if t in result:
            result[t].append(r["word"])
    # Jika DB kosong, gunakan default BRS
    if not any(result.values()):
        return {k: list(v) for k, v in DEFAULT_TONE_KEYWORDS.items()}
    return result


def tone_from_keywords(text: str, tone_kw: dict) -> str:
    """Tentukan tone berdasarkan keyword list, returns 'Neutral' jika tidak ada match."""
    tl = text.lower()
    scores = {t: sum(1 for w in ws if w.lower() in tl) for t, ws in tone_kw.items()}
    if max(scores.values()) == 0:
        return "Neutral"
    return max(scores, key=scores.get)


# ==============================================================================
# DATABASE INIT + SESSION STATE
# ==============================================================================

try:
    db.init_database()
    _call("init_auth_tables")
    _call("init_tone_keyword_tables")
except Exception as e:
    st.error(f"⚠️ Database Error: {e} — Pastikan MySQL/Laragon sudah running.")
    st.stop()

_DEFAULTS = {
    "logged_in":      False,
    "user":           None,
    "results":        [],
    "is_scraping":    False,
    "terminal_logs":  "",
    "active_keywords": [],
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

def do_login(username, password):
    user = db_authenticate(username, hash_pw(password))
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user
        return True
    return False


def do_logout():
    for k in list(_DEFAULTS.keys()):
        st.session_state[k] = _DEFAULTS[k]
    st.rerun()


# ── Login Page ───────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 📡 MONITOR")
        st.markdown("**Media Online Network and Tracking Research**")
        st.markdown("PT ASABRI (Persero)")
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        with st.form("login_form"):
            uname = st.text_input("Username", placeholder="Masukkan username")
            passw = st.text_input("Password", type="password", placeholder="Masukkan password")
            if st.form_submit_button("🔐 Login", use_container_width=True):
                if do_login(uname, passw):
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
        st.caption("Default login: **admin** / **(lihat .env DEFAULT_ADMIN_PASSWORD)**  (ubah setelah login pertama)")
    st.stop()


# ==============================================================================
# SETELAH LOGIN
# ==============================================================================

def load_keywords():
    try:
        st.session_state.active_keywords = [k["keyword"] for k in db.get_keywords()]
    except:
        st.session_state.active_keywords = []

load_keywords()

_user = st.session_state.user
_role = _user["role"]


# ==============================================================================
# LOGGER
# ==============================================================================

class StreamlitLogger:
    def __init__(self):
        self.buf = []
    def write(self, msg):
        self.buf.append(msg)
    def flush(self):
        pass
    def get_logs(self):
        return "".join(self.buf)


# ==============================================================================
# PROCESS SINGLE ARTICLE (threading helper)
# ==============================================================================

def process_single_article(news_item, keyword_id, keyword, tone_kw=None):
    """
    Ambil, analisis, dan simpan satu artikel.
    Return: (article_data | None, status)
    Status: 'new' | 'duplicate' | 'filtered' | 'failed'
    """
    try:
        title_raw = news_item.get("title", "")
        kl = keyword.lower()
        tl = title_raw.lower()
        parts = [p for p in kl.split() if len(p) > 2]
        found = any(p in tl for p in parts) or kl in tl
        if not found:
            return ({"title": title_raw}, "filtered")

        full = medmon.get_full_article(news_item["url"])
        if not full:
            return (None, "failed")

        # Tanggal publikasi
        pub_date = full.get("publish_date") or news_item.get("published date")
        full["publish_date"] = pub_date
        full["publisher"]    = news_item.get("publisher", {}).get("title", "Unknown")

        # Sentimen: model NLP utama
        title   = full.get("title", "")
        content = full.get("text", "")
        combined = f"{title}. {content}" if content else title
        score, label = medmon.analyze_sentiment(combined)

        # Override dengan keyword list BRS jika ada match yang lebih spesifik
        if tone_kw:
            kw_label = tone_from_keywords(title, tone_kw)
            if kw_label != "Neutral":
                label = kw_label

        full["sentiment_score"] = score
        full["sentiment_label"] = label

        res = db.save_article(full, keyword_id)
        if res == "duplicate": return (full, "duplicate")
        if res:                return (full, "new")
        return (full, "failed")

    except Exception as e:
        print(f"[!] Error: {e}")
        return (None, "failed")


# ==============================================================================
# SIDEBAR
# ==============================================================================

with st.sidebar:
    st.markdown("### 📡 MONITOR v4.0")
    st.caption("Media Monitoring PT ASABRI")
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    # ── User info ──
    st.markdown(
        f"👤 **{_user['full_name']}**<br>{role_badge(_role)}",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Logout"):
        do_logout()

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    # ── Keyword management (hanya level 2 & super user) ──
    if can_edit(_role):
        st.subheader("📌 Keyword Monitoring")
        if st.session_state.active_keywords:
            kw_html = "".join(f'<span class="kw-tag">{k}</span>'
                              for k in st.session_state.active_keywords)
            st.markdown(kw_html, unsafe_allow_html=True)
        else:
            st.info("Belum ada keyword. Tambahkan di bawah.")

        new_kw = st.text_input("Tambah Keyword", placeholder="e.g. PT ASABRI")
        if st.button("➕ Tambah Keyword"):
            if new_kw and new_kw.strip():
                kc = new_kw.strip()
                if kc.lower() in [k.lower() for k in st.session_state.active_keywords]:
                    st.warning(f"Keyword '{kc}' sudah ada.")
                else:
                    try:
                        db.add_keyword(kc)
                        st.session_state.active_keywords.append(kc)
                        st.success(f"✅ '{kc}' ditambahkan.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
            else:
                st.warning("Isi keyword terlebih dahulu.")

        # Hapus keyword
        if st.session_state.active_keywords:
            del_kw = st.selectbox("Hapus Keyword", ["— pilih —"] + st.session_state.active_keywords,
                                  key="del_kw_sel")
            if st.button("🗑️ Hapus Keyword") and del_kw != "— pilih —":
                try:
                    _call("delete_keyword", del_kw)
                    st.session_state.active_keywords.remove(del_kw)
                    st.success(f"Keyword '{del_kw}' dihapus.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal hapus: {e}")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # ── Konfigurasi Scraping ──
        st.subheader("⚙️ Konfigurasi Scraping")
        c1, c2 = st.columns(2)
        with c1:
            _lang    = st.selectbox("Bahasa",  ["id", "en"])
        with c2:
            _country = st.selectbox("Negara",  ["ID", "US"])
        _period      = st.select_slider("Periode", ["1h","1d","7d","14d","1m","1y"], value="14d")
        _max_results = st.number_input("Maks Berita/KW", 1, 100, 10)
        _workers     = st.slider("Thread Speed", 1, 10, 5)

        _kw_to_scrape = st.multiselect(
            "Keyword yang di-scrape",
            options=st.session_state.active_keywords,
            default=st.session_state.active_keywords,
        )
        _start_btn = st.button(
            "🚀 Mulai Scraping",
            disabled=st.session_state.is_scraping or len(_kw_to_scrape) == 0,
        )
    else:
        _start_btn = False
        _kw_to_scrape = []


# ==============================================================================
# HEADER
# ==============================================================================

st.title("📡 MONITOR – Media Online Network and Tracking Research")
st.caption(
    f"PT ASABRI (Persero) | Bidang Komunikasi dan Protokoler | "
    f"{datetime.now().strftime('%d %B %Y, %H:%M')} WIB"
)

# ==============================================================================
# TABS
# ==============================================================================

_tab_labels = ["📊 Dashboard", "📈 Tren", "📝 Monitoring Berita",
               "⚙️ Pengaturan Tone", "📄 Laporan", "🖥️ Logs"]
if can_manage_users(_role):
    _tab_labels.append("👥 Manajemen User")

_tabs   = st.tabs(_tab_labels)
_t_dash = _tabs[0]
_t_tren = _tabs[1]
_t_news = _tabs[2]
_t_tone = _tabs[3]
_t_rept = _tabs[4]
_t_logs = _tabs[5]
_t_user = _tabs[6] if len(_tabs) > 6 else None


# ==============================================================================
# SCRAPING LOGIC
# ==============================================================================

if _start_btn and can_edit(_role):
    st.session_state.is_scraping  = True
    st.session_state.results       = []
    st.session_state.terminal_logs = ""

    tone_kw_live = load_tone_keywords()

    with _t_logs:
        _prog  = st.progress(0)
        _stat  = st.empty()
        _term  = st.empty()

    try:
        _cap    = StreamlitLogger()
        _stdout = sys.stdout
        sys.stdout = _cap

        all_arts = []
        total_kw = len(_kw_to_scrape)

        for ki, kw in enumerate(_kw_to_scrape):
            print(f"\n[{ki+1}/{total_kw}] Keyword: {kw}")
            _stat.markdown(f"### 🔍 Scraping: **{kw}** …")

            if ki > 0:
                print("   [*] Jeda 3 detik …")
                time.sleep(3)

            kw_id = db.add_keyword(kw)
            news_list = []
            for attempt in range(2):
                news_list = medmon.scrape_google_news(
                    keyword=kw, language=_lang, country=_country,
                    period=_period, max_results=_max_results,
                )
                if news_list:
                    break
                if attempt == 0:
                    print("   [!] 0 hasil, retry …"); time.sleep(2)

            print(f"   [+] Ditemukan {len(news_list)} artikel")
            kw_arts = []
            pos_c = neg_c = neu_c = new_c = dup_c = fail_c = skip_c = 0

            with ThreadPoolExecutor(max_workers=_workers) as ex:
                futures = {
                    ex.submit(process_single_article, n, kw_id, kw, tone_kw_live): n
                    for n in news_list
                }
                for i, fut in enumerate(as_completed(futures)):
                    prog_val = ((ki * _max_results) + i + 1) / (total_kw * _max_results)
                    _prog.progress(min(prog_val, 1.0))
                    try:
                        data, status = fut.result()
                        if status == "new" and data:
                            new_c += 1
                            data["keyword"] = kw
                            kw_arts.append(data); all_arts.append(data)
                            lbl = data.get("sentiment_label", "Neutral")
                            if lbl == "Positive": pos_c += 1
                            elif lbl == "Negative": neg_c += 1
                            else: neu_c += 1
                            print(f"   [+] NEW: {data['title'][:50]}… ({lbl})")
                        elif status == "duplicate":
                            dup_c += 1
                        elif status == "filtered":
                            skip_c += 1
                        else:
                            fail_c += 1
                    except Exception as exc:
                        fail_c += 1
                        print(f"   [X] {exc}")

                    st.session_state.terminal_logs = _cap.get_logs()
                    _term.code(st.session_state.terminal_logs, language="bash")

            print(f"\n   📊 '{kw}': baru={new_c} duplikat={dup_c} skip={skip_c} gagal={fail_c}")
            db.save_scrape_history(kw_id, len(news_list), len(kw_arts), pos_c, neg_c, neu_c)

        st.session_state.results       = all_arts
        st.session_state.is_scraping   = False
        _stat.success(f"🎉 Selesai! Total {len(all_arts)} artikel baru dari {total_kw} keyword.")
        _prog.progress(100)
        print(f"\n[+] SELESAI. Total: {len(all_arts)} artikel")
        st.session_state.terminal_logs = _cap.get_logs()
        _term.code(st.session_state.terminal_logs, language="bash")

    except Exception as e:
        st.error(f"Error: {e}")
        st.session_state.is_scraping = False
    finally:
        sys.stdout = _stdout


# ==============================================================================
# TAB 1 – DASHBOARD
# ==============================================================================

with _t_dash:
    st.subheader("📊 Dashboard Media Monitoring")

    # ── Filter ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Filter Dashboard", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            f_kw = st.selectbox("Keyword",
                                ["Semua"] + st.session_state.active_keywords, key="d_fkw")
        with fc2:
            f_src = st.selectbox("Sumber", ["Semua"] + SOURCE_TYPES, key="d_fsrc")
        with fc3:
            f_type = st.selectbox("Tipe Konten", ["Semua"] + CONTENT_TYPES, key="d_ftype")
        with fc4:
            f_year = st.number_input("Tahun", min_value=2020,
                                     max_value=datetime.now().year,
                                     value=datetime.now().year, key="d_year")

    # ── Load data ────────────────────────────────────────────────────────────
    try:
        raw = db.get_articles(limit=2000)
    except:
        raw = []

    if raw:
        df_all = pd.DataFrame(raw)
        if "publish_date" in df_all.columns:
            df_all["publish_date"] = pd.to_datetime(df_all["publish_date"], errors="coerce")
            df_all["year"]  = df_all["publish_date"].dt.year
            df_all["month"] = df_all["publish_date"].dt.month

        # Terapkan filter
        df = df_all.copy()
        if f_kw  != "Semua" and "keyword"      in df.columns: df = df[df["keyword"]      == f_kw]
        if f_src != "Semua" and "source_type"  in df.columns: df = df[df["source_type"]  == f_src]
        if f_type!= "Semua" and "content_type" in df.columns: df = df[df["content_type"] == f_type]
        if "year" in df.columns: df = df[df["year"] == f_year]

        # ── Metrik ringkasan ─────────────────────────────────────────────────
        m1, m2, m3, m4, m5 = st.columns(5)
        _tot = len(df)
        _pos = len(df[df["sentiment_label"] == "Positive"]) if "sentiment_label" in df.columns else 0
        _neg = len(df[df["sentiment_label"] == "Negative"]) if "sentiment_label" in df.columns else 0
        _neu = _tot - _pos - _neg
        _src_ext = len(df[df["source_type"]=="Eksternal"]) if "source_type" in df.columns else "-"

        with m1: st.metric("Total Pemberitaan", _tot)
        with m2: st.metric("✅ Positif",  _pos)
        with m3: st.metric("❌ Negatif",  _neg)
        with m4: st.metric("➖ Netral",   _neu)
        with m5: st.metric("📡 Eksternal", _src_ext)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        col_left, col_right = st.columns([3, 2])

        # ── Grafik batang per bulan ──────────────────────────────────────────
        with col_left:
            st.markdown("#### 📅 Rekap Pemberitaan per Bulan")
            if "month" in df.columns and not df.empty:
                monthly = (
                    df.groupby(["month", "sentiment_label"])
                    .size().unstack(fill_value=0)
                    .reindex(range(1, 13), fill_value=0)
                )
                for col in ["Positive", "Negative", "Neutral"]:
                    if col not in monthly.columns:
                        monthly[col] = 0

                fig_bar, ax = plt.subplots(figsize=(9, 4), facecolor=BG_COLOR)
                ax.set_facecolor(CARD_COLOR)
                x = np.arange(12)
                w = 0.27
                ax.bar(x - w, monthly["Positive"], w, color="#22c55e", label="Positif")
                ax.bar(x,     monthly["Neutral"],  w, color="#64748b", label="Netral")
                ax.bar(x + w, monthly["Negative"], w, color="#ef4444", label="Negatif")
                ax.set_xticks(x); ax.set_xticklabels(MONTH_NAMES, color="#cbd5e1")
                ax.tick_params(colors="#cbd5e1")
                ax.spines[["top","right","left","bottom"]].set_color("#334155")
                ax.yaxis.label.set_color("#cbd5e1")
                ax.set_ylabel("Jumlah", color="#cbd5e1")
                ax.legend(labelcolor="#cbd5e1", facecolor=CARD_COLOR, edgecolor="#334155")
                fig_bar.tight_layout()
                st.pyplot(fig_bar)

                # Download PNG grafik
                st.download_button(
                    "⬇️ Download Grafik (PNG)",
                    fig_to_png(fig_bar),
                    file_name=f"grafik_bulanan_{f_year}.png",
                    mime="image/png",
                )
            else:
                st.info("Belum ada data dengan tanggal untuk grafik ini.")

        # ── Pie chart distribusi media ───────────────────────────────────────
        with col_right:
            st.markdown("#### 🥧 Distribusi Media")
            if "media_category" in df.columns and df["media_category"].notna().any():
                cat_counts = df["media_category"].value_counts().head(8)
            elif "publisher" in df.columns:
                cat_counts = df["publisher"].value_counts().head(8)
            else:
                cat_counts = pd.Series(dtype=int)

            if not cat_counts.empty:
                colors = plt.cm.get_cmap("Set2")(np.linspace(0, 1, len(cat_counts)))
                fig_pie, ap = plt.subplots(figsize=(5, 4), facecolor=BG_COLOR)
                ap.set_facecolor(BG_COLOR)
                wedges, texts, autotexts = ap.pie(
                    cat_counts.values,
                    labels=None,
                    autopct="%1.0f%%",
                    startangle=140,
                    colors=colors,
                    pctdistance=0.78,
                )
                for at in autotexts:
                    at.set_color("white"); at.set_fontsize(9)
                ap.legend(
                    wedges, cat_counts.index,
                    loc="lower center", bbox_to_anchor=(0.5, -0.22),
                    ncol=2, fontsize=8,
                    labelcolor="#cbd5e1", facecolor=CARD_COLOR, edgecolor="#334155",
                )
                fig_pie.tight_layout()
                st.pyplot(fig_pie)
                st.download_button(
                    "⬇️ Download Pie (PNG)",
                    fig_to_png(fig_pie),
                    file_name=f"distribusi_media_{f_year}.png",
                    mime="image/png",
                )
            else:
                st.info("Kolom media_category / publisher tidak tersedia.")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        col_a, col_b = st.columns([2, 3])

        # ── Grafik rilis internal vs eksternal ───────────────────────────────
        with col_a:
            st.markdown("#### 📊 Rilis Internal vs Eksternal")
            if "source_type" in df.columns and df["source_type"].notna().any():
                src_c = df["source_type"].value_counts()
                fig_src, ax2 = plt.subplots(figsize=(4, 3), facecolor=BG_COLOR)
                ax2.set_facecolor(CARD_COLOR)
                bars = ax2.bar(src_c.index, src_c.values,
                               color=["#2563eb", "#0891b2"])
                for bar, val in zip(bars, src_c.values):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                             str(val), ha="center", color="#cbd5e1", fontsize=10)
                ax2.tick_params(colors="#cbd5e1")
                ax2.spines[["top","right","left","bottom"]].set_color("#334155")
                fig_src.tight_layout()
                st.pyplot(fig_src)
            else:
                st.info("Data sumber (internal/eksternal) belum diisi pada artikel.")

        # ── Tabel rekap bulanan ───────────────────────────────────────────────
        with col_b:
            st.markdown("#### 🗓️ Tabel Rekapitulasi Bulanan")
            if "month" in df.columns and not df.empty:
                recap = df.groupby("month").apply(
                    lambda g: pd.Series({
                        "Positif":  (g["sentiment_label"] == "Positive").sum() if "sentiment_label" in g else 0,
                        "Negatif":  (g["sentiment_label"] == "Negative").sum() if "sentiment_label" in g else 0,
                        "Netral":   (g["sentiment_label"] == "Neutral").sum()  if "sentiment_label" in g else 0,
                        "Total":    len(g),
                    })
                ).reset_index()
                recap["Bulan"] = recap["month"].apply(lambda m: MONTH_NAMES[m-1])
                recap = recap[["Bulan","Positif","Negatif","Netral","Total"]]
                st.dataframe(recap, use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇️ Download Rekap (Excel)",
                    df_to_excel(recap, "Rekap Bulanan"),
                    file_name=f"rekap_bulanan_{f_year}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.info("Belum ada data tanggal untuk rekap bulanan.")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # ── Word Cloud dari judul berita ─────────────────────────────────────
        st.markdown("#### ☁️ Kata Trending dari Judul Berita")
        if "title" in df.columns and not df.empty:
            all_titles = " ".join(df["title"].dropna().tolist())
            # Stopwords dasar Bahasa Indonesia
            stopwords_id = {
                "dan","di","ke","dari","yang","untuk","dengan","ini","itu","pada",
                "adalah","akan","atau","dalam","tidak","juga","sudah","saat","bisa",
                "lebih","oleh","kami","atas","bagi","lain","serta","telah","karena",
                "pt","tbk","persero","indonesia","sebagai","terhadap","para","pun",
            }
            if all_titles.strip():
                wc = WordCloud(
                    width=900, height=350,
                    background_color=CARD_COLOR,
                    colormap="Blues",
                    stopwords=stopwords_id,
                    max_words=80,
                ).generate(all_titles)
                fig_wc, axwc = plt.subplots(figsize=(11, 3.5), facecolor=CARD_COLOR)
                axwc.imshow(wc, interpolation="bilinear")
                axwc.axis("off")
                fig_wc.tight_layout(pad=0)
                st.pyplot(fig_wc)
                st.download_button(
                    "⬇️ Download Word Cloud (PNG)",
                    fig_to_png(fig_wc),
                    file_name=f"wordcloud_judul_{f_year}.png",
                    mime="image/png",
                )
            else:
                st.info("Tidak cukup teks judul untuk Word Cloud.")
        else:
            st.info("Kolom judul tidak tersedia.")

    else:
        st.info("Belum ada data. Lakukan scraping terlebih dahulu dari sidebar.")


# ==============================================================================
# TAB 2 – TREN
# ==============================================================================

with _t_tren:
    st.subheader("📈 Analisis Tren Pemberitaan")
    try:
        tc1, tc2 = st.columns(2)
        with tc1:
            days_r = st.selectbox("Rentang Waktu (hari)", [7, 14, 30, 60, 90], index=1)
        with tc2:
            t_kw = st.selectbox("Filter Keyword", ["Semua"] + st.session_state.active_keywords)

        kw_id_t = None
        if t_kw != "Semua":
            for k in db.get_keywords():
                if k["keyword"] == t_kw:
                    kw_id_t = k["id"]; break

        trend = db.get_trend_data(keyword_id=kw_id_t, days=days_r)
        if trend:
            tdf = pd.DataFrame(trend)
            tdf["date"] = pd.to_datetime(tdf["date"])
            tdf = tdf.set_index("date")

            st.markdown("#### 📰 Jumlah Artikel per Hari")
            st.line_chart(tdf["total"])

            st.markdown("#### 🎭 Tren Sentimen Harian")
            cols_avail = [c for c in ["positive","negative","neutral"] if c in tdf.columns]
            st.area_chart(tdf[cols_avail])

            st.markdown("#### 📋 Data Tren")
            st.dataframe(tdf.reset_index(), use_container_width=True)
            st.download_button(
                "⬇️ Download Tren (Excel)",
                df_to_excel(tdf.reset_index(), "Tren"),
                file_name="tren_pemberitaan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("Belum ada data tren. Lakukan beberapa kali scraping untuk melihat tren.")
    except Exception as e:
        st.warning(f"Error: {e}")


# ==============================================================================
# TAB 3 – MONITORING BERITA (dengan Review)
# ==============================================================================

with _t_news:
    st.subheader("📝 Monitoring & Review Berita")

    # ── Sub-tab: Daftar Berita | Form Input Manual ──
    sub1, sub2 = st.tabs(["📋 Daftar Berita", "✏️ Review / Edit Artikel"])

    # ── Sub-tab 1: Daftar Berita ──────────────────────────────────────────
    with sub1:
        flt1, flt2, flt3, flt4, flt5 = st.columns(5)
        with flt1:
            fn_kw   = st.selectbox("Keyword",     ["Semua"] + st.session_state.active_keywords, key="n_kw")
        with flt2:
            fn_tone = st.selectbox("Tone",         ["Semua"] + TONE_OPTIONS, key="n_tone")
        with flt3:
            fn_src  = st.selectbox("Sumber",       ["Semua"] + SOURCE_TYPES, key="n_src")
        with flt4:
            fn_type = st.selectbox("Tipe",         ["Semua"] + CONTENT_TYPES, key="n_type")
        with flt5:
            fn_cat  = st.selectbox("Kategori Media",["Semua"] + MEDIA_CATEGORIES, key="n_cat")

        try:
            articles_raw = db.get_articles(limit=500)
        except:
            articles_raw = []

        if articles_raw:
            adf = pd.DataFrame(articles_raw)

            # Terapkan filter
            if fn_kw   != "Semua" and "keyword"        in adf.columns: adf = adf[adf["keyword"]        == fn_kw]
            if fn_tone != "Semua" and "sentiment_label" in adf.columns: adf = adf[adf["sentiment_label"] == fn_tone]
            if fn_src  != "Semua" and "source_type"    in adf.columns: adf = adf[adf["source_type"]    == fn_src]
            if fn_type != "Semua" and "content_type"   in adf.columns: adf = adf[adf["content_type"]   == fn_type]
            if fn_cat  != "Semua" and "media_category" in adf.columns: adf = adf[adf["media_category"] == fn_cat]

            st.caption(f"Menampilkan **{len(adf)}** artikel")

            # Kolom tampilan
            show_cols = [c for c in
                         ["id","title","keyword","publisher","media_category","source_type",
                          "content_type","publish_date","sentiment_label","url"]
                         if c in adf.columns]

            st.dataframe(
                adf[show_cols],
                column_config={
                    "url":             st.column_config.LinkColumn("Link"),
                    "sentiment_label": st.column_config.TextColumn("Tone"),
                    "id":              st.column_config.NumberColumn("ID", width="small"),
                },
                use_container_width=True,
                height=420,
            )

            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.download_button(
                    "⬇️ CSV", adf.to_csv(index=False).encode(),
                    f"berita_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv",
                )
            with dc2:
                st.download_button(
                    "⬇️ Excel",
                    df_to_excel(adf, "Daftar Berita"),
                    f"berita_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.info("Belum ada data.")

    # ── Sub-tab 2: Review / Edit Artikel ─────────────────────────────────
    with sub2:
        if not can_edit(_role):
            st.warning("⚠️ Hanya Level 2 (Kabid/Staf) atau Super User yang dapat melakukan review artikel.")
        else:
            st.markdown("Pilih ID artikel untuk diisi / diperbaiki data kategori, sumber, tone, dan upload bukti.")

            try:
                rev_arts = db.get_articles(limit=200)
            except:
                rev_arts = []

            if not rev_arts:
                st.info("Belum ada artikel.")
            else:
                rev_df  = pd.DataFrame(rev_arts)
                id_list = rev_df["id"].tolist() if "id" in rev_df.columns else []

                sel_id = st.selectbox(
                    "Pilih ID Artikel",
                    options=id_list,
                    format_func=lambda i: (
                        rev_df[rev_df["id"] == i]["title"].values[0][:80] + "…"
                        if "title" in rev_df.columns else str(i)
                    ),
                    key="rev_sel_id",
                )

                if sel_id:
                    art_row = rev_df[rev_df["id"] == sel_id].iloc[0] if len(rev_df[rev_df["id"] == sel_id]) else None
                    if art_row is not None:
                        st.markdown(f"**Judul:** {art_row.get('title', '-')}")
                        st.markdown(f"**Publisher:** {art_row.get('publisher', '-')}")
                        if art_row.get("url"):
                            st.markdown(f"[🔗 Buka Link Berita]({art_row['url']})")

                        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

                        re1, re2 = st.columns(2)
                        with re1:
                            cur_tone = art_row.get("sentiment_label", "Neutral")
                            idx_tone = TONE_OPTIONS.index(cur_tone) if cur_tone in TONE_OPTIONS else 2
                            new_tone = st.selectbox("Tone Berita", TONE_OPTIONS,
                                                    index=idx_tone, key="rev_tone")

                            cur_cat = art_row.get("media_category", MEDIA_CATEGORIES[8])
                            idx_cat = MEDIA_CATEGORIES.index(cur_cat) if cur_cat in MEDIA_CATEGORIES else 0
                            new_cat = st.selectbox("Kategori Media (Tier)", MEDIA_CATEGORIES,
                                                   index=idx_cat, key="rev_cat")

                        with re2:
                            cur_src = art_row.get("source_type", "Eksternal")
                            idx_src = SOURCE_TYPES.index(cur_src) if cur_src in SOURCE_TYPES else 0
                            new_src = st.selectbox("Sumber", SOURCE_TYPES,
                                                   index=idx_src, key="rev_src")

                            cur_ctype = art_row.get("content_type", "Berita / Artikel")
                            idx_ctype = CONTENT_TYPES.index(cur_ctype) if cur_ctype in CONTENT_TYPES else 0
                            new_ctype = st.selectbox("Tipe Konten", CONTENT_TYPES,
                                                     index=idx_ctype, key="rev_ctype")

                        # Upload bukti (opsional)
                        st.markdown("**Upload Bukti Pemberitaan** (opsional, PDF/PNG/JPG)")
                        uploaded_file = st.file_uploader(
                            "Pilih file", type=["pdf", "png", "jpg", "jpeg"],
                            key=f"upload_{sel_id}",
                        )

                        if st.button("✅ Submit Review", key="rev_submit"):
                            ok1 = db_update_article_tone(sel_id, new_tone)
                            ok2 = db_update_article_meta(sel_id, new_cat, new_src, new_ctype)
                            if uploaded_file:
                                file_bytes = uploaded_file.read()
                                db_save_attachment(sel_id, uploaded_file.name, file_bytes)
                            if ok1 or ok2:
                                st.success(f"✅ Artikel ID {sel_id} berhasil diperbarui.")
                            else:
                                # Jika fungsi db baru belum ada, beri petunjuk
                                st.warning(
                                    "⚠️ Fungsi `update_article_tone` dan `update_article_meta` "
                                    "belum ada di db.py. Tambahkan dari file **db_tambahan.py**."
                                )


# ==============================================================================
# TAB 4 – PENGATURAN TONE
# ==============================================================================

with _t_tone:
    st.subheader("⚙️ Pengaturan Tone Berita")

    if not can_edit(_role):
        st.warning("Hanya Level 2 (Kabid/Staf) dan Super User yang dapat mengubah pengaturan tone.")
    else:
        st.markdown(
            "Kelola keyword yang digunakan untuk menentukan tone berita secara otomatis. "
            "Keyword ini digunakan **bersama** model NLP; keyword yang lebih spesifik "
            "akan diprioritaskan."
        )

        tone_kw_current = load_tone_keywords()

        for tone_type in ["Positive", "Negative", "Neutral"]:
            color = TONE_COLORS[tone_type]
            st.markdown(
                f"<h4 style='color:{color}'>{'✅' if tone_type=='Positive' else '❌' if tone_type=='Negative' else '➖'} "
                f"Keyword {tone_type}</h4>",
                unsafe_allow_html=True,
            )
            words = tone_kw_current.get(tone_type, [])

            # Tampilkan keyword sebagai tag
            if words:
                tags_html = "".join(
                    f'<span style="background:{color}22; color:{color}; border:1px solid {color}55; '
                    f'padding:3px 10px; border-radius:12px; margin:3px; font-size:13px; display:inline-block;">'
                    f'{w}</span>'
                    for w in words
                )
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Belum ada keyword.")

            ta1, ta2 = st.columns([3, 1])
            with ta1:
                add_word = st.text_input(
                    f"Tambah keyword {tone_type}", placeholder="e.g. penghargaan",
                    key=f"add_{tone_type}",
                )
            with ta2:
                del_word = st.selectbox(
                    f"Hapus keyword", ["— pilih —"] + words,
                    key=f"del_{tone_type}",
                )

            ka1, ka2 = st.columns(2)
            with ka1:
                if st.button(f"➕ Tambah ke {tone_type}", key=f"btn_add_{tone_type}"):
                    if add_word.strip():
                        result = db_add_tone_kw(add_word.strip().lower(), tone_type)
                        if result:
                            st.success(f"'{add_word.strip()}' ditambahkan ke {tone_type}.")
                            st.rerun()
                        else:
                            st.warning(
                                "Fungsi `add_tone_keyword` belum ada di db.py. "
                                "Tambahkan dari file **db_tambahan.py**."
                            )
            with ka2:
                if st.button(f"🗑️ Hapus dari {tone_type}", key=f"btn_del_{tone_type}"):
                    if del_word != "— pilih —":
                        rows = db_get_tone_kw()
                        kw_id = next(
                            (r["id"] for r in rows
                             if r["word"] == del_word and r["tone_type"] == tone_type), None
                        )
                        if kw_id:
                            db_del_tone_kw(kw_id)
                            st.success(f"'{del_word}' dihapus dari {tone_type}.")
                            st.rerun()
                        else:
                            st.warning("Keyword tidak ditemukan di database. Mungkin masih menggunakan default.")

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # Reset ke default BRS
        if st.button("🔄 Reset ke Default BRS"):
            for tone_type, words in DEFAULT_TONE_KEYWORDS.items():
                for w in words:
                    db_add_tone_kw(w, tone_type)
            st.success("Keyword tone direset ke default BRS.")
            st.rerun()


# ==============================================================================
# TAB 5 – LAPORAN
# ==============================================================================

with _t_rept:
    st.subheader("📄 Laporan Periodik")
    st.markdown(
        "Generate laporan komprehensif pemberitaan PT ASABRI dalam bentuk tabel rekap "
        "dan grafik, tersedia untuk periode triwulan, semester, dan tahunan."
    )

    rp1, rp2, rp3 = st.columns(3)
    with rp1:
        rpt_period = st.selectbox("Periode Laporan", list(REPORT_PERIODS.keys()))
    with rp2:
        rpt_year = st.number_input("Tahun", min_value=2020,
                                   max_value=datetime.now().year,
                                   value=datetime.now().year, key="rpt_yr")
    with rp3:
        rpt_kw = st.selectbox("Keyword", ["Semua"] + st.session_state.active_keywords, key="rpt_kw")

    if st.button("📊 Generate Laporan"):
        selected_months = REPORT_PERIODS[rpt_period]

        try:
            all_raw = db.get_articles(limit=5000)
        except:
            all_raw = []

        if all_raw:
            rdf = pd.DataFrame(all_raw)
            if "publish_date" in rdf.columns:
                rdf["publish_date"] = pd.to_datetime(rdf["publish_date"], errors="coerce")
                rdf["year"]  = rdf["publish_date"].dt.year
                rdf["month"] = rdf["publish_date"].dt.month

            # Filter tahun + bulan + keyword
            rdf = rdf[rdf["year"] == rpt_year] if "year" in rdf.columns else rdf
            if "month" in rdf.columns:
                rdf = rdf[rdf["month"].isin(selected_months)]
            if rpt_kw != "Semua" and "keyword" in rdf.columns:
                rdf = rdf[rdf["keyword"] == rpt_kw]

            if rdf.empty:
                st.warning(f"Tidak ada data untuk periode **{rpt_period} {rpt_year}**.")
            else:
                st.success(f"✅ Ditemukan **{len(rdf)}** artikel untuk {rpt_period} {rpt_year}")

                # ── Ringkasan ──────────────────────────────────────────────
                st.markdown(f"### Laporan {rpt_period} {rpt_year}")
                if rpt_kw != "Semua":
                    st.caption(f"Keyword: {rpt_kw}")

                s1, s2, s3, s4 = st.columns(4)
                _rp_tot = len(rdf)
                _rp_pos = (rdf["sentiment_label"] == "Positive").sum() if "sentiment_label" in rdf.columns else 0
                _rp_neg = (rdf["sentiment_label"] == "Negative").sum() if "sentiment_label" in rdf.columns else 0
                _rp_neu = _rp_tot - _rp_pos - _rp_neg
                with s1: st.metric("Total", _rp_tot)
                with s2: st.metric("Positif", int(_rp_pos))
                with s3: st.metric("Negatif", int(_rp_neg))
                with s4: st.metric("Netral",  int(_rp_neu))

                # ── Tabel rekap per bulan ──────────────────────────────────
                st.markdown("#### 📋 Rekap per Bulan")
                if "month" in rdf.columns:
                    recap_rpt = rdf.groupby("month").apply(
                        lambda g: pd.Series({
                            "Positif": int((g["sentiment_label"] == "Positive").sum()) if "sentiment_label" in g else 0,
                            "Negatif": int((g["sentiment_label"] == "Negative").sum()) if "sentiment_label" in g else 0,
                            "Netral":  int((g["sentiment_label"] == "Neutral").sum())  if "sentiment_label" in g else 0,
                            "Total":   len(g),
                        })
                    ).reset_index()
                    recap_rpt["Bulan"] = recap_rpt["month"].apply(lambda m: MONTH_NAMES[m-1])
                    recap_rpt = recap_rpt[["Bulan","Positif","Negatif","Netral","Total"]]
                    st.dataframe(recap_rpt, use_container_width=True, hide_index=True)

                # ── Grafik batang laporan ──────────────────────────────────
                st.markdown("#### 📊 Grafik Pemberitaan Periode Ini")
                if "month" in rdf.columns and not rdf.empty:
                    mo = (
                        rdf.groupby(["month", "sentiment_label"])
                        .size().unstack(fill_value=0)
                        .reindex(selected_months, fill_value=0)
                    )
                    for cc in ["Positive","Negative","Neutral"]:
                        if cc not in mo.columns: mo[cc] = 0

                    fig_rpt, axr = plt.subplots(figsize=(10, 4), facecolor=BG_COLOR)
                    axr.set_facecolor(CARD_COLOR)
                    xr = np.arange(len(selected_months)); wr = 0.27
                    axr.bar(xr-wr, mo["Positive"], wr, color="#22c55e", label="Positif")
                    axr.bar(xr,    mo["Neutral"],  wr, color="#64748b", label="Netral")
                    axr.bar(xr+wr, mo["Negative"], wr, color="#ef4444", label="Negatif")
                    axr.set_xticks(xr)
                    axr.set_xticklabels([MONTH_NAMES[m-1] for m in selected_months], color="#cbd5e1")
                    axr.tick_params(colors="#cbd5e1")
                    axr.spines[["top","right","left","bottom"]].set_color("#334155")
                    axr.set_title(
                        f"Pemberitaan {rpt_period} {rpt_year}",
                        color="#cbd5e1", fontsize=12
                    )
                    axr.legend(labelcolor="#cbd5e1", facecolor=CARD_COLOR, edgecolor="#334155")
                    fig_rpt.tight_layout()
                    st.pyplot(fig_rpt)

                    # ── Export ──────────────────────────────────────────────
                    st.markdown("#### ⬇️ Download Laporan")
                    dl1, dl2, dl3 = st.columns(3)

                    # Excel
                    with dl1:
                        show_cols_rpt = [c for c in
                                         ["title","keyword","publisher","media_category",
                                          "source_type","content_type","publish_date","sentiment_label","url"]
                                         if c in rdf.columns]
                        excel_rpt = df_to_excel(rdf[show_cols_rpt], "Laporan")
                        st.download_button(
                            "📊 Download Excel",
                            excel_rpt,
                            file_name=f"laporan_{rpt_year}_{rpt_period.split()[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )

                    # PNG grafik
                    with dl2:
                        st.download_button(
                            "🖼️ Download Grafik (PNG)",
                            fig_to_png(fig_rpt),
                            file_name=f"grafik_{rpt_year}_{rpt_period.split()[0]}.png",
                            mime="image/png",
                        )

                    # PDF laporan (multi-page dengan matplotlib)
                    with dl3:
                        pdf_buf = io.BytesIO()
                        with PdfPages(pdf_buf) as pdf_pages:
                            # Halaman 1 – ringkasan
                            fig_s, ax_s = plt.subplots(figsize=(11.69, 8.27), facecolor="white")
                            ax_s.axis("off")
                            summary_text = (
                                f"LAPORAN MEDIA MONITORING – PT ASABRI (Persero)\n\n"
                                f"Periode : {rpt_period}\n"
                                f"Tahun   : {rpt_year}\n"
                                f"Keyword : {rpt_kw}\n\n"
                                f"RINGKASAN\n"
                                f"{'─'*45}\n"
                                f"Total Pemberitaan : {_rp_tot}\n"
                                f"Positif           : {_rp_pos}  ({_rp_pos/_rp_tot*100:.1f}%)\n"
                                f"Negatif           : {_rp_neg}  ({_rp_neg/_rp_tot*100:.1f}%)\n"
                                f"Netral            : {_rp_neu}  ({_rp_neu/_rp_tot*100:.1f}%)\n\n"
                                f"Dibuat: {datetime.now().strftime('%d %B %Y %H:%M')} WIB\n"
                                f"Bidang Komunikasi dan Protokoler"
                            )
                            ax_s.text(0.05, 0.95, summary_text,
                                      transform=ax_s.transAxes,
                                      fontsize=13, verticalalignment="top",
                                      fontfamily="monospace",
                                      bbox=dict(boxstyle="round", facecolor="#f0f4ff", alpha=0.6))
                            pdf_pages.savefig(fig_s, bbox_inches="tight")
                            plt.close(fig_s)

                            # Halaman 2 – grafik batang
                            pdf_pages.savefig(fig_rpt, bbox_inches="tight")

                            # Halaman 3 – tabel artikel
                            if "month" in rdf.columns and not recap_rpt.empty:
                                fig_t, ax_t = plt.subplots(figsize=(11.69, 3), facecolor="white")
                                ax_t.axis("off")
                                tbl_data  = recap_rpt.values.tolist()
                                tbl_cols  = recap_rpt.columns.tolist()
                                tbl = ax_t.table(
                                    cellText=tbl_data, colLabels=tbl_cols,
                                    cellLoc="center", loc="center",
                                )
                                tbl.auto_set_font_size(False)
                                tbl.set_fontsize(11)
                                tbl.scale(1, 1.6)
                                ax_t.set_title("Rekap Pemberitaan per Bulan",
                                               fontsize=13, pad=12)
                                pdf_pages.savefig(fig_t, bbox_inches="tight")
                                plt.close(fig_t)

                        pdf_bytes = pdf_buf.getvalue()
                        st.download_button(
                            "📄 Download PDF",
                            pdf_bytes,
                            file_name=f"laporan_{rpt_year}_{rpt_period.split()[0]}.pdf",
                            mime="application/pdf",
                        )
        else:
            st.warning("Belum ada data artikel di database.")


# ==============================================================================
# TAB 6 – LOGS
# ==============================================================================

with _t_logs:
    st.subheader("🖥️ Terminal Logs")
    st.code(
        st.session_state.terminal_logs if st.session_state.terminal_logs else "# Belum ada log. Jalankan scraping terlebih dahulu.",
        language="bash",
    )
    if st.session_state.terminal_logs and st.button("🗑️ Bersihkan Log"):
        st.session_state.terminal_logs = ""
        st.rerun()


# ==============================================================================
# TAB 7 – MANAJEMEN USER (Super User only)
# ==============================================================================

if _t_user is not None:
    with _t_user:
        st.subheader("👥 Manajemen User")
        st.markdown("Tambah, lihat, dan hapus akun pengguna MONITOR.")

        # ── Tabel user yang ada ──────────────────────────────────────────
        users_list = db_get_users()
        if users_list:
            udf = pd.DataFrame(users_list)
            show_ucols = [c for c in ["id","username","full_name","role"] if c in udf.columns]
            if "role" in udf.columns:
                udf["role_label"] = udf["role"].apply(lambda r: ROLES.get(r, r))
                show_ucols = [c for c in ["id","username","full_name","role_label"] if c in udf.columns]
            st.dataframe(udf[show_ucols], use_container_width=True, hide_index=True)
        else:
            st.info(
                "Belum ada data user, atau fungsi `get_users` belum ditambahkan ke db.py. "
                "Lihat file **db_tambahan.py**."
            )

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # ── Form tambah user ─────────────────────────────────────────────
        st.markdown("#### ➕ Tambah User Baru")
        with st.form("add_user_form"):
            ua1, ua2 = st.columns(2)
            with ua1:
                new_uname = st.text_input("Username", placeholder="e.g. kartika.r")
                new_fname = st.text_input("Nama Lengkap", placeholder="e.g. Kartika Rahmadayanti")
            with ua2:
                new_pw    = st.text_input("Password", type="password")
                new_role  = st.selectbox("Role", list(ROLES.keys()),
                                         format_func=lambda r: ROLES[r])
            if st.form_submit_button("💾 Tambah User"):
                if new_uname and new_pw and new_fname:
                    uid = db_add_user(new_uname, hash_pw(new_pw), new_role, new_fname)
                    if uid:
                        st.success(f"✅ User **{new_uname}** berhasil ditambahkan.")
                        st.rerun()
                    else:
                        st.warning(
                            "Fungsi `add_user` belum ada di db.py. "
                            "Tambahkan dari file **db_tambahan.py**."
                        )
                else:
                    st.warning("Isi semua field terlebih dahulu.")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        # ── Hapus user ───────────────────────────────────────────────────
        st.markdown("#### 🗑️ Hapus User")
        if users_list:
            del_opts = {u["id"]: f"{u.get('full_name','?')} ({u.get('username','?')})"
                        for u in users_list if u.get("username") != "admin"}
            if del_opts:
                del_uid = st.selectbox(
                    "Pilih User", list(del_opts.keys()),
                    format_func=lambda i: del_opts[i],
                )
                if st.button("🗑️ Hapus User ini", key="del_user_btn"):
                    ok = db_delete_user(del_uid)
                    if ok:
                        st.success("User berhasil dihapus.")
                        st.rerun()
                    else:
                        st.warning("Gagal menghapus user atau fungsi belum tersedia di db.py.")
            else:
                st.info("Tidak ada user lain yang dapat dihapus (selain admin).")
