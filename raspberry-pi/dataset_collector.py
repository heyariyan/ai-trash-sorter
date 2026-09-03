#!/usr/bin/env python3
"""Interactive Web & Physical Camera Dataset Collector for Novi AI Smart Bin.

Provides a live high-FPS web stream, one-tap mobile & keyboard hotkey capture,
burst mode, and physical button capture to rapidly collect and label training images.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, render_template_string, request, send_file
from PIL import Image

DATASET_DIR = Path("/var/lib/ai-trash-sorter/dataset")
CATEGORIES = ["BIODEGRADABLE", "PLASTIC", "METAL", "OTHER"]

for cat in CATEGORIES:
    (DATASET_DIR / cat).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

# Global camera state
camera = None
camera_lock = threading.Lock()
current_frame_bytes = None
recent_captures = []  # List of {id, path, category, timestamp}


def init_camera():
    global camera
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        config = cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
        cam.configure(config)
        cam.start()
        time.sleep(1.0)
        camera = cam
        print("Picamera2 initialized successfully!")
    except Exception as e:
        print("Camera init error:", e)


def get_latest_frame():
    global camera, current_frame_bytes
    if camera is None:
        return None
    try:
        arr = camera.capture_array("main")
        img = Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        current_frame_bytes = buf.getvalue()
        return current_frame_bytes
    except Exception:
        return None


def generate_mjpeg():
    while True:
        frame = get_latest_frame()
        if frame is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
        time.sleep(0.04)  # ~25 FPS


def save_single_photo(category: str) -> dict | None:
    global camera, recent_captures
    if category not in CATEGORIES or camera is None:
        return None
    try:
        arr = camera.capture_array("main")
        img = Image.fromarray(arr)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")[:19]
        uid = str(uuid.uuid4())[:8]
        filename = f"{category}_{stamp}_{uid}.jpg"
        target_path = DATASET_DIR / category / filename
        img.save(str(target_path), "JPEG", quality=90)
        
        info = {
            "id": uid,
            "filename": filename,
            "category": category,
            "path": str(target_path),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        recent_captures.insert(0, info)
        if len(recent_captures) > 20:
            recent_captures.pop()
        return info
    except Exception as e:
        print(f"Error capturing for {category}:", e)
        return None


def get_category_counts() -> dict[str, int]:
    counts = {}
    total = 0
    for cat in CATEGORIES:
        c = len(list((DATASET_DIR / cat).glob("*.jpg")))
        counts[cat] = c
        total += c
    counts["TOTAL"] = total
    return counts


# ── Physical 4-Button Listener Thread ──
def button_listener():
    try:
        import lgpio
        h = lgpio.gpiochip_open(0)
        btn_map = {20: "BIODEGRADABLE", 21: "PLASTIC", 16: "METAL", 12: "OTHER"}
        for pin in btn_map:
            try:
                lgpio.gpio_claim_input(h, pin, lgpio.SET_PULL_DOWN)
            except Exception:
                lgpio.gpio_claim_input(h, pin)

        print("Physical button collector active: YES(20)=BIO, NO(21)=PLASTIC, PREV(16)=METAL, NEXT(12)=OTHER")
        while True:
            for pin, cat in btn_map.items():
                if int(lgpio.gpio_read(h, pin)) == 1:
                    time.sleep(0.03)
                    if int(lgpio.gpio_read(h, pin)) == 1:
                        print(f"[PHYSICAL BUTTON] Captured {cat}!")
                        save_single_photo(cat)
                        while int(lgpio.gpio_read(h, pin)) == 1:
                            time.sleep(0.05)
            time.sleep(0.03)
    except Exception as e:
        print("Physical button listener disabled:", e)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Novi AI - Live Dataset Collector</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --bio: #10b981;
      --plastic: #3b82f6;
      --metal: #f59e0b;
      --other: #a855f7;
      --text: #f8fafc;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px;
    }
    header {
      width: 100%;
      max-width: 760px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    h1 { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
    .badge {
      background: #059669;
      color: white;
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 99px;
      font-weight: bold;
    }
    .main-container {
      width: 100%;
      max-width: 760px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .video-wrapper {
      position: relative;
      background: #000;
      border-radius: 16px;
      overflow: hidden;
      aspect-ratio: 4/3;
      border: 2px solid var(--border);
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .video-wrapper img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .video-overlay {
      position: absolute;
      top: 12px;
      left: 12px;
      background: rgba(0,0,0,0.65);
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      backdrop-filter: blur(4px);
    }
    .flash-overlay {
      position: absolute;
      inset: 0;
      background: white;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.08s ease-out;
    }
    .counts-bar {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
      background: var(--card);
      padding: 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }
    .count-item {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .count-val { font-size: 18px; font-weight: 800; }
    .count-lbl { font-size: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
    .btn-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }
    @media (min-width: 600px) {
      .btn-grid { grid-template-columns: repeat(4, 1fr); }
    }
    .cat-btn {
      padding: 20px 12px;
      border-radius: 14px;
      border: none;
      font-size: 16px;
      font-weight: 800;
      color: white;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      transition: all 0.1s ease;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .cat-btn:active { transform: scale(0.96); }
    .btn-bio { background: linear-gradient(135deg, #10b981, #059669); }
    .btn-plastic { background: linear-gradient(135deg, #3b82f6, #2563eb); }
    .btn-metal { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .btn-other { background: linear-gradient(135deg, #a855f7, #9333ea); }
    .hotkey {
      font-size: 11px;
      opacity: 0.85;
      background: rgba(0,0,0,0.25);
      padding: 2px 8px;
      border-radius: 6px;
    }
    .burst-bar {
      display: flex;
      gap: 12px;
    }
    .burst-btn {
      flex: 1;
      padding: 12px;
      background: #334155;
      color: white;
      border: 1px solid #475569;
      border-radius: 10px;
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      transition: background 0.15s;
    }
    .burst-btn:hover { background: #475569; }
    .recent-section {
      background: var(--card);
      padding: 16px;
      border-radius: 14px;
      border: 1px solid var(--border);
    }
    .recent-header {
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
    }
    .recent-list {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 8px;
    }
    .recent-thumb {
      flex-shrink: 0;
      width: 70px;
      height: 70px;
      border-radius: 8px;
      overflow: hidden;
      border: 2px solid var(--border);
      position: relative;
    }
    .recent-thumb img { width: 100%; height: 100%; object-fit: cover; }
    .recent-cat {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      font-size: 8px;
      font-weight: bold;
      text-align: center;
      padding: 1px;
      color: white;
      background: rgba(0,0,0,0.7);
    }
    .zip-btn {
      width: 100%;
      padding: 14px;
      background: #0ea5e9;
      color: white;
      border: none;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 800;
      cursor: pointer;
      text-align: center;
      text-decoration: none;
      display: block;
      margin-top: 8px;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>📸 Novi AI Dataset Collector</h1>
      <p style="font-size: 12px; color: #94a3b8;">Place trash in tray & tap category button</p>
    </div>
    <span class="badge">LIVE STREAM</span>
  </header>

  <div class="main-container">
    <!-- Camera Viewport -->
    <div class="video-wrapper">
      <img src="/video_feed" alt="Live Camera Stream" id="stream-img">
      <div class="video-overlay" id="status-overlay">● Camera Active (640x480)</div>
      <div class="flash-overlay" id="flash"></div>
    </div>

    <!-- Category Counters -->
    <div class="counts-bar">
      <div class="count-item" style="color: var(--bio)">
        <span class="count-val" id="cnt-bio">0</span>
        <span class="count-lbl">Bio</span>
      </div>
      <div class="count-item" style="color: var(--plastic)">
        <span class="count-val" id="cnt-plastic">0</span>
        <span class="count-lbl">Plastic</span>
      </div>
      <div class="count-item" style="color: var(--metal)">
        <span class="count-val" id="cnt-metal">0</span>
        <span class="count-lbl">Metal</span>
      </div>
      <div class="count-item" style="color: var(--other)">
        <span class="count-val" id="cnt-other">0</span>
        <span class="count-lbl">Other</span>
      </div>
      <div class="count-item" style="color: #f8fafc">
        <span class="count-val" id="cnt-total">0</span>
        <span class="count-lbl">Total</span>
      </div>
    </div>

    <!-- Category Action Buttons -->
    <div class="btn-grid">
      <button class="cat-btn btn-bio" onclick="capture('BIODEGRADABLE')">
        <span>🌱 BIODEGRADABLE</span>
        <span class="hotkey">Press [ 1 ]</span>
      </button>
      <button class="cat-btn btn-plastic" onclick="capture('PLASTIC')">
        <span>🧴 PLASTIC</span>
        <span class="hotkey">Press [ 2 ]</span>
      </button>
      <button class="cat-btn btn-metal" onclick="capture('METAL')">
        <span>🥫 METAL</span>
        <span class="hotkey">Press [ 3 ]</span>
      </button>
      <button class="cat-btn btn-other" onclick="capture('OTHER')">
        <span>📦 OTHER</span>
        <span class="hotkey">Press [ 4 ]</span>
      </button>
    </div>

    <!-- Burst Capture Bar -->
    <div class="burst-bar">
      <button class="burst-btn" onclick="startBurst(5)">⚡ Burst 5x (Hold object & rotate)</button>
      <button class="burst-btn" onclick="startBurst(10)">⚡ Burst 10x (Multi-angle)</button>
    </div>

    <!-- Recent Captures Filmstrip -->
    <div class="recent-section">
      <div class="recent-header">
        <span>Recent Captures</span>
        <span style="font-size: 11px; color: #94a3b8;">Physical buttons on Pi also work!</span>
      </div>
      <div class="recent-list" id="recent-list">
        <p style="font-size: 12px; color: #64748b;">No captures yet in this session.</p>
      </div>
    </div>

    <!-- Download Dataset -->
    <a href="/download_dataset" class="zip-btn">📦 Download Dataset as ZIP (.zip)</a>
  </div>

  <script>
    let selectedBurstCategory = 'PLASTIC';

    function flash() {
      const el = document.getElementById('flash');
      el.style.opacity = '0.7';
      setTimeout(() => el.style.opacity = '0', 80);
    }

    async function capture(category) {
      flash();
      try {
        const res = await fetch('/capture', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ category })
        });
        const data = await res.json();
        updateCounts(data.counts);
        renderRecent(data.recent);
      } catch (err) {
        console.error(err);
      }
    }

    async function startBurst(count) {
      const cat = prompt("Which category for burst capture? (BIODEGRADABLE, PLASTIC, METAL, OTHER)", "PLASTIC");
      if (!cat) return;
      const valid = cat.trim().toUpperCase();
      for (let i = 0; i < count; i++) {
        await capture(valid);
        await new Promise(r => setTimeout(r, 220));
      }
    }

    function updateCounts(c) {
      if (!c) return;
      document.getElementById('cnt-bio').textContent = c.BIODEGRADABLE || 0;
      document.getElementById('cnt-plastic').textContent = c.PLASTIC || 0;
      document.getElementById('cnt-metal').textContent = c.METAL || 0;
      document.getElementById('cnt-other').textContent = c.OTHER || 0;
      document.getElementById('cnt-total').textContent = c.TOTAL || 0;
    }

    function renderRecent(items) {
      if (!items || items.length === 0) return;
      const container = document.getElementById('recent-list');
      container.innerHTML = items.map(item => `
        <div class="recent-thumb">
          <img src="/image/${encodeURIComponent(item.category)}/${encodeURIComponent(item.filename)}" alt="${item.category}">
          <span class="recent-cat">${item.category.slice(0,4)}</span>
        </div>
      `).join('');
    }

    // Hotkeys 1, 2, 3, 4
    window.addEventListener('keydown', (e) => {
      if (e.key === '1') capture('BIODEGRADABLE');
      if (e.key === '2') capture('PLASTIC');
      if (e.key === '3') capture('METAL');
      if (e.key === '4') capture('OTHER');
    });

    // Initial counts poll
    fetch('/counts').then(r => r.json()).then(updateCounts);
    setInterval(() => {
      fetch('/counts').then(r => r.json()).then(updateCounts);
    }, 2000);
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/video_feed")
def video_feed():
    return Response(generate_mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/capture", methods=["POST"])
def handle_capture():
    data = request.get_json() or {}
    category = str(data.get("category", "")).upper()
    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400
    res = save_single_photo(category)
    return jsonify({
        "success": res is not None,
        "captured": res,
        "counts": get_category_counts(),
        "recent": recent_captures,
    })


@app.route("/counts")
def counts():
    return jsonify(get_category_counts())


@app.route("/image/<category>/<filename>")
def serve_image(category, filename):
    path = DATASET_DIR / category / filename
    if path.exists():
        return send_file(str(path), mimetype="image/jpeg")
    return "Not found", 404


@app.route("/download_dataset")
def download_dataset():
    zip_path = Path("/tmp/novi_dataset.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for cat in CATEGORIES:
            cat_dir = DATASET_DIR / cat
            for file in cat_dir.glob("*.jpg"):
                zipf.write(file, arcname=f"{cat}/{file.name}")
    return send_file(str(zip_path), as_attachment=True, download_name="novi_dataset.zip")


if __name__ == "__main__":
    init_camera()
    # Start physical button thread
    t = threading.Thread(target=button_listener, daemon=True)
    t.start()
    
    print("\n" + "=" * 60)
    print(" 📸 NOVI AI DATASET COLLECTOR IS RUNNING!")
    print(" Open in browser on your phone or PC:")
    print(" 👉 http://Ariyan.local:8080")
    print("=" * 60 + "\n")
    
    app.run(host="0.0.0.0", port=8080, threaded=True)
