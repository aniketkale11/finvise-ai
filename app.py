import streamlit as st
import yfinance as yf
import requests
import os
from groq import Groq
from video_generator import generate_video
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# ── Session state init ─────────────────────────────────────────────────────────
for key in ["stock", "news", "summary", "video_path", "analyzed"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinVise AI — Indian Stock Intelligence",
    page_icon="📈",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #2d3250;
        text-align: center;
    }
    .metric-label { color: #9ca3af; font-size: 13px; margin-bottom: 4px; }
    .metric-value { color: #f9fafb; font-size: 22px; font-weight: 700; }
    .metric-green { color: #22c55e !important; }
    .metric-red   { color: #ef4444 !important; }
    .section-box {
        background: #1e2130;
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #2d3250;
        margin-bottom: 16px;
    }
    .section-title { color: #818cf8; font-weight: 700; font-size: 13px;
                     text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .news-item { border-left: 3px solid #818cf8; padding-left: 12px;
                 margin-bottom: 12px; color: #d1d5db; font-size: 14px; }
    .news-source { color: #6b7280; font-size: 12px; margin-top: 3px; }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white; border: none; border-radius: 8px;
        padding: 10px 32px; font-weight: 600; font-size: 16px;
        width: 100%; margin-top: 8px;
    }
    .stButton > button:hover { opacity: 0.9; }
    h1 { color: #f9fafb !important; }
    .tag { display:inline-block; background:#312e81; color:#a5b4fc;
           border-radius:6px; padding:2px 10px; font-size:12px; margin-right:6px; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 📈 FinVise AI — Indian Stock Intelligence")
st.markdown("*Real-time stock data · AI summaries · Auto-generated video briefs*")
st.divider()

# ── Sidebar: API keys ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Configuration")
    groq_key   = st.text_input("Groq API Key",   type="password",
                               value=os.getenv("GROQ_API_KEY", ""),
                               help="Get free key at console.groq.com")
    gnews_key  = st.text_input("GNews API Key",  type="password",
                               value=os.getenv("GNEWS_API_KEY", ""),
                               help="Get free key at gnews.io")
    st.markdown("---")
    st.markdown("**Supported exchanges**")
    st.markdown("• NSE: add `.NS` (auto-handled)\n• BSE: add `.BO` (auto-handled)")
    st.markdown("---")
    st.markdown("**Example tickers**")
    for t in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO", "TATAMOTORS"]:
        st.markdown(f"`{t}`")

# ── Input ──────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    ticker_input = st.text_input(
        "Enter stock ticker or company name",
        placeholder="e.g. RELIANCE, TCS, INFY, HDFCBANK",
        label_visibility="collapsed"
    )
with col2:
    analyze = st.button("🔍 Analyze Stock")

# ── Helpers ────────────────────────────────────────────────────────────────────
def resolve_ticker(raw: str) -> str:
    """Ensure ticker has .NS suffix for NSE."""
    raw = raw.strip().upper()
    if "." not in raw:
        raw = raw + ".NS"
    return raw

@st.cache_data(ttl=300)
def fetch_stock(ticker: str) -> dict | None:
    import time
    errors = []

    # Try up to 3 times with delay
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(2)  # wait 2 seconds before retry

            tk   = yf.Ticker(ticker)
            hist = tk.history(period="5d", timeout=10)

            if hist.empty:
                # Try with .BO suffix if .NS fails
                if ".NS" in ticker:
                    alt = ticker.replace(".NS", ".BO")
                    tk   = yf.Ticker(alt)
                    hist = tk.history(period="5d", timeout=10)
                if hist.empty:
                    errors.append("No data returned")
                    continue

            info = tk.fast_info  # faster than tk.info, less rate limiting

            latest = hist.iloc[-1]
            prev   = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]
            change     = latest["Close"] - prev["Close"]
            change_pct = (change / prev["Close"]) * 100

            # fast_info uses different attribute names
            try:
                name     = tk.info.get("longName", ticker)
                sector   = tk.info.get("sector", "N/A")
                mkt_cap  = tk.info.get("marketCap", "N/A")
                w52_high = tk.info.get("fiftyTwoWeekHigh", "N/A")
                w52_low  = tk.info.get("fiftyTwoWeekLow",  "N/A")
            except Exception:
                name     = ticker.replace(".NS", "").replace(".BO", "")
                sector   = "N/A"
                mkt_cap  = "N/A"
                w52_high = round(hist["High"].max(), 2)
                w52_low  = round(hist["Low"].min(),  2)

            return {
                "name":        name,
                "symbol":      ticker,
                "price":       round(latest["Close"], 2),
                "open":        round(latest["Open"],  2),
                "high":        round(latest["High"],  2),
                "low":         round(latest["Low"],   2),
                "volume":      int(latest["Volume"]),
                "change":      round(change, 2),
                "change_pct":  round(change_pct, 2),
                "week52_high": w52_high,
                "week52_low":  w52_low,
                "sector":      sector,
                "market_cap":  mkt_cap,
            }

        except Exception as e:
            errors.append(str(e))
            continue

    st.error(f"Could not fetch stock data after 3 attempts. Please try again in a minute.\nDetails: {errors[-1]}")
    return None

@st.cache_data(ttl=300)
def fetch_news(company: str, api_key: str) -> list[dict]:
    try:
        url = (
            f"https://gnews.io/api/v4/search"
            f"?q={company}+stock&lang=en&country=in"
            f"&max=5&apikey={api_key}"
        )
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            return [{"title": a["title"], "source": a["source"]["name"],
                     "url": a["url"], "published": a["publishedAt"]}
                    for a in articles]
    except Exception:
        pass
    return []

def build_prompt(stock: dict, news: list[dict]) -> str:
    news_text = "\n".join(
        [f"- {n['title']} ({n['source']})" for n in news[:3]]
    ) or "No recent news available."

    mktcap = stock["market_cap"]
    if isinstance(mktcap, (int, float)):
        mktcap = f"₹{mktcap/1e7:.0f} Cr"

    return f"""You are a financial content writer for a YouTube channel that teaches beginners about the stock market. 
Write a 90-second video script for {stock['name']} ({stock['symbol']}) based on this data.

STOCK DATA:
- Current Price: ₹{stock['price']}
- Open: ₹{stock['open']} | High: ₹{stock['high']} | Low: ₹{stock['low']}
- Change: ₹{stock['change']} ({stock['change_pct']}%)
- Volume: {stock['volume']:,}
- 52-Week High: {stock['week52_high']} | 52-Week Low: {stock['week52_low']}
- Sector: {stock['sector']} | Market Cap: {mktcap}

RECENT NEWS:
{news_text}

Write EXACTLY in this format (include the labels):

[HOOK - 0 to 10 seconds]
(One punchy opening sentence to grab attention. Mention the company name.)

[STOCK SNAPSHOT - 10 to 30 seconds]
(Current price, today's movement up or down, how it compares to its 52-week range. Plain English, no jargon.)

[WHAT IS HAPPENING - 30 to 60 seconds]
(2 to 3 key things from the news driving this stock today. Explain each simply as if to a first-time investor.)

[BEGINNER TAKEAWAY - 60 to 80 seconds]
(What does all this mean for someone who just started investing? What should they watch for? Keep it encouraging and honest.)

[CALL TO ACTION - 80 to 90 seconds]
(A neutral educational closing. Remind them to do their own research. Keep it friendly.)

Rules: No jargon. Short sentences. Sound like a friendly human, not a robot. Total script = about 200 to 230 words."""

def generate_summary(prompt: str, api_key: str) -> str:
    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"LLM error: {e}"

def fmt_volume(v: int) -> str:
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.1f}K"
    return str(v)

# ── Main flow ──────────────────────────────────────────────────────────────────

# When Analyze is clicked — fetch everything and store in session_state
if analyze and ticker_input:
    if not groq_key:
        st.error("⚠️ Please enter your Groq API key in the sidebar.")
        st.stop()

    ticker = resolve_ticker(ticker_input)

    with st.spinner(f"Fetching data for **{ticker}**..."):
        stock = fetch_stock(ticker)

    if not stock:
        st.error(f"Could not fetch data for `{ticker}`. Try again (e.g. RELIANCE, TCS).")
        st.stop()

    news = []
    if gnews_key:
        with st.spinner("Fetching latest news..."):
            news = fetch_news(stock["name"].split()[0], gnews_key)

    with st.spinner("Generating AI video brief..."):
        prompt  = build_prompt(stock, news)
        summary = generate_summary(prompt, groq_key)

    # Save everything to session state
    st.session_state.stock    = stock
    st.session_state.news     = news
    st.session_state.summary  = summary
    st.session_state.analyzed = True
    st.session_state.video_path = None   # reset old video

elif analyze and not ticker_input:
    st.warning("Please enter a stock ticker first.")

# ── Display results (persists across button clicks) ────────────────────────────
if st.session_state.analyzed and st.session_state.stock:
    stock   = st.session_state.stock
    news    = st.session_state.news or []
    summary = st.session_state.summary

    def metric_html(label, value, cls="metric-value"):
        return f"""<div class='metric-card'>
            <div class='metric-label'>{label}</div>
            <div class='{cls}'>{value}</div>
        </div>"""

    # Stock name + tags
    st.markdown(f"### {stock['name']}")
    st.markdown(
        f"<span class='tag'>{stock['symbol']}</span>"
        f"<span class='tag'>{stock['sector']}</span>",
        unsafe_allow_html=True
    )
    st.markdown("")

    # Metrics row
    color = "metric-green" if stock["change"] >= 0 else "metric-red"
    arrow = "▲" if stock["change"] >= 0 else "▼"
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(metric_html("Current Price", f"₹{stock['price']}"), unsafe_allow_html=True)
    c2.markdown(metric_html("Change", f"{arrow} ₹{abs(stock['change'])} ({stock['change_pct']}%)", color), unsafe_allow_html=True)
    c3.markdown(metric_html("Open",   f"₹{stock['open']}"),   unsafe_allow_html=True)
    c4.markdown(metric_html("High",   f"₹{stock['high']}"),   unsafe_allow_html=True)
    c5.markdown(metric_html("Low",    f"₹{stock['low']}"),    unsafe_allow_html=True)
    c6.markdown(metric_html("Volume", fmt_volume(stock["volume"])), unsafe_allow_html=True)

    st.markdown("")
    wc1, wc2 = st.columns(2)
    wc1.markdown(metric_html("52-Week High", f"₹{stock['week52_high']}"), unsafe_allow_html=True)
    wc2.markdown(metric_html("52-Week Low",  f"₹{stock['week52_low']}"),  unsafe_allow_html=True)
    st.markdown("")

    # News + AI brief
    left, right = st.columns([1, 1])

    with left:
        st.markdown("<div class='section-box'><div class='section-title'>📰 Latest News</div>",
                    unsafe_allow_html=True)
        if news:
            for n in news[:4]:
                st.markdown(
                    f"<div class='news-item'>"
                    f"<a href='{n['url']}' target='_blank' style='color:#d1d5db;text-decoration:none;'>{n['title']}</a>"
                    f"<div class='news-source'>{n['source']} · {n['published'][:10]}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<div style='color:#6b7280'>No news found.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='section-box'><div class='section-title'>🤖 AI Video Brief Script</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div style='color:#d1d5db;font-size:14px;line-height:1.8;white-space:pre-wrap'>{summary}</div>",
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Video generation ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🎬 Generate 90-Second Video Brief")
    st.info("This will create a narrated MP4 with text slides — takes about 30 seconds.")

    if st.button("🎬 Generate Video Now"):
        with st.spinner("Generating video (this takes ~30 seconds)..."):
            video_path = generate_video(summary, stock)
        st.session_state.video_path = video_path

    # Show video if already generated
    if st.session_state.video_path and os.path.exists(st.session_state.video_path):
        st.success("✅ Video generated successfully!")
        with open(st.session_state.video_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Video (MP4)",
                data=f,
                file_name=f"{stock['symbol']}_brief.mp4",
                mime="video/mp4"
            )
        st.video(st.session_state.video_path)