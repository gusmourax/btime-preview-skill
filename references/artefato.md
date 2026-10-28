# Contrato do artefato

O artefato sai sempre de `assets/template.html`. O motor (`btp-shell` e `btp-engine`) não se edita: é ele que garante que toda prévia da btime tenha a mesma cara, a mesma legenda e o mesmo comportamento. O trabalho por projeto é preencher dados e desenhar as telas.

## Sumário
1. Estrutura do arquivo
2. `btp-data` (JSON)
3. Telas: `<template data-screen>`
4. Marcações `data-d`
5. Interações sem JavaScript
6. `app-js` para o resto
7. Kit de componentes `.app-*`
8. Design system do cliente (`app-theme`)
9. Escrita
10. Checklist antes de publicar

## 1. Estrutura do arquivo

```
<title>                     EDITAR  nome do projeto, 2 a 4 palavras ("Prévia Hub Financeiro")
<style id="btp-shell">      motor visual (não editar)
<style id="app-theme">      EDITAR  tokens --app-* do cliente
<style id="app-css">        EDITAR  CSS extra dos componentes (opcional)
<script id="btp-data">      EDITAR  projeto, fontes, telas, decisões
<template data-shared="menu"> EDITAR trechos repetidos (menu lateral)
<template data-screen="T01"> EDITAR uma por tela
<script id="app-js">        EDITAR  interações específicas (opcional)
<div id="btp">              ponto de montagem
<script id="btp-engine">    motor (não editar)
```

O arquivo não tem `<!doctype>`, `<html>`, `<head>` nem `<body>`: a publicação do Artifact embrulha. Para testar localmente, use a cópia que `validate.py --local` gera.

Edite cada bloco com substituições exatas (Edit) do conteúdo de dentro do bloco. Não monte o arquivo recortando por busca de texto de tags: o comentário do topo e o motor têm textos parecidos, e um corte errado deixa a página em branco sem erro no console.

## 2. `btp-data`

```json
{
  "projeto": {
    "nome": "Hub Financeiro Aurora",
    "cliente": "Clínica Aurora",
    "tipo": "refatoracao",                 // "novo" | "refatoracao"
    "versao": 1,
    "geradoEm": "2026-10-27",
    "dominio": "hub.clinicaaurora.com.br",     // aparece na barra da moldura
    "resumo": "Uma ou duas frases: o que é o sistema, o que esta prévia cobre e de quais fontes saiu.",
    "historico": [ { "versao": 1, "data": "2026-10-27", "nota": "Primeira versão, a partir da call de 21/10 e do TO BE V2." } ]
  },
  "fontes": [
    { "id": "R1", "tipo": "reuniao",   "titulo": "Call Módulo Financeiro", "data": "2026-10-21", "detalhe": "Anotações do Gemini e gravação (28 min)", "link": "https://docs.google.com/..." },
    { "id": "A1", "tipo": "documento", "titulo": "TO BE V2", "data": "2026-10-19", "detalhe": "Critérios CA-01 a CA-15", "link": "..." },
    { "id": "V1", "tipo": "design",    "titulo": "Tema do Hub", "detalhe": "src/index.css", "link": "..." }
  ],
  "telas": [
    { "id": "T01", "nome": "Conciliação", "rota": "/conciliacao", "grupo": "Operação",
      "dispositivo": "desktop",               // "desktop" | "mobile"
      "larguraMinima": 1024,                   // opcional: px mínimos antes de rolar na moldura
      "ajustar": true,                         // opcional: desenha em larguraMinima e encolhe para caber (sistema existente)
      "objetivo": "Uma frase com o trabalho que a pessoa faz nesta tela.",
      "decisoes": ["D1"],                      // decisões que fazem a TELA existir (tracejado na moldura inteira)
      "hoje": [ { "img": "img/t01-hoje.jpg", "legenda": "Produção, mostrada na call", "fonte": "R1", "ref": "14:53" } ],
      "depois": [ { "img": "depois/t01.png" } ], // print da prévia (teste.html#so-T01); com hoje, cria a aba "Antes e depois"
      "hojeAviso": "opcional: por que não há imagem do sistema atual (aparece sob o objetivo)" }
  ],
  // Só quando telas mudam de lugar, se juntam, se dividem ou saem (seção 2.1):
  "telasAtuais": [ { "nome": "Conciliação", "local": "Menu" }, { "nome": "Relatórios", "local": "Menu", "igual": true } ],
  "removidas": [ { "id": "X1", "nome": "Alertas", "local": "Menu › Alertas", "rota": "/alertas",
      "hoje": [ { "img": "hoje/x1-alertas.png", "fonte": "V1" } ],
      "destino": "Para onde vai o que ela fazia (aceita **negrito**).", "para": ["T01"] } ],
  "decisoes": [
    { "id": "D1", "tipo": "reuniao", "titulo": "Frase curta com o que foi decidido",
      "mudanca": "altera",                     // opcional, em sistema existente: "altera" | "nova" | "remove"
      "telas": ["T01"],                        // fichas em que o card aparece
      "explicacao": "O que a prévia faz por causa disso. Aceita **negrito** e `código`.",
      "trechos": [ { "fonte": "R1", "ref": "14:53", "quem": "Lucas", "texto": "Transferência de contas da própria empresa não é receita ou despesa.", "link": "opcional, sobrepõe o link da fonte" } ],
      "novo": true },                          // só em atualizações: decisão nova ou mudada nesta versão
    { "id": "D9", "tipo": "aberto", "titulo": "...", "telas": ["T03"], "explicacao": "...",
      "pergunta": "Pergunta fechada, que dá para responder numa reunião.",
      "recomendacao": "O que a prévia assumiu e por quê.", "quemDecide": "Cliente",
      "trechos": [] }
  ]
}
```

