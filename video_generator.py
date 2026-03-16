"""
video_generator.py - No ffmpeg required, uses imageio with pip-installed ffmpeg
"""

import re
import os
import textwrap
import tempfile
import streamlit as st
from datetime import datetime


def parse_sections(script: str) -> list:
    patterns = [
        ("HOOK",               0,  10),
        ("STOCK SNAPSHOT",    10,  30),
        ("WHAT IS HAPPENING", 30,  60),
        ("BEGINNER TAKEAWAY", 60,  80),
        ("CALL TO ACTION",    80,  90),
    ]
    sections = []
    for label, t_start, t_end in patterns:
        match = re.search(
            rf"\[{re.escape(label)}.*?\](.*?)(?=\[|\Z)",
            script, re.DOTALL | re.IGNORECASE
        )
        text = match.group(1).strip() if match else "Information not available."
        sections.append({
            "label":    label.title(),
            "text":     text,
            "t_start":  t_start,
            "t_end":    t_end,
            "duration": t_end - t_start,
        })
    return sections


def load_font(size: int):
    from PIL import ImageFont
    paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_slide(section: dict, stock: dict, index: int, total: int):
    from PIL import Image, ImageDraw
    import numpy as np

    W, H    = 1280, 720
    BG      = (15,  17,  23)
    ACCENT  = (99,  102, 241)
    WHITE   = (249, 250, 251)
    GRAY    = (156, 163, 175)
    SUBGRAY = (75,  85,  99)
    GREEN   = (34,  197, 94)
    RED     = (239, 68,  68)
    CARD    = (30,  33,  48)

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([0, 0, W, 7], fill=ACCENT)

    # Progress bar
    draw.rectangle([0, H-6, W, H], fill=SUBGRAY)
    draw.rectangle([0, H-6, int(W * (index+1) / total), H], fill=ACCENT)

    # Section badge
    badge_txt = f"  {section['label'].upper()}  "
    bw = len(badge_txt) * 11
    draw.rounded_rectangle([40, 28, 40+bw, 60], radius=6, fill=ACCENT)
    draw.text((48, 35), badge_txt, font=load_font(18), fill=WHITE)

    # Timestamp
    draw.text((W-130, 36), f"{section['t_start']}s - {section['t_end']}s",
              font=load_font(16), fill=GRAY)

    # Stock card
    change    = stock.get("change", 0)
    arrow     = "+" if change >= 0 else "-"
    chg_color = GREEN if change >= 0 else RED
    draw.rounded_rectangle([40, 72, 700, 132], radius=8, fill=CARD)
    draw.text((56, 80),  stock.get("name", "")[:40], font=load_font(18), fill=GRAY)
    draw.text((56, 102), f"Rs {stock.get('price','N/A')}",
              font=load_font(26), fill=WHITE)
    draw.text((240, 108),
              f"{arrow} Rs {abs(change)}  ({stock.get('change_pct',0)}%)",
              font=load_font(20), fill=chg_color)

    # Divider
    draw.rectangle([40, 144, W-40, 146], fill=(45, 50, 80))

    # Body text
    wrapped = textwrap.fill(section["text"], width=48)
    lines   = wrapped.split("\n")[:9]
    y = 164
    for line in lines:
        font = load_font(30) if len(line) < 40 else load_font(24)
        draw.text((60, y), line, font=font, fill=WHITE)
        y += 52

    # Footer
    draw.rectangle([0, H-42, W, H-6], fill=(20, 22, 35))
    draw.text((44, H-34),
              f"FinVise AI  |  Indian Stock Intelligence  |  {datetime.now().strftime('%d %b %Y')}",
              font=load_font(17), fill=SUBGRAY)

    return np.array(img)


def get_ffmpeg():
    """Get ffmpeg executable - try imageio_ffmpeg first, then system."""
    # Method 1: imageio_ffmpeg (most reliable on Windows)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    # Method 2: system ffmpeg
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    return None


