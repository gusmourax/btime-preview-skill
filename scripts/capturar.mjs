#!/usr/bin/env node
/*
 * Roteiro de navegador para a btime-preview: prints e HTML/CSS reais do sistema atual
 * (rodando localmente) e prints da própria prévia (teste.html).
 *
 * Uso:
 *   node capturar.mjs ROTEIRO.json [--saida DIR] [--janela 1440x900] [--mostrar]
 *
 * O roteiro é uma lista de passos (ou { "janela": "1440x900", "passos": [...] }).
 * Cada passo é um objeto com uma ação:
 *   { "ir": "http://localhost:3000/movimentacoes" }       abre o endereço e espera carregar
 *   { "esperar": 800 }  ou  { "esperar": ".tabela tbody tr" }  pausa (ms) ou espera o seletor aparecer
 *   { "clicar": "button.troca" }  ou  { "clicar": { "texto": "Abrir", "dentro": "tbody tr" } }
 *   { "digitar": ["#email", "texto"] }                       digita tecla a tecla (dispara os eventos do app)
 *   { "tecla": "Enter" }
 *   { "rolar": 400 }  ou  { "rolar": ".seletor" }            rola a página ou leva o elemento à vista
 *   { "js": "document.body.classList.add('x')" }            roda código na página
 *   { "print": "hoje/t01.png", "seletor": "main" }          print da página ou só do elemento
 *   { "html": "dom/t01.html", "seletor": "main" }           outerHTML do elemento (sem <script>)
 *   { "css": "dom/app.css" }                                 todo o CSS aplicado à página (CSSOM)
 * No objeto do roteiro, "ocultar": ["nextjs-portal"] esconde esses seletores em toda página (selos de desenvolvimento).
 * Um passo "js" que devolve valor imprime o valor (bom para medir: scrollWidth, ordem das linhas).
 * Para a prévia: "ir" para teste.html#so-T01 mostra só a tela T01, sem marcações (print de "como vai ficar").
 * Textos aceitam ${ENV:NOME} (lido das variáveis de ambiente), para não gravar senha no roteiro.
 * Caminhos relativos saem em --saida (padrão: pasta do roteiro).
 *
 * Precisa de Node 22+ (WebSocket nativo) e Chrome ou Edge.
 */
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, isAbsolute, join, resolve } from "node:path";

const args = process.argv.slice(2);
if (!args.length || args.includes("-h") || args.includes("--help")) {
  console.log(readFileSync(new URL(import.meta.url), "utf8").split("*/")[0]);
  process.exit(args.length ? 0 : 1);
}
const opt = (nome, padrao) => { const i = args.indexOf(nome); return i >= 0 ? args[i + 1] : padrao; };
const roteiroPath = resolve(args[0]);
const bruto = JSON.parse(readFileSync(roteiroPath, "utf8"));
const roteiro = Array.isArray(bruto) ? { passos: bruto } : bruto;
const SAIDA = resolve(opt("--saida", dirname(roteiroPath)));
const [LARG, ALT] = (opt("--janela", roteiro.janela || "1440x900")).split("x").map(Number);
const MOSTRAR = args.includes("--mostrar");

const env = s => typeof s === "string" ? s.replace(/\$\{ENV:([A-Z0-9_]+)\}/g, (_, n) => {
  if (process.env[n] === undefined) throw new Error("Variável de ambiente ausente: " + n);
  return process.env[n];
}) : s;
const arq = p => { const f = isAbsolute(p) ? p : join(SAIDA, p); mkdirSync(dirname(f), { recursive: true }); return f; };
const dormir = ms => new Promise(r => setTimeout(r, ms));

function acharChrome() {
  const cands = process.platform === "win32" ? [
    process.env.PROGRAMFILES + "\\Google\\Chrome\\Application\\chrome.exe",
    process.env["PROGRAMFILES(X86)"] + "\\Google\\Chrome\\Application\\chrome.exe",
    process.env.LOCALAPPDATA + "\\Google\\Chrome\\Application\\chrome.exe",
    process.env["PROGRAMFILES(X86)"] + "\\Microsoft\\Edge\\Application\\msedge.exe",
    process.env.PROGRAMFILES + "\\Microsoft\\Edge\\Application\\msedge.exe",
  ] : process.platform === "darwin" ? [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  ] : ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/microsoft-edge"];
  const c = cands.find(p => p && existsSync(p));
  if (!c) throw new Error("Chrome/Edge não encontrado.");
  return c;
}

