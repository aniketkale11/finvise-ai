# FinVise AI — Indian Stock Intelligence Platform

> AI-powered stock market intelligence with automatic 90-second video brief generation for Indian stocks (NSE/BSE).

## Live Demo
🔗 [Add your Streamlit Cloud URL here after deployment]

## Sample Video Output
📹 [Add a link to a sample generated video here]

---

## What I Built

A production-ready Streamlit application that:
1. Accepts any NSE/BSE stock ticker or company name
2. Fetches real-time stock data (price, OHLCV, 52-week range) via `yfinance`
3. Fetches recent news headlines via GNews API
4. Uses Groq (Llama 3) to generate a structured, beginner-friendly 90-second video script
5. Auto-generates an MP4 video with TTS narration and text slides using `gTTS` + `MoviePy`

---

## Tech Stack

| Category    | Tool                       | Why                                      |
|-------------|----------------------------|------------------------------------------|
| UI          | Streamlit                  | Fast, Python-native, free cloud hosting  |
| Stock Data  | yfinance                   | Free, no API key, real NSE/BSE data      |
| News        | GNews API (free tier)      | Reliable, Indian market coverage         |
| LLM         | Groq API — Llama 3 8B      | Fastest free LLM inference available     |
| TTS         | gTTS (Google Text-to-Speech)| Fully free, no API key needed           |
| Video       | MoviePy + Pillow           | Free, no API key, full MP4 output        |
| Deployment  | Streamlit Cloud            | Free, one-click deploy from GitHub       |

---

## Local Setup (Run in VS Code)

### Step 1 — Clone / open the project
```bash
cd finvise
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your real API keys
```

### Step 5 — Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Get Free API Keys (5 minutes)

### Groq API Key (LLM — required)
1. Go to https://console.groq.com
2. Sign up with Google
3. Click "API Keys" → "Create API Key"
4. Copy the key

### GNews API Key (news — recommended)
1. Go to https://gnews.io
2. Sign up free
3. Your API key is shown on the dashboard

---

## Deploy to Streamlit Cloud (Free)

1. Push this folder to a **public GitHub repository**
2. Go to https://share.streamlit.io
3. Click "New app"
4. Select your repo → branch → `app.py`
5. Click "Advanced settings" → "Secrets" and paste:

```toml
GROQ_API_KEY = "your_groq_key_here"
GNEWS_API_KEY = "your_gnews_key_here"
```

6. Click "Deploy" — live in ~2 minutes!

---

## Features

- ✅ Real-time NSE/BSE stock data (no mock data)
- ✅ Live news headlines with source links
- ✅ AI-generated beginner-friendly video script (5 timed sections)
- ✅ Auto-generated MP4 with voiceover + text slides
- ✅ Downloadable video file
- ✅ Graceful error handling (invalid ticker, API failures, rate limits)
- ✅ Dark theme, responsive layout
- ✅ API keys via sidebar (works without .env too)

---

## What I'd Improve With More Time

- Add stock price chart (last 30 days candlestick via Plotly)
- Add Hindi language TTS option for wider Indian audience
- Cache stock + news data to reduce API calls (Streamlit `@st.cache_data`)
- Add background music to the video
- Support portfolio watchlist (multiple stocks at once)
- Add sentiment analysis on news headlines

---

## Project Structure

```
finvise/
├── app.py               # Main Streamlit application
├── video_generator.py   # gTTS + MoviePy video generation
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .streamlit/
│   ├── config.toml      # Streamlit theme config
│   └── secrets.toml.example
└── README.md
```

---

## Error Handling

| Scenario              | Behavior                                              |
|-----------------------|-------------------------------------------------------|
| Invalid ticker        | Clear error message, ask user to check ticker         |
| No GNews key          | App still works, news section shows warning           |
| LLM API failure       | Error shown, user can retry                           |
| TTS failure           | Video generated with silent slide for that section    |
| yfinance rate limit   | Retry suggestion with alternative ticker format       |

---

*Built for FinVise AI Tech Pvt Ltd Technical Assignment — 24-hour challenge*
