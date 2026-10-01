"""Monte la pub TikTok à partir de tes vrais clips (brand/clips/) selon brand/clips/plan.json.

- recadre chaque clip en 1080x1920 (centre), 30 fps, coupé pile sur le beat
- ajoute les sous-titres style TikTok (blanc, contour noir)
- termine par la carte logo de exo_ac_tiktok.mp4 (25.5–30 s)
- pose la musique exo_ac_beat.wav (lancer music.py avant si besoin)

Usage : python3 montage.py            -> exo_ac_tiktok_clips.mp4
        python3 montage.py --test     -> génère de faux clips de test d'abord
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
CLIPS = HERE.parent / "clips"
FONT = HERE.parent / "fonts" / "ChakraPetch-Bold.ttf"
TMP = HERE / "_montage"
OUT = HERE / "exo_ac_tiktok_clips.mp4"
FPS = 30


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def make_test_clips(plan):
    names = {c["file"] for s in plan["segments"] for c in s["clips"]}
    for i, n in enumerate(sorted(names)):
        ff("-f", "lavfi", "-i", f"testsrc2=size=1920x1080:rate=30:duration=15",
           "-vf", f"hue=h={i * 70},drawtext=fontfile={FONT}:text='{n}':fontsize=120:"
                  "fontcolor=white:x=(w-tw)/2:y=(h-th)/2",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", CLIPS / n)


def caption_filter(seg, idx):
    if not seg.get("caption"):
        return ""
    txt = TMP / f"cap{idx}.txt"
    txt.write_text(seg["caption"])
    size = 190 if seg.get("big") else 92
    y = "(h-th)/2" if seg.get("big") else "h*0.62"
    return (f",drawtext=fontfile={FONT}:textfile={txt}:fontsize={size}:fontcolor=white:"
            f"borderw={14 if seg.get('big') else 9}:bordercolor=black:line_spacing=12:"
            f"x=(w-tw)/2:y={y}")


def main():
    plan = json.loads((CLIPS / "plan.json").read_text())
    if "--test" in sys.argv:
        make_test_clips(plan)

    missing = sorted({c["file"] for s in plan["segments"] for c in s["clips"]
                      if not (CLIPS / c["file"]).exists()})
    if missing:
        sys.exit("Clips manquants dans brand/clips/ : " + ", ".join(missing))
    beat = HERE / "exo_ac_beat.wav"
    promo = HERE / "exo_ac_tiktok.mp4"
    for f in (beat, promo):
        if not f.exists():
            sys.exit(f"Manque {f.name} : lance render.py puis music.py d'abord.")

    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir()
    parts = []
    for i, seg in enumerate(plan["segments"]):
        dur = (seg["to"] - seg["from"]) / len(seg["clips"])
        cap = caption_filter(seg, i)
        for j, clip in enumerate(seg["clips"]):
            out = TMP / f"p{i:02d}_{j}.mp4"
            vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                  f"fps={FPS},setsar=1,eq=contrast=1.08:saturation=1.15{cap}")
            ff("-ss", clip.get("start", 0), "-t", f"{dur:.3f}", "-i", CLIPS / clip["file"],
               "-vf", vf, "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
               "-pix_fmt", "yuv420p", "-frames:v", round(dur * FPS), out)
            parts.append(out)

    fin = plan["fin"]
    end = TMP / "p99_fin.mp4"
    ff("-ss", fin["from"], "-t", fin["to"] - fin["from"], "-i", promo, "-an",
       "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", end)
    parts.append(end)

    lst = TMP / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    ff("-f", "concat", "-safe", "0", "-i", lst, "-i", beat, "-map", "0:v", "-map", "1:a",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT)
    shutil.rmtree(TMP)
    print(OUT)


if __name__ == "__main__":
    main()
