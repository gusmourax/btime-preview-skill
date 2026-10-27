"""Troca os blocos btp-shell e btp-engine de uma prévia pelos do template atual da skill.

Uso: py -3 upgrade_engine.py WORK/preview.html   (faça backup antes; depois rode validate.py)
"""
import re
import sys
from pathlib import Path


def bloco(s, abre, fecha):
    comentarios = [(m.start(), m.end()) for m in re.finditer(r"<!--.*?-->", s, re.S)]
    i = 0
    while True:
        i = s.find(abre, i)
        if i < 0:
            raise SystemExit(f"bloco {abre} não encontrado fora de comentário")
        if not any(a <= i < b for a, b in comentarios):
            j = s.find(fecha, i)
            return i, j + len(fecha)
        i += 1


tpl = (Path(__file__).resolve().parent.parent / "assets" / "template.html").read_text(encoding="utf-8")
alvo = Path(sys.argv[1])
s = alvo.read_text(encoding="utf-8")
for abre, fecha in (('<style id="btp-shell">', "</style>"), ('<script id="btp-engine">', "</script>")):
    a, b = bloco(tpl, abre, fecha)
    novo = tpl[a:b]
    a, b = bloco(s, abre, fecha)
    s = s[:a] + novo + s[b:]
alvo.write_text(s, encoding="utf-8")
print("motor atualizado em", alvo)
