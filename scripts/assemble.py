#!/usr/bin/env python3
"""Monta WORK/preview.html a partir do template da skill e das partes editáveis do projeto.

Uso:  py -3 assemble.py WORK
Lê de WORK/partes/ (todas opcionais, menos data.json e telas.html):
  titulo.txt     conteúdo do <title> (ex.: "Prévia Portal Fornecedores")
  tema.css       conteúdo do bloco style app-theme (tokens --app-*)
  app.css        conteúdo do bloco style app-css
  data.json      conteúdo do bloco btp-data
  telas.html     os <template data-shared> e <template data-screen> do projeto
  app.js         conteúdo do bloco script app-js
e grava WORK/preview.html. O motor (btp-shell e btp-engine) vem sempre do template atual.
Editar as partes e rodar de novo é mais seguro que editar o preview.html à mão.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent.parent


def fora_de_comentario(s: str, abre: str, desde: int = 0) -> int:
    coms = [(m.start(), m.end()) for m in re.finditer(r"<!--.*?(?:-->|\Z)", s, re.S)]
    i = desde
    while True:
        i = s.find(abre, i)
        if i < 0 or not any(a <= i < b for a, b in coms):
            return i
        i += 1


def troca_conteudo(s: str, abre: str, fecha: str, novo: str) -> str:
    i = fora_de_comentario(s, abre)
    if i < 0:
        raise SystemExit(f"Bloco {abre} não encontrado no template.")
    a = i + len(abre)
    b = s.find(fecha, a)
    return s[:a] + "\n" + novo.strip("\n") + "\n" + s[b:]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    work = Path(sys.argv[1])
    partes = work / "partes"
    ler = lambda n: (partes / n).read_text(encoding="utf-8") if (partes / n).exists() else None
    s = (SKILL / "assets" / "template.html").read_text(encoding="utf-8")

    titulo = ler("titulo.txt")
    if titulo:
        s = re.sub(r"<title>.*?</title>", "<title>" + titulo.strip() + "</title>", s, count=1, flags=re.S)
    for nome, abre in (("tema.css", '<style id="app-theme">'), ("app.css", '<style id="app-css">')):
        c = ler(nome)
        if c is not None:
            s = troca_conteudo(s, abre, "</style>", c)
    data = ler("data.json")
    if data is None:
        raise SystemExit("Falta partes/data.json.")
    json.loads(data)  # erro cedo se o JSON estiver quebrado
    s = troca_conteudo(s, '<script type="application/json" id="btp-data">', "</script>", data)

    telas = ler("telas.html")
    if telas is None:
        raise SystemExit("Falta partes/telas.html.")
    # remove os templates e comentários de exemplo entre o btp-data e o app-js
    ini = s.find("</script>", fora_de_comentario(s, 'id="btp-data"')) + len("</script>")
    fim = fora_de_comentario(s, '<script id="app-js">')
    s = s[:ini] + "\n\n" + telas.strip("\n") + "\n\n" + s[fim:]
    js = ler("app.js")
    if js is not None:
        s = troca_conteudo(s, '<script id="app-js">', "</script>",
                           "window.btpInit = window.btpInit || {};\n" + js)
    out = work / "preview.html"
    out.write_text(s, encoding="utf-8")
    print(f"Montado: {out.resolve()} ({len(s.encode('utf-8')) / 1024:.0f} KB). Rode validate.py em seguida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