def generate_video(script: str, stock: dict) -> str | None:
    try:
        import numpy as np
        from gtts import gTTS
        from PIL import Image
    except ImportError as e:
        st.error(f"Missing library: {e}. Run: pip install gtts pillow numpy")
        return None

    # Make sure imageio_ffmpeg is installed and provides ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if not ffmpeg_exe or not os.path.exists(ffmpeg_exe):
            raise RuntimeError("ffmpeg not found")
    except Exception:
        st.error("ffmpeg not found. Run this in terminal:\n\npip install imageio-ffmpeg\n\nThen try again.")
        return None

    import subprocess
    sections = parse_sections(script)
    tmpdir   = tempfile.mkdtemp()

    # ── Step 1: TTS audio per section ─────────────────────────────────────────
    audio_files   = []
    audio_lengths = []
    for i, sec in enumerate(sections):
        mp3 = os.path.join(tmpdir, f"audio_{i}.mp3")
        try:
            gTTS(text=sec["text"], lang="en", slow=False).save(mp3)
            # Get real duration with ffprobe
            probe = subprocess.run(
                [ffmpeg_exe, "-i", mp3],
                capture_output=True, text=True
            )
            dur = sec["duration"]
            for line in probe.stderr.split("\n"):
                if "Duration" in line:
                    try:
                        t = line.strip().split("Duration:")[1].split(",")[0].strip()
                        h, m, s = t.split(":")
                        dur = int(h)*3600 + int(m)*60 + float(s)
                    except Exception:
                        pass
            audio_files.append(mp3)
            audio_lengths.append(max(float(dur), float(sec["duration"])))
        except Exception as e:
            st.warning(f"TTS error section {i}: {e}")
            audio_files.append(None)
            audio_lengths.append(float(sec["duration"]))

    # ── Step 2: Draw slides → save as PNG frames ───────────────────────────────
    FPS        = 24
    frame_dirs = []
    for i, (sec, dur) in enumerate(zip(sections, audio_lengths)):
        slide     = draw_slide(sec, stock, i, len(sections))
        png_path  = os.path.join(tmpdir, f"slide_{i}.png")
        Image.fromarray(slide).save(png_path)
        frame_dirs.append((png_path, max(1, int(dur * FPS))))

    # ── Step 3: Build video from slides using ffmpeg concat ───────────────────
    # Write a concat file for ffmpeg
    concat_file = os.path.join(tmpdir, "concat.txt")
    with open(concat_file, "w") as f:
        for png_path, n_frames in frame_dirs:
            duration_sec = n_frames / FPS
            f.write(f"file '{png_path}'\n")
            f.write(f"duration {duration_sec:.3f}\n")
        # ffmpeg concat needs last file repeated
        f.write(f"file '{frame_dirs[-1][0]}'\n")

    silent_mp4 = os.path.join(tmpdir, "silent.mp4")
    cmd_video  = [
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-vf", "scale=1280:720",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        silent_mp4
    ]
    result = subprocess.run(cmd_video, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Video creation failed:\n{result.stderr[-500:]}")
        return None

    # ── Step 4: Concatenate audio ──────────────────────────────────────────────
    valid_audio = [f for f in audio_files if f and os.path.exists(f)]
    combined_mp3 = os.path.join(tmpdir, "combined.mp3")
    if valid_audio:
        with open(combined_mp3, "wb") as out_f:
            for af in valid_audio:
                with open(af, "rb") as in_f:
                    out_f.write(in_f.read())
    else:
        combined_mp3 = None

    # ── Step 5: Merge audio + video ───────────────────────────────────────────
    out_path = os.path.join(tmpdir, "finvise_brief.mp4")
    if combined_mp3 and os.path.exists(combined_mp3):
        cmd_merge = [
            ffmpeg_exe, "-y",
            "-i", silent_mp4,
            "-i", combined_mp3,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            out_path
        ]
        result2 = subprocess.run(cmd_merge, capture_output=True, text=True)
        if result2.returncode != 0:
            st.warning("Audio merge failed — video will be silent.")
            out_path = silent_mp4
    else:
        out_path = silent_mp4

    return out_path if os.path.exists(out_path) else None