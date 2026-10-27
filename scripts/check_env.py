#!/usr/bin/env python3
"""Confere (e, com --install, instala) o que a btime-preview usa para tirar quadros das gravações.

Uso:
  py -3 check_env.py            só confere e mostra o que falta
  py -3 check_env.py --install  instala o que falta (rode só depois que o usuário autorizar)

A skill não transcreve áudio: o texto das reuniões vem sempre da transcrição
que já está nos documentos do projeto (Anotações do Gemini, Transcript do Meet).
Conectores do Google (Drive, Agenda, Gmail) não aparecem aqui: são checados
pelo Claude com ToolSearch, porque vivem na conta do claude.ai, não na máquina.
"""
from __future__ import annotations

import glob
import json
import os
import platform
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SO = platform.system()  # Windows, Darwin, Linux


def which(name: str) -> str | None:
    p = shutil.which(name)
    if p:
        return p
    la = os.environ.get("LOCALAPPDATA")
    if SO == "Windows" and la:
        for pat in (os.path.join(la, "Microsoft", "WinGet", "Packages", "*", "**", name + ".exe"),
                    os.path.join(la, "Microsoft", "WinGet", "Links", name + ".exe")):
            hits = glob.glob(pat, recursive=True)
            if hits:
                return hits[0]
    return None


INSTALL = {
    "ffmpeg": {"Windows": ["winget", "install", "-e", "--id", "Gyan.FFmpeg", "--accept-source-agreements", "--accept-package-agreements"],
               "Darwin": ["brew", "install", "ffmpeg"], "Linux": ["sudo", "apt-get", "install", "-y", "ffmpeg"]},
    "yt-dlp": {"Windows": ["winget", "install", "-e", "--id", "yt-dlp.yt-dlp", "--accept-source-agreements", "--accept-package-agreements"],
               "Darwin": ["brew", "install", "yt-dlp"], "Linux": [sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"]},
}


def status() -> dict:
    return {
        "sistema": SO,
        "python": sys.version.split()[0],
        "ffmpeg": which("ffmpeg"),
        "ffprobe": which("ffprobe"),
        "yt-dlp": which("yt-dlp"),
        "node": which("node"),
        "chrome": which("chrome") or next((p for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                                       "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"] if os.path.exists(p)), None),
        "edge": next((p for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                                  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"] if os.path.exists(p)), None),
    }


def main() -> int:
    s = status()
    faltam = [k for k in ("ffmpeg", "ffprobe") if not s[k]]
    if "--install" in sys.argv:
        for k in ("ffmpeg", "yt-dlp"):
            if (k == "ffmpeg" and faltam) or (k == "yt-dlp" and not s["yt-dlp"]):
                cmd = INSTALL[k].get(SO)
                if cmd:
                    print("→ " + " ".join(cmd), flush=True)
                    subprocess.run(cmd)
        s = status()
        faltam = [k for k in ("ffmpeg", "ffprobe") if not s[k]]
        if faltam and SO == "Windows":
            print("Se o winget acabou de instalar, o PATH só atualiza num terminal novo; os scripts da skill já procuram na pasta do WinGet.")

    print(json.dumps(s, ensure_ascii=False, indent=2))
    print()
    print("Quadros do vídeo (frames.py): " + ("pronto" if not faltam else "falta " + ", ".join(faltam)))
    print("Transcrição: sempre a dos documentos do projeto (Anotações do Gemini / Transcript do Meet).")
    navegador = s["chrome"] or s["edge"]
    print("Prints e HTML das telas (capturar.mjs): " + ("pronto" if s["node"] and navegador
          else "falta " + ", ".join(x for x, ok in (("node 22+", s["node"]), ("Chrome ou Edge", navegador)) if not ok)))
    return 0 if not faltam else 1


if __name__ == "__main__":
    sys.exit(main())
