# 🪐 Orbit Downloader API

A blazing-fast, lightweight backend API designed to extract high-fidelity video and audio from over 1,000+ platforms. Built with **FastAPI** and powered by the industry-standard **yt-dlp** engine.

## ✨ Core Features
* **Universal Support:** Extracts media from YouTube, Facebook, Instagram, TikTok, X (Twitter), and thousands of other sites.
* **Maximum Fidelity:** Utilizes FFmpeg to seamlessly merge separate high-definition video (1080p, 1440p, 4K) and high-bitrate audio streams without compression loss.
* **Lightning Fast:** Built on FastAPI for asynchronous, non-blocking requests, ensuring rapid fetch times and reliable performance.
* **Headless Architecture:** Completely decoupled API, ready to be connected to any modern frontend interface (React, Vue, or Vanilla JS).

## 🛠️ Tech Stack
* **Python 3.10+**
* **FastAPI** (Web Framework)
* **Uvicorn** (ASGI Server)
* **yt-dlp** (Media Extraction Engine)
* **FFmpeg** (Media Processing & Merging)

## 🚀 Deployment 
This API is designed to be easily deployed on cloud platforms like **Render**, **Railway**, or **Heroku**. 

To run this locally for development:
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure `ffmpeg` is installed and added to your system's PATH.
4. Start the server: `uvicorn main:app --host 0.0.0.0 --port 8000`

---
*Built to empower creators with unrestricted, premium tools.*
