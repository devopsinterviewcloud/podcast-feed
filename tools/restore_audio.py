#!/usr/bin/env python3
"""Download the pre-July-2026 episode audio from the YouTube copies.

Needs a residential IP (datacenter IPs get YouTube's bot wall) and yt-dlp
on PATH (pip install yt-dlp). Run from the repo root:

    python3 tools/restore_audio.py

Safe to re-run; existing files are skipped.
"""
import json
import pathlib
import subprocess

jobs = json.load(open("tools/restore_jobs.json"))
audio = pathlib.Path("audio")
failed = []
for i, j in enumerate(jobs, 1):
    out = audio / f"{j['out']}.m4a"
    if out.exists() and out.stat().st_size > 0:
        continue
    print(f"[{i}/{len(jobs)}] {j['title'][:60]}")
    r = subprocess.run(["yt-dlp", "-q", "-f", "bestaudio[ext=m4a]/bestaudio",
                        "-o", str(audio / (j["out"] + ".%(ext)s")),
                        f"https://www.youtube.com/watch?v={j['videoId']}"])
    if r.returncode:
        failed.append(j["videoId"])

print(f"done, {len(jobs) - len(failed)}/{len(jobs)} present"
      + (f", failed: {failed}" if failed else ""))
