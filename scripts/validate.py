#!/usr/bin/env python3
"""Valida uma prévia btime-preview e gera a versão de publicação.

Uso:
  py -3 validate.py <preview.html>                          só valida
  py -3 validate.py <preview.html> --out <publicar.html>    valida e grava a cópia de publicação,
                                                            com as imagens locais embutidas (data URI)
  ... --local <teste.html>                                  também grava uma cópia com doctype, para abrir
                                                            no navegador ou tirar print com Chrome headless

Confere: motor do template intacto, coerência entre btp-data e os <template>
(ids, tipos, trechos com fonte existente, data-d, data-goto, data-use),
imagens locais existentes e tamanho final. Sai com código 1 se houver erro.
No Windows, passe caminhos no formato C:/... (não /c/...).
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TIPOS_DEC = {"reuniao", "documento", "referencia", "inferencia", "aberto"}
MUDANCAS = {"nova", "altera", "remove"}
MOTOR_ATUAL = 2
TIPOS_FONTE = {"reuniao", "documento", "design", "url", "imagem", "outro"}
CDNS = ("https://cdnjs.cloudflare.com/", "https://cdn.jsdelivr.net/npm/", "https://unpkg.com/",
        "https://cdn.tailwindcss.com", "https://code.jquery.com/")
TEMPLATE_TITLE = "Prévia Portal de Pedidos"
LIMITE = 15 * 1024 * 1024


def opt(nome: str) -> str | None:
    if nome in sys.argv:
        i = sys.argv.index(nome)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def main() -> int:
    pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--out", "--local")]
    if not pos:
        print(__doc__)
        return 2
    path = Path(pos[0])
    raw = path.read_text(encoding="utf-8")
    # comentário sem fechamento esconde todo o resto da página; o navegador faz o mesmo
    html = re.sub(r"<!--.*?(?:-->|\Z)", "", raw, flags=re.S)
    base = path.parent
    erros: list[str] = []
    avisos: list[str] = []
    if raw.count("<!--") != raw.count("-->"):
        erros.append("Há um comentário HTML (<!--) sem fechamento: tudo depois dele some e a página abre em branco.")

    # Motor intacto
    if not re.search(r'<style id="btp-shell">.*?\.btp-root \[hidden\].*?</style>', html, re.S):
        erros.append("Bloco style btp-shell ausente ou cortado (a página abriria em branco). Recopie do template da skill.")
    motor = re.search(r'<script id="btp-engine">\s*/\* btime-preview engine v(\d+).*?\}\)\(\);\s*</script>', html, re.S)
    if not motor:
        erros.append("Bloco script btp-engine ausente ou cortado. Recopie do template da skill.")
    elif int(motor.group(1)) < MOTOR_ATUAL:
        avisos.append(f"Motor v{motor.group(1)} desatualizado (atual: v{MOTOR_ATUAL}). Rode scripts/upgrade_engine.py para trocar só os blocos do motor.")
    if '<div id="btp"></div>' not in html:
        erros.append('Falta o ponto de montagem <div id="btp"></div>.')

    m = re.search(r'<script[^>]*type="application/json"[^>]*id="btp-data"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        print("ERRO:  bloco btp-data (script application/json) não encontrado.")
        return 1
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"ERRO:  btp-data não é JSON válido: {e}")
        return 1

    screens = dict(re.findall(r'<template\s+data-screen="([^"]+)"\s*>(.*?)</template>', html, re.S))
    shared = dict(re.findall(r'<template\s+data-shared="([^"]+)"\s*>(.*?)</template>', html, re.S))
    t = re.search(r"<title>(.*?)</title>", raw[:8192], re.S)
    if not t:
        erros.append("Falta <title> nos primeiros 8 KB do arquivo.")
    elif t.group(1).strip() == TEMPLATE_TITLE:
        erros.append("O <title> ainda é o do template. Use o nome do projeto (2 a 4 palavras).")
    if data.get("exemplo"):
        erros.append('btp-data ainda tem "exemplo": true (conteúdo do template). Remova a chave.')

    P = data.get("projeto") or {}
    for k in ("nome", "tipo", "geradoEm"):
        if not P.get(k):
            erros.append(f"projeto.{k} vazio.")
    if P.get("tipo") not in (None, "novo", "refatoracao"):
        erros.append('projeto.tipo deve ser "novo" ou "refatoracao".')

    fontes = data.get("fontes") or []
    telas = data.get("telas") or []
    decs = data.get("decisoes") or []

    def ids(lista, nome):
        vistos = set()
        for x in lista:
            i = x.get("id")
            if not i:
                erros.append(f"{nome} sem id: {json.dumps(x, ensure_ascii=False)[:80]}")
            elif i in vistos:
                erros.append(f"{nome} com id repetido: {i}")
            vistos.add(i)
        return vistos

    F, T, D = ids(fontes, "fonte"), ids(telas, "tela"), ids(decs, "decisão")
    for f in fontes:
        if f.get("tipo") not in TIPOS_FONTE:
            erros.append(f"Fonte {f.get('id')}: tipo '{f.get('tipo')}' inválido ({', '.join(sorted(TIPOS_FONTE))}).")
        if str(f.get("id", "")).startswith("D"):
            erros.append(f"Fonte {f.get('id')}: prefixo D é das decisões. Use R (reunião), A (arquivo) ou V (visual).")
        if not f.get("link"):
            avisos.append(f"Fonte {f.get('id')} sem link. Quem ler a prévia não consegue abrir o original.")

    marcadas: set[str] = set()
    usados: set[str] = set()
    for nome, body in [(f"tela {k}", v) for k, v in screens.items()] + [(f"trecho {k}", v) for k, v in shared.items()]:
        for val in re.findall(r'data-d="([^"]*)"', body):
            for did in val.split():
                marcadas.add(did)
                if did not in D:
                    erros.append(f"{nome}: data-d=\"{did}\" não existe em decisoes.")
        for g in re.findall(r'data-goto="([^"]*)"', body):
            if g not in T:
                erros.append(f"{nome}: data-goto=\"{g}\" aponta para tela inexistente.")
        for u in re.findall(r'data-use="([^"]*)"', body):
            usados.add(u)
            if u not in shared:
                erros.append(f"{nome}: data-use=\"{u}\" sem <template data-shared=\"{u}\">.")
        for i in re.findall(r'\sid="([^"]+)"', body):
            avisos.append(f"{nome}: id=\"{i}\" dentro do template. A tela é montada duas vezes; use data-* e root.querySelector.")
        if re.search(r"document\.(getElementById|querySelector)", body):
            avisos.append(f"{nome}: script consultando document. Use btpInit.Txx(root, api).")
    for k in screens:
        if k not in T:
            erros.append(f"<template data-screen=\"{k}\"> sem tela correspondente em btp-data.")

    for tela in telas:
        tid = tela.get("id")
        if tid not in screens:
            erros.append(f"Tela {tid} sem <template data-screen=\"{tid}\">.")
        for did in tela.get("decisoes") or []:
            if did not in D:
                erros.append(f"Tela {tid}: decisão de tela '{did}' não existe.")
            marcadas.add(did)
        for chave in ("hoje", "depois"):
            for h in tela.get(chave) or []:
                if h.get("fonte") and h["fonte"] not in F:
                    erros.append(f"Tela {tid}: mídia '{chave}' cita fonte inexistente {h['fonte']}.")
                if h.get("video"):
                    erros.append(f"Tela {tid}: '{chave}' tem vídeo; a prévia usa só imagens (vídeo pesa no artefato). Troque por um print.")
                elif not h.get("img"):
                    erros.append(f"Tela {tid}: item de '{chave}' sem 'img'.")
        if not any(tid in (d.get("telas") or []) for d in decs) and not tela.get("decisoes"):
            avisos.append(f"Tela {tid} ({tela.get('nome')}) não tem nenhuma decisão que explique por que existe.")
        if P.get("tipo") == "refatoracao" and not tela.get("hoje") and not tela.get("hojeAviso"):
            avisos.append(f"Tela {tid}: refatoração sem imagem 'Como está hoje' nem 'hojeAviso' explicando a falta.")

    for d in decs:
        did, tp = d.get("id", "?"), d.get("tipo")
        if tp not in TIPOS_DEC:
            erros.append(f"{did}: tipo '{tp}' inválido ({', '.join(sorted(TIPOS_DEC))}).")
        if not d.get("titulo"):
            erros.append(f"{did}: sem título.")
        for tid in d.get("telas") or []:
            if tid not in T:
                erros.append(f"{did}: tela '{tid}' não existe.")
        if not d.get("telas"):
            avisos.append(f"{did}: sem telas. Não aparece em nenhuma ficha.")
        trechos = d.get("trechos") or []
        for tr in trechos:
            if tr.get("fonte") not in F:
                erros.append(f"{did}: trecho cita fonte inexistente '{tr.get('fonte')}'.")
            if not (tr.get("texto") or "").strip():
                erros.append(f"{did}: trecho sem texto.")
        if tp in ("reuniao", "documento", "referencia") and not trechos:
            erros.append(f"{did}: tipo '{tp}' precisa de pelo menos um trecho da fonte. Sem trecho, use 'inferencia'.")
        if tp == "inferencia" and not d.get("explicacao"):
            erros.append(f"{did}: inferência precisa de explicação (por que foi proposta).")
        if d.get("mudanca") and d["mudanca"] not in MUDANCAS:
            erros.append(f"{did}: mudanca '{d['mudanca']}' inválida ({', '.join(sorted(MUDANCAS))}).")
        if tp == "aberto" and not d.get("pergunta"):
            erros.append(f"{did}: ponto em aberto precisa de 'pergunta'.")
        if did not in marcadas:
            avisos.append(f"{did}: não está marcada em nenhuma prévia (data-d) nem como decisão de tela.")

    for src in re.findall(r'<script[^>]+src="([^"]+)"', html):
        if not src.startswith(CDNS):
            erros.append(f"Script externo fora da lista permitida: {src}")
        elif re.search(r"@latest|/latest/", src):
            erros.append(f"Fixe a versão exata do script: {src}")

    imgs: set[str] = set()
    for tela in telas:
        for h in (tela.get("hoje") or []) + (tela.get("depois") or []):
            imgs.update([h["img"]] if h.get("img") else [])
    for body in list(screens.values()) + list(shared.values()):
        imgs.update(re.findall(r'<img[^>]+src="([^"]+)"', body))
        if re.search(r"<video[\s>]", body):
            erros.append("Há <video> numa tela; a prévia usa só imagens (vídeo pesa no artefato).")
    locais: dict[str, Path] = {}
    for src in sorted(imgs):
        if src.startswith("data:"):
            continue
        if src.startswith("http"):
            erros.append(f"Mídia externa não carrega no artefato: {src}. Baixe para img/.")
            continue
        p = (base / src).resolve()
        if p.exists():
            locais[src] = p
        else:
            erros.append(f"Mídia não encontrada: {src} (procurada em {p})")

    final = raw
    for src, p in locais.items():
        mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
        final = final.replace(f'"{src}"', f'"{uri}"')
    tamanho = len(final.encode("utf-8"))
    if tamanho > LIMITE:
        maiores = sorted(locais.items(), key=lambda kv: -kv[1].stat().st_size)[:3]
        erros.append(f"A página publicada teria {tamanho / 1e6:.1f} MB (limite 16 MB). Maiores: "
                     + ", ".join(f"{k} ({v.stat().st_size / 1e6:.1f} MB)" for k, v in maiores)
                     + ". Reduza as imagens (ffmpeg -vf scale=1280:-2 -q:v 5).")

    tipos: dict[str, int] = {}
    for d in decs:
        tipos[str(d.get("tipo"))] = tipos.get(str(d.get("tipo")), 0) + 1
    print(f"Prévia: {P.get('nome')} · v{P.get('versao', 1)} · {len(telas)} telas · {len(decs)} decisões · {len(fontes)} fontes · {len(locais)} imagens")
    print("Decisões por tipo: " + ", ".join(f"{k}={v}" for k, v in sorted(tipos.items())))
    if tipos.get("inferencia", 0) > max(3, len(decs) // 3):
        avisos.append("Mais de um terço das decisões são inferências. Procure trechos nas fontes ou marque como 'aberto' com a pergunta.")
    for e in erros:
        print("ERRO:  " + e)
    for a in avisos:
        print("AVISO: " + a)

    if erros:
        print(f"\n{len(erros)} erro(s). Corrija antes de publicar.")
        return 1
    out, local = opt("--out"), opt("--local")
    if out:
        Path(out).write_text(final, encoding="utf-8")
        print(f"\nVersão de publicação: {Path(out).resolve()} ({tamanho / 1e6:.2f} MB, imagens embutidas; publique sem 'files').")
    if local:
        wrap = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
                '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
                + final + "</body></html>")
        Path(local).write_text(wrap, encoding="utf-8")
        print(f"Cópia para teste local: {Path(local).resolve()}")
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
