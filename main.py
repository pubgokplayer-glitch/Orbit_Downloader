import os
import tempfile
import shutil
import re
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Orbit Downloader - Universal Media Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def cleanup_dir(path: str) -> None:
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

TARGET_HEIGHTS = [2160, 1440, 1080, 720, 480, 360]
QUALITY_LABELS = {
    2160: "4K (2160p)",
    1440: "1440p (2K)",
    1080: "1080p (Full HD)",
    720:  "720p (HD)",
    480:  "480p",
    360:  "360p",
}

# ---------------------------------------------------------------------------
# /api/info
# ---------------------------------------------------------------------------

@app.get("/api/info")
def get_info(url: str = Query(..., description="YouTube video URL")):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    title     = info.get("title", "Unknown Title")
    thumbnail = info.get("thumbnail", "")
    duration  = info.get("duration", 0)
    formats   = info.get("formats", [])

    available_heights: set = set()
    for fmt in formats:
        h      = fmt.get("height")
        vcodec = fmt.get("vcodec", "none")
        if h and vcodec and vcodec != "none":
            available_heights.add(int(h))

    quality_options = []
    for height in TARGET_HEIGHTS:
        if any(h >= height for h in available_heights):
            quality_options.append({
                "label":  QUALITY_LABELS.get(height, f"{height}p"),
                "height": height,
                "type":   "video",
                "ext":    "mp4",
            })

    quality_options.append({
        "label":  "Audio Only (MP3)",
        "height": 0,
        "type":   "audio",
        "ext":    "mp3",
    })

    return {
        "title":           title,
        "thumbnail":       thumbnail,
        "duration":        duration,
        "quality_options": quality_options,
    }

# ---------------------------------------------------------------------------
# /api/download
# ---------------------------------------------------------------------------

@app.get("/api/download")
def download(
    background_tasks: BackgroundTasks,
    url:        str = Query(...),
    height:     int = Query(0),
    title:      str = Query("video"),
    media_type: str = Query("video"),
):
    tmp_dir    = tempfile.mkdtemp(prefix="ytdl_")
    safe_title = sanitize_filename(title) or "download"

    if media_type == "audio" or height == 0:
        output_template = os.path.join(tmp_dir, f"{safe_title}.%(ext)s")
        ydl_opts = {
            "quiet":       True,
            "no_warnings": True,
            "format":      "bestaudio/best",
            "outtmpl":     output_template,
            "postprocessors": [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   "mp3",
                "preferredquality": "192",
            }],
        }
        dl_filename  = f"{safe_title}.mp3"
        content_type = "audio/mpeg"
    else:
        output_template = os.path.join(tmp_dir, f"{safe_title}.%(ext)s")
        fmt = (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
            f"/best"
        )
        ydl_opts = {
            "quiet":                True,
            "no_warnings":          True,
            "format":               fmt,
            "outtmpl":              output_template,
            "merge_output_format":  "mp4",
            "postprocessors": [{
                "key":             "FFmpegVideoConvertor",
                "preferedformat":  "mp4",
            }],
        }
        dl_filename  = f"{safe_title}.mp4"
        content_type = "video/mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        cleanup_dir(tmp_dir)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        cleanup_dir(tmp_dir)
        raise HTTPException(status_code=500, detail=f"Download failed: {exc}")

    output_file = None
    for candidate in Path(tmp_dir).iterdir():
        if candidate.is_file():
            output_file = candidate
            break

    if output_file is None or not output_file.exists():
        cleanup_dir(tmp_dir)
        raise HTTPException(status_code=500, detail="Output file not found after download.")

    background_tasks.add_task(cleanup_dir, tmp_dir)

    return FileResponse(
        path=str(output_file),
        media_type=content_type,
        filename=dl_filename,
        headers={"Content-Disposition": f'attachment; filename="{dl_filename}"'},
    )

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}