Os comentários `//` acima só explicam os campos; no arquivo, o JSON não pode ter comentários.

Regras que o validador confere:
- Ids: telas `T01`, `T02`...; decisões `D1`, `D2`...; fontes `R`/`A`/`V` + número. Numere decisões na ordem em que aparecem nas telas, para os badges lerem em sequência.
- `reuniao`, `documento` e `referencia` precisam de pelo menos um trecho. Sem trecho, é `inferencia`.
- `inferencia` precisa de `explicacao` dizendo por que foi proposta.
- `aberto` precisa de `pergunta`.
- Toda decisão aparece marcada em algum lugar (`data-d` ou `telas[].decisoes`).
- Toda tela tem pelo menos uma decisão que a justifique.
- Imagens são arquivos locais (caminho relativo ao `preview.html`: `img/`, `hoje/`, `depois/`); o `validate.py --out` embute todas na versão de publicação. URL externa não carrega no artefato. Vídeo não entra: pesa demais na página, e o validador recusa.
- `mudanca`, quando houver, é `altera`, `nova` ou `remove`.
- O motor tem um modo de captura: `teste.html#so-T01` mostra só a tela T01, sem marcações e sem moldura, na largura da janela. É dele que saem os prints de `depois`.

### 2.1 Reorganização: telas que mudam de lugar, se juntam, se dividem ou saem

Quando o pedido mexe na estrutura de telas, e não só dentro delas, a prévia ganha um **Mapa das telas** no início (hoje à esquerda, como vai ficar à direita, uma seta com o tipo de mudança e a decisão que pediu), uma linha de origem no topo de cada ficha e uma ficha curta para cada tela que sai. Os campos:

| Campo | Onde | O que faz |
|---|---|---|
| `situacao` | tela | `nova` (não existe hoje), `ajustada` (padrão quando há `hoje`: muda só por dentro), `movida` (muda de lugar no menu ou de endereço), `mesclada` (junta duas ou mais telas de hoje), `dividida` (uma tela de hoje vira várias). |
| `local` | tela | Onde a tela fica na navegação nova (`"Atendimento › Pacientes"`). Sem ele, o motor usa `grupo › nome`. |
| `hoje[].tela`, `hoje[].local` | tela | De qual tela de hoje vem aquele print, e onde ela fica hoje. É o que liga as telas no mapa: uma `mesclada` tem prints de duas ou mais telas; as telas de uma `dividida` citam a mesma tela de origem (com o mesmo `local`). |
| `depois[i]` | tela | Na aba Antes e depois, o print `hoje[i]` se compara com `depois[i]` (ou com `depois[0]`, se faltar). Com mais de um print de hoje, aparece "Comparar com" para escolher. Numa `mesclada`, ponha os prints de depois na mesma ordem dos de hoje (ex.: aba Saldos ↔ Movimentações, aba Histórico ↔ Auditoria). |
| `decisoes` | tela | A decisão que pediu a mudança de estrutura. Aparece no badge da linha do mapa. |
| `removidas[]` | raiz | Telas que saem do sistema, com ids `X1`, `X2`... Cada uma tem `nome`, `local`, `rota`, `hoje` (o print de como é hoje) ou `hojeAviso`, `destino` (texto) e `para` (ids das telas que herdam o que ela fazia). A decisão que a tira cita o id em `telas` (`"telas": ["X1"]`, com `"mudanca": "remove"`), e o card aparece na ficha dela. |
| `telasAtuais[]` | raiz | O menu de hoje, para conferir se nenhuma tela some sem explicação. Cada item é um nome (`"Cadastros"`) ou `{ "nome", "local", "igual": true }`. As que não aparecem em nenhum `hoje[].tela` nem em `removidas` entram no mapa como "continua igual" (com `igual: true`) ou "fora desta prévia" (sem), e o validador avisa. |

