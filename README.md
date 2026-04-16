# KhomDev Brand Monitor: Reputation & Strategy

<div align="center">
  <img src="icon.png" width="150" alt="KhomDev Brand Monitor Icon" />
</div>
**BrandMonitor** is a state-of-the-art, AI-powered brand intelligence tool designed for business owners and PR professionals. It aggregates sentiment from across the web (Google Reviews, News, Social Media) and uses **Google Gemini 1.5 Flash** to generate deep strategic insights and actionable marketing roadmaps.

![Screenshot 1](screenshots/Screenshot%202026-04-16%20at%2020.53.39.png)
![Screenshot 2](screenshots/Screenshot%202026-04-16%20at%2020.54.20.png)
![Screenshot 3](screenshots/Screenshot%202026-04-16%20at%2020.54.32.png)

## 🚀 Key Features

- **Multi-Platform Scraping**: Real-time extraction from Google Reviews, News snippets, and (simulated) social media using Playwright.
- **AI Sentiment Analysis**: Deep learning analysis with weighted scoring for every platform.
- **Competitor Benchmarking**: Direct comparison against rivals to identify threats and advantages.
- **Actionable Roadmap**: AI-generated To-Do lists categorized by PR, Social, and Product development.
- **Premium UX**: A clinical, dark-themed dashboard featuring glassmorphism, smooth animations, and interactive Chart.js gauges.
- **Demo Mode**: Full UI functionality even without an API key, perfect for demonstrations and portfolio reviews.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Analysis**: Google Gemini 1.5 Flash (via `google-generativeai`)
- **Web Automation**: Playwright (Headless Chromium)
- **Logging/Config**: Loguru, Pydantic Settings
- **Frontend**: HTML5, Vanilla JS (ES6+), CSS3 (Advanced HSL Palettes)
- **Visualization**: Chart.js

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/KhomenkovDev/khomdev_brand_monitor.git
cd brand-monitor
```

### 2. Environment Setup
Create a `.env` file based on `.env.example`:
```env
GEMINI_API_KEY=your_genai_key_here
LOG_LEVEL=INFO
HEADLESS=True
DEMO_MODE=False
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Run with Uvicorn
```bash
python main.py
```
Access the app at `http://localhost:8000`.

## 🐳 Docker Support
Easily deploy using Dockerized environments:
```bash
docker-compose up --build
```

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Created for portfolio demonstration purposes.*
