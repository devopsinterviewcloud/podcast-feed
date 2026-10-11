#!/usr/bin/env python3
"""Download the pre-July-2026 episode audio from the YouTube copies.

Needs a residential IP (datacenter IPs get YouTube's bot wall) and a CURRENT
yt-dlp -- an old one fails with "Only images are available" / "Precondition
check failed". Easiest is the standalone binary, dropped in the repo root:

    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp && chmod +x yt-dlp
    (Windows: same URL with yt-dlp.exe)

then run from the repo root:

    python3 tools/restore_audio.py

Safe to re-run; existing files are skipped.
"""
import json
import pathlib
import shutil
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parent.parent
ytdlp = next((str(p) for p in (root / "yt-dlp", root / "yt-dlp.exe") if p.exists()),
             shutil.which("yt-dlp"))
if not ytdlp:
    sys.exit("yt-dlp not found -- see the note at the top of this script")
print("using", ytdlp, "version",
      subprocess.run([ytdlp, "--version"], capture_output=True, text=True).stdout.strip())

jobs = json.load(open(root / "tools" / "restore_jobs.json"))
audio = root / "audio"
failed = []
for i, j in enumerate(jobs, 1):
    out = audio / f"{j['out']}.m4a"
    if out.exists() and out.stat().st_size > 0:
        continue
    print(f"[{i}/{len(jobs)}] {j['title'][:60]}")
    r = subprocess.run([ytdlp, "-q", "-f", "bestaudio[ext=m4a]/bestaudio",
                        "-o", str(audio / (j["out"] + ".%(ext)s")),
                        f"https://www.youtube.com/watch?v={j['videoId']}"])
    if r.returncode:
        failed.append(j["videoId"])

print(f"done, {len(jobs) - len(failed)}/{len(jobs)} present"
      + (f", failed: {failed}" if failed else ""))
