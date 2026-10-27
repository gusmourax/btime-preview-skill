#!/usr/bin/env python3
"""Extrai quadros de uma gravação de reunião para a btime-preview.

Três modos, combináveis:
  --at 14:53 16:05 ...     um quadro em cada horário (os horários citados na transcrição)
  --scenes [--threshold]   um quadro a cada troca de tela compartilhada (detecção de cena)
  --every SEG              um quadro a cada SEG segundos (varredura grossa)

Uso:
  py -3 frames.py VIDEO --out DIR --at 04:12 21:40
  py -3 frames.py VIDEO --out DIR --scenes --start 10:00 --end 18:00 --max 40
  py -3 frames.py VIDEO --out DIR --every 30

Os arquivos saem como DIR/<modo>-HH-MM-SS.jpg e o índice em DIR/frames.md
(uma linha por quadro, com o horário), para ler com a ferramenta Read e
alinhar com a transcrição.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def find_bin(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    pats = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        pats.append(os.path.join(la, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "**", "bin", name + ".exe"))
    pats += ["/opt/homebrew/bin/" + name, "/usr/local/bin/" + name]
    for pat in pats:
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    sys.exit(f"{name} não encontrado. Rode scripts/check_env.py --install (com permissão do usuário).")


def to_sec(v: str | None) -> float | None:
    if v is None:
        return None
    parts = [float(x) for x in str(v).split(":")]
    s = 0.0
    for p in parts:
        s = s * 60 + p
    return s


def hms(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600:02d}-{s % 3600 // 60:02d}-{s % 60:02d}"


def label(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def duration(ffprobe: str, video: str) -> float:
    out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", video],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def grab(ffmpeg: str, video: str, t: float, dest: Path, width: int) -> bool:
    r = subprocess.run([ffmpeg, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", f"scale={width}:-2", "-q:v", "3", str(dest)], capture_output=True, text=True)
    return r.returncode == 0 and dest.exists()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--at", nargs="*", default=[], help="horários MM:SS ou HH:MM:SS")
    ap.add_argument("--offset", type=float, default=2.0, help="segundos somados a cada --at (a tela costuma aparecer logo depois da fala)")
    ap.add_argument("--scenes", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.12, help="sensibilidade da troca de cena (0.05 a 0.3)")
    ap.add_argument("--every", type=float, default=0)
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--max", type=int, default=60, help="teto de quadros em --scenes/--every")
    ap.add_argument("--width", type=int, default=1280)
    a = ap.parse_args()

    ffmpeg, ffprobe = find_bin("ffmpeg"), find_bin("ffprobe")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dur = duration(ffprobe, a.video)
    start = to_sec(a.start) or 0.0
    end = to_sec(a.end) or dur
    linhas: list[tuple[float, str, str]] = []

    for v in a.at:
        t = min(max(to_sec(v) + a.offset, 0), max(dur - 0.5, 0))
        dest = out / f"at-{hms(to_sec(v))}.jpg"
        if grab(ffmpeg, a.video, t, dest, a.width):
            linhas.append((to_sec(v), dest.name, "at"))

    if a.every:
        t = start
        n = 0
        while t < end and n < a.max:
            dest = out / f"every-{hms(t)}.jpg"
            if grab(ffmpeg, a.video, t, dest, a.width):
                linhas.append((t, dest.name, "every"))
            t += a.every
            n += 1

    if a.scenes:
        tmp = out / "_scene"
        tmp.mkdir(exist_ok=True)
        cmd = [ffmpeg, "-y", "-hide_banner", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", a.video,
               "-vf", f"select=eq(n\\,0)+gt(scene\\,{a.threshold}),showinfo,scale={a.width}:-2",
               "-fps_mode", "vfr", "-q:v", "3", str(tmp / "s-%04d.jpg")]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        times = [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]
        files = sorted(tmp.glob("s-*.jpg"))
        pares = list(zip(times, files))
        if len(pares) > a.max:  # mantém uma amostra espalhada
            passo = len(pares) / a.max
            pares = [pares[int(i * passo)] for i in range(a.max)]
        keep = set()
        for t, f in pares:
            real = start + t
            dest = out / f"scene-{hms(real)}.jpg"
            shutil.move(str(f), dest)
            keep.add(dest)
            linhas.append((real, dest.name, "scene"))
        shutil.rmtree(tmp, ignore_errors=True)
        if not pares:
            print("Nenhuma troca de cena encontrada; tente --threshold menor (ex.: 0.06) ou --every 30.", file=sys.stderr)

    linhas.sort()
    idx = out / "frames.md"
    with idx.open("w", encoding="utf-8") as fh:
        fh.write(f"# Quadros de {Path(a.video).name}\n\nDuração: {label(dur)}\n\n")
        for t, nome, modo in linhas:
            fh.write(f"- `{(out / nome).resolve()}` (t={label(t)}, {modo})\n")
    print(idx.read_text(encoding="utf-8"))
    return 0 if linhas else 1


if __name__ == "__main__":
    sys.exit(main())
