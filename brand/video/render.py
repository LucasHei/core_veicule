"""Rend promo.html image par image puis encode le MP4 TikTok (1080x1920, 30 fps).

Usage : python3 render.py [--preview t1,t2,...]
"""
import pathlib
import shutil
import subprocess
import sys

from playwright.sync_api import sync_playwright

FPS = 30
DURATION = 30.0
HERE = pathlib.Path(__file__).parent
FRAMES = HERE / "frames"
OUT = HERE / "exo_ac_tiktok.mp4"

SEEK = """t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })"""


def main():
    preview = None
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        preview = [float(x) for x in sys.argv[2].split(",")]

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.goto((HERE / "promo.html").as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(500)

        if preview:
            for t in preview:
                page.evaluate(SEEK, t * 1000)
                page.screenshot(path=str(HERE / f"preview_{t:05.2f}.png"))
            browser.close()
            return

        shutil.rmtree(FRAMES, ignore_errors=True)
        FRAMES.mkdir()
        total = int(DURATION * FPS)
        for i in range(total):
            page.evaluate(SEEK, i * 1000 / FPS)
            page.screenshot(path=str(FRAMES / f"{i:04d}.jpg"), type="jpeg", quality=95)
        browser.close()

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", str(FRAMES / "%04d.jpg"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(OUT),
    ], check=True)
    shutil.rmtree(FRAMES)
    print(OUT)


if __name__ == "__main__":
    main()