// ---------- CDP mínimo ----------
async function abrirNavegador() {
  const perfil = mkdtempSync(join(tmpdir(), "btp-chrome-"));
  const porta = 9300 + Math.floor(Math.random() * 500);
  const proc = spawn(acharChrome(), [
    ...(MOSTRAR ? [] : ["--headless=new"]), `--remote-debugging-port=${porta}`, `--user-data-dir=${perfil}`,
    `--window-size=${LARG},${ALT}`, "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
    "--force-device-scale-factor=1", "--lang=pt-BR", "about:blank",
  ], { stdio: "ignore" });
  let alvo;
  for (let i = 0; i < 60 && !alvo; i++) {
    await dormir(250);
    try { alvo = (await (await fetch(`http://127.0.0.1:${porta}/json/list`)).json()).find(t => t.type === "page"); } catch {}
  }
  if (!alvo) throw new Error("Não consegui falar com o navegador.");
  const ws = new WebSocket(alvo.webSocketDebuggerUrl);
  await new Promise((ok, erro) => { ws.onopen = ok; ws.onerror = erro; });
  let seq = 0; const pend = new Map(); const ouvintes = new Set();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const { ok, erro } = pend.get(m.id); pend.delete(m.id); m.error ? erro(new Error(m.error.message)) : ok(m.result); }
    else if (m.method) ouvintes.forEach(f => f(m));
  };
  const cdp = (method, params = {}) => new Promise((ok, erro) => { const id = ++seq; pend.set(id, { ok, erro }); ws.send(JSON.stringify({ id, method, params })); });
  const fechar = () => { try { ws.close(); } catch {} proc.kill(); setTimeout(() => { try { rmSync(perfil, { recursive: true, force: true }); } catch {} }, 1500); };
  return { cdp, ouvintes, fechar };
}