O validador também confere: `mesclada` com pelo menos duas telas de origem; `movida` e `dividida` com `hoje[].tela`; `dividida` sem outra tela vinda da mesma origem (talvez seja `movida`); tela removida sem decisão que a cite (erro); e reorganização sem `telasAtuais` (aviso).

## 3. Telas

Cada tela é um `<template data-screen="T01">` com uma raiz `.app` (ou `.app no-side` sem menu lateral). O motor monta o template duas vezes, no modo Documento e no modo Protótipo. Por isso:
- **Não use `id=""`** dentro do template. Use `data-*` e, no JS, `root.querySelector`.
- O menu lateral (e qualquer outro trecho repetido) fica uma vez só, num `<template data-shared="menu">` com os itens marcados por `data-item="conciliacao"`. Cada tela usa `<div data-use="menu" data-active="conciliacao"></div>`, e o item correspondente ganha `class="on"`. Itens fora do escopo levam `data-toast="Fora do escopo desta prévia"`. Marcações `data-d` dentro do trecho compartilhado aparecem em todas as telas que o usam.
- Mostre o estado mais informativo da tela (lista com dados, não vazia). Estados alternativos (vazio, erro, sucesso) entram como painel acionável ou como aba interna.

## 4. Marcações `data-d`

`data-d="D3"` em qualquer elemento: o motor desenha o tracejado na cor do tipo e um badge clicável no canto superior direito. Vários ids separados por espaço (`data-d="D3 D7"`) geram vários badges.

- Marque o menor elemento que a decisão justifica: o botão, a coluna (`<th>` ou a célula exemplo), o card, o grupo de filtros. Marcar a `.app-main` inteira não diz nada.
- A decisão que faz a tela existir vai em `telas[].decisoes`, não num `data-d` da raiz.
- Elementos dentro de modais e gavetas também podem ser marcados; o badge aparece quando o painel abre.
- Em linhas de tabela, marque uma célula de exemplo, não todas.

Quem lê clica no badge e vai para o card da decisão; passa o mouse no card e o elemento acende na prévia. No modo Protótipo, o badge abre um balão com a decisão.

## 5. Interações sem JavaScript

O motor trata estes atributos dentro de cada tela:

| Atributo | Efeito |
|---|---|
| `data-goto="T02"` | Vai para outra tela (rola até a ficha no Documento; troca a tela no Protótipo). Em `<tr>`, a linha fica clicável e focável. |
| `data-goto-state="pendentes"` (junto com `data-goto`) | A tela de destino recebe o evento `btp:enter` com `e.detail.state === "pendentes"`; trate em `btpInit` (ex.: abrir já filtrada). |
| `data-open="nome"` + `data-panel="nome" hidden` | Abre/fecha o painel (modal `.app-overlay > .app-modal` ou `.app-drawer`). Clique no fundo e Esc fecham. |
| `data-close` | Fecha o painel em que está. |
| `data-tabs` com botões `data-tab="x"` (+ `aria-selected`) e irmãos `data-tabpane="x"` | Abas. Os painéis ficam no mesmo pai do grupo de abas. |
| `data-pick` dentro de `data-pick-group` | Seleção única (chips, segmentos): o clicado ganha `.on-pick`. |
| `data-toast="texto"` | Mostra um aviso no canto da prévia. |
| `<form data-toast-submit="texto">` | Submit não envia nada; fecha o painel e mostra o aviso. |

## 6. `app-js`

Para filtros que filtram, cálculo ao vivo, busca com sugestões, calendário etc.:

