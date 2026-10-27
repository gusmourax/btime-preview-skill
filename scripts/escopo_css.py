#!/usr/bin/env python3
"""Prende o CSS de um sistema existente dentro da prévia, para reaproveitar o visual real sem vazar para a página.

Uso:
  py -3 escopo_css.py dom/app.css --out partes/app.css [--escopo .app-real] [--raiz "classe1 classe2"]

O que faz com cada regra:
  - prefixa os seletores com o escopo (`.botao` vira `.app-real .botao`);
  - troca `:root`, `html` e `body` pelo próprio escopo (`:root[data-theme=dark] .x` vira `.app-real[data-theme=dark] .x`,
    que nunca casa: a prévia fica sempre no tema claro do sistema);
  - classes listadas em --raiz (as que o framework põe no <html>/<body>, como as de fonte do next/font,
    `capturar.mjs` anota quais são no topo do HTML capturado) passam a valer no próprio escopo;
  - `position: fixed` vira `absolute` (fica preso à moldura da prévia) e `vh`/`dvh`/`svh`/`lvh`
    viram `calc(N * var(--btp-vh, 8px))`, para a tela não ter a altura da janela inteira;
  - remove @font-face (as fontes vêm do Google Fonts no app-theme) e mantém @keyframes como estão;
  - entra em @media, @supports, @layer e @container.
O resultado vai no <style id="app-css"> e o HTML da tela fica dentro de <div class="app-real">...</div>.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def ler_blocos(css: str, i: int = 0, fim: int | None = None):
    """Devolve [(prelúdio, corpo)] do nível atual; corpo é str (declarações) ou lista (blocos aninhados)."""
    fim = len(css) if fim is None else fim
    itens = []
    while i < fim:
        j = i
        while j < fim and css[j] not in "{};":
            if css[j] in "\"'":
                q = css[j]; j += 1
                while j < fim and css[j] != q:
                    j += 2 if css[j] == "\\" else 1
            j += 1
        if j >= fim:
            break
        pre = css[i:j].strip()
        if css[j] == ";":  # @import/@charset soltos
            if pre:
                itens.append((pre, None))
            i = j + 1
            continue
        if css[j] == "}":
            i = j + 1
            continue
        # achar o fechamento
        prof, k = 1, j + 1
        while k < fim and prof:
            c = css[k]
            if c in "\"'":
                q = c; k += 1
                while k < fim and css[k] != q:
                    k += 2 if css[k] == "\\" else 1
            elif c == "{":
                prof += 1
            elif c == "}":
                prof -= 1
            k += 1
        corpo = css[j + 1:k - 1]
        itens.append((pre, corpo))
        i = k
    return itens


def dividir_virgulas(s: str) -> list[str]:
    partes, prof, atual = [], 0, ""
    for c in s:
        if c in "([":
            prof += 1
        elif c in ")]":
            prof -= 1
        if c == "," and prof == 0:
            partes.append(atual.strip()); atual = ""
        else:
            atual += c
    if atual.strip():
        partes.append(atual.strip())
    return partes


RAIZ_RE = re.compile(r"^(?::root|html|body)(?![\w-])")


def escopar_seletor(sel: str, escopo: str, raiz: set[str]) -> str:
    s = sel.strip()
    if any(s == "." + c for c in raiz):
        return escopo
    # html body .x / :root .x / html.classe
    trocou = False
    while True:
        m = RAIZ_RE.match(s)
        if not m:
            break
        s = s[m.end():]
        trocou = True
        if s.startswith(" ") and RAIZ_RE.match(s.lstrip()):
            s = s.lstrip()
    if trocou:
        return escopo + s if not s or not s.startswith(" ") else escopo + s
    for c in raiz:
        if s.startswith("." + c + " "):
            return escopo + s[len(c) + 1:]
    return f"{escopo} {s}"


VH_RE = re.compile(r"(-?\d*\.?\d+)(?:d|s|l)?vh\b")


def ajustar_decls(corpo: str) -> str:
    corpo = re.sub(r"position\s*:\s*fixed", "position: absolute", corpo)
    corpo = VH_RE.sub(lambda m: f"calc({m.group(1)} * var(--btp-vh, 8px))", corpo)
    return corpo.strip()


def escopar(css: str, escopo: str, raiz: set[str], nivel: int = 0) -> str:
    saida = []
    ind = "  " * nivel
    for pre, corpo in ler_blocos(css):
        if corpo is None:
            if not pre.lower().startswith(("@import", "@charset", "@namespace")):
                saida.append(ind + pre + ";")
            continue
        low = pre.lower()
        if low.startswith("@font-face"):
            continue
        if low.startswith(("@keyframes", "@-webkit-keyframes", "@property", "@counter-style", "@page")):
            saida.append(f"{ind}{pre} {{ {corpo.strip()} }}")
            continue
        if low.startswith(("@media", "@supports", "@layer", "@container", "@scope", "@document")):
            dentro = escopar(corpo, escopo, raiz, nivel + 1)
            if dentro.strip():
                saida.append(f"{ind}{pre} {{\n{dentro}\n{ind}}}")
            continue
        if low.startswith("@"):
            continue
        seletores = [escopar_seletor(s, escopo, raiz) for s in dividir_virgulas(pre)]
        # Regras aninhadas (CSS nesting) dentro de uma regra comum: mantém o corpo como veio.
        saida.append(f"{ind}{', '.join(seletores)} {{ {ajustar_decls(corpo)} }}")
    return "\n".join(saida)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("css")
    ap.add_argument("--out", required=True)
    ap.add_argument("--escopo", default=".app-real")
    ap.add_argument("--raiz", default="", help="classes do <html>/<body> do sistema, separadas por espaço")
    a = ap.parse_args()
    css = Path(a.css).read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    raiz = {c for c in a.raiz.split() if c}
    out = escopar(css, a.escopo, raiz)
    cab = (f"/* CSS do sistema atual, preso em {a.escopo} por escopo_css.py. Não edite aqui: ajustes da versão nova "
           f"vão depois deste bloco. */\n{a.escopo} {{ position: relative; isolation: isolate; }}\n")
    Path(a.out).write_text(cab + out + "\n", encoding="utf-8")
    print(f"{Path(a.out)}: {len(out) / 1024:.0f} KB, escopo {a.escopo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