const main = async () => {
  const { cdp, ouvintes, fechar } = await abrirNavegador();
  const avaliar = async (expr) => {
    const r = await cdp("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error("Erro na página: " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result.value;
  };
  await cdp("Page.enable"); await cdp("Runtime.enable");
  await cdp("Emulation.setDeviceMetricsOverride", { width: LARG, height: ALT, deviceScaleFactor: 1, mobile: false });
  // "ocultar": seletores escondidos em toda página (selos de desenvolvimento, banners de cookie).
  if (roteiro.ocultar) {
    const css = JSON.stringify([].concat(roteiro.ocultar).join(",") + "{display:none!important}");
    await cdp("Page.addScriptToEvaluateOnNewDocument", { source: `addEventListener("DOMContentLoaded", () => { const s = document.createElement("style"); s.textContent = ${css}; document.head.append(s); });` });
  }
  ouvintes.add(m => { if (m.method === "Runtime.exceptionThrown") console.warn("  ! erro na página:", m.params.exceptionDetails?.exception?.description?.split("\n")[0]); });

  const esperarCarga = () => new Promise(ok => { const f = m => { if (m.method === "Page.loadEventFired") { ouvintes.delete(f); ok(); } }; ouvintes.add(f); setTimeout(ok, 15000); });
  const esperarSeletor = async (sel, ms = 15000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) { if (await avaliar(`!!document.querySelector(${JSON.stringify(sel)})`)) return; await dormir(150); }
    throw new Error("Não apareceu: " + sel);
  };
  // Elemento por seletor ou por texto; devolve o centro na tela (e rola até ele).
  const localizar = async (alvo) => {
    const q = typeof alvo === "string" ? { seletor: alvo } : alvo;
    const r = await avaliar(`(() => {
      const q = ${JSON.stringify(q)};
      let els = [...document.querySelectorAll(q.seletor || q.dentro || "button, a, [role=button], [role=tab], summary, label, th, td, li")];
      if (q.texto) els = els.flatMap(e => [e, ...e.querySelectorAll("*")]).filter(e => (e.textContent || "").trim().replace(/\\s+/g, " ") === q.texto || (e.getAttribute("aria-label") || "") === q.texto);
      const el = els.find(e => e.getClientRects().length) ; if (!el) return null;
      let r = el.getBoundingClientRect();
      if (r.top < 0 || r.bottom > innerHeight || r.left < 0 || r.right > innerWidth) { el.scrollIntoView({ block: "center", inline: "nearest" }); r = el.getBoundingClientRect(); }
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    })()`);
    if (!r) throw new Error("Elemento não encontrado: " + JSON.stringify(alvo));
    return r;
  };
  for (const [i, passo] of roteiro.passos.entries()) {
    const rot = Object.keys(passo)[0];
    process.stdout.write(`${String(i + 1).padStart(2)}. ${rot} ${JSON.stringify(passo[rot]).slice(0, 70)}\n`);
    if (passo.ir) {
      // Trocar só o #fragmento não recarrega a página: passa por about:blank para o motor da prévia rodar de novo.
      if (env(passo.ir).includes("#")) { const b = esperarCarga(); await cdp("Page.navigate", { url: "about:blank" }); await b; }
      const c = esperarCarga(); await cdp("Page.navigate", { url: env(passo.ir) }); await c; await dormir(passo.pausa ?? 600); }
    else if (passo.esperar !== undefined) { typeof passo.esperar === "number" ? await dormir(passo.esperar) : await esperarSeletor(passo.esperar); }
    else if (passo.clicar) {
      const { x, y } = await localizar(passo.clicar);
      for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) await cdp("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: 1 });
      await dormir(passo.pausa ?? 500);
    }
    else if (passo.digitar) {
      const [sel, txt] = passo.digitar;
      const { x, y } = await localizar(sel);
      for (const type of ["mousePressed", "mouseReleased"]) await cdp("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: 1 });
      for (const ch of env(txt)) await cdp("Input.insertText", { text: ch });
      await dormir(200);
    }
    else if (passo.tecla) {
      const k = passo.tecla, cod = { Enter: 13, Escape: 27, Tab: 9 }[k];
      await cdp("Input.dispatchKeyEvent", { type: "keyDown", key: k, code: k, windowsVirtualKeyCode: cod, ...(k === "Enter" ? { text: "\r" } : {}) });
      await cdp("Input.dispatchKeyEvent", { type: "keyUp", key: k, code: k, windowsVirtualKeyCode: cod });
      await dormir(passo.pausa ?? 400);
    }
    else if (passo.rolar !== undefined) {
      if (typeof passo.rolar === "number") await avaliar(`(document.scrollingElement || document.body).scrollBy({ top: ${passo.rolar}, behavior: "smooth" })`);
      else await localizar(passo.rolar);
      await dormir(passo.pausa ?? 600);
    }
    else if (passo.js) { const v = await avaliar(env(passo.js)); if (v !== undefined && v !== null) console.log("  =", typeof v === "string" ? v : JSON.stringify(v)); await dormir(passo.pausa ?? 200); }
    else if (passo.print) {
      let clip;
      if (passo.seletor) {
        clip = await avaliar(`(() => { const r = document.querySelector(${JSON.stringify(passo.seletor)}).getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height, scale: 1 }; })()`);
      }
      const r = await cdp("Page.captureScreenshot", { format: passo.print.endsWith(".jpg") ? "jpeg" : "png", quality: passo.print.endsWith(".jpg") ? 85 : undefined, clip, captureBeyondViewport: !!passo.inteira || !!clip });
      writeFileSync(arq(passo.print), Buffer.from(r.data, "base64"));
    }
    else if (passo.html) {
      const h = await avaliar(`(() => { const el = document.querySelector(${JSON.stringify(passo.seletor || "body")}).cloneNode(true);
        el.querySelectorAll("script, noscript, next-route-announcer, nextjs-portal").forEach(x => x.remove());
        const raiz = (document.documentElement.className + " " + document.body.className).trim().replace(/\\s+/g, " ");
        return "<!-- raiz: " + raiz + " -->\\n" + el.outerHTML; })()`);
      writeFileSync(arq(passo.html), h);
    }
    else if (passo.css) {
      const c = await avaliar(`[...document.styleSheets].map(s => { try { return [...s.cssRules].map(r => r.cssText).join("\\n"); } catch (e) { return "/* folha sem acesso: " + s.href + " */"; } }).join("\\n")`);
      writeFileSync(arq(passo.css), c);
    }
    else if (passo.gravar) throw new Error("A gravação de vídeo saiu da skill: use prints (passo \"print\").");
    else throw new Error("Passo desconhecido: " + JSON.stringify(passo));
  }
  fechar();
};

main().catch(e => { console.error("Erro:", e.message); process.exit(1); });