```js
window.btpInit = window.btpInit || {};
btpInit.T01 = (root, api) => {
  const sel = root.querySelector('[data-filter="status"]');
  sel.addEventListener("change", () => {
    root.querySelectorAll("tbody tr[data-status]").forEach(tr => { tr.hidden = !!sel.value && tr.dataset.status !== sel.value; });
  });
};
```

`api.goto(id, estado)`, `api.toast(texto)`, `api.view` (`"doc"` ou `"proto"`). Para reagir a uma chegada com estado: `root.addEventListener("btp:enter", e => { ... e.detail.state ... })`. A função roda uma vez por montagem. Use `el.hidden` para mostrar/esconder (o motor reposiciona os badges sozinho). Sem bibliotecas externas na prévia; se uma for indispensável (gráfico complexo), carregue de `cdnjs.cloudflare.com` com versão exata.

## 7. Kit `.app-*`

Classes prontas no `btp-shell`, todas desenhadas só com tokens `--app-*`:

- Estrutura: `.app` (grade menu + conteúdo), `.app.no-side`, `.app-side`, `.app-brand`, `.app-nav` (`.lbl`, `a.on`), `.app-main`, `.app-top`, `.app-row`, `.app-stack`, `.app-grid`.
- Texto: `.app-h` (título da página, use `<h4>`), `.app-sub`.
- Controles: `.app-btn` (`.pri`, `.ghost`, `.danger`), `.app-field` (label que envolve o controle), `.app-input`, `.app-select`, `.app-tabs`.
- Dados: `.app-card` (`> .hd`), `.app-kpi` (`.k`, `.v`, `.s`), `.app-table-wrap > .app-table` (`.num`), `.app-pill` (`.ok`, `.warn`, `.bad`, `.info`), `.app-empty`, `.app-alert`.
- Camadas: `.app-overlay > .app-modal` (`> .hd`), `.app-drawer`.

O que o kit não tiver vai para `app-css`, com classes prefixadas pelo projeto (`.hf-dre-row`) e só tokens `--app-*` ou cores do próprio cliente.

## 8. `app-theme`

Preencha com o design system do cliente. Para usar a fonte do cliente do Google Fonts, ponha `@import url("https://fonts.googleapis.com/css2?family=...&display=swap");` como primeira linha do bloco `app-theme` e use-a em `--app-font`, sempre com fontes de reserva. Fontes que não estejam no Google Fonts: use a mais próxima e anote na fonte `V` correspondente. A prévia não muda com o tema claro/escuro da página, porque representa o produto. Se o produto tiver modo escuro, escolha o modo que o cliente usa no dia a dia.

Logotipo: se houver arquivo, copie para `WORK/img/logo.png` e use `<img src="img/logo.png">` em `.app-brand`; senão, o nome em texto.

## 9. Escrita

- Português do Brasil, frases curtas, voz ativa, termos que o cliente usa (os da reunião, não os do código).
- `titulo` da decisão diz o que muda ("Filtros sobem para o topo, ao lado de Exportar"), não o tema ("Filtros").
- `explicacao` diz o efeito na prévia e, se houver, o motivo de negócio. Paráfrase aqui; aspas só nos trechos.
- `objetivo` da tela é o trabalho da pessoa, não a lista de componentes.
- Nada de jargão interno de ferramenta ("btp", "template", "data-d") no texto que o leitor vê.

## 10. Checklist antes de publicar

- [ ] `validate.py` sem erros; avisos lidos.
- [ ] Toda tela tem decisão de tela ou marcações; toda decisão aparece em alguma tela.
- [ ] Inferências estão marcadas como tal; dúvidas reais viraram `aberto` com pergunta.
- [ ] Trechos literais, com `ref` que permite achar o original.
- [ ] Menu, links e linhas navegam; modais abrem e fecham; filtros filtram.
- [ ] Dados fictícios, sem dado pessoal real.
- [ ] Em refatoração, cada tela tem "Como está hoje" ou `hojeAviso` dizendo por que não tem.
- [ ] Em sistema existente, só o que muda tem `data-d`, cada mudança tem `mudanca`, e `hoje`/`depois` foram capturados na mesma largura.
- [ ] Se telas mudam de lugar, se juntam, se dividem ou saem: `situacao` em cada tela, `hoje[].tela` nas origens, `removidas` com a decisão que as tira e `telasAtuais` com o menu de hoje, sem tela atual sem destino.
