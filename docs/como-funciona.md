# Como a btime-preview funciona por dentro

O valor da skill está na **rastreabilidade**. Uma prévia bonita sem fonte vira opinião; com o trecho e o horário da reunião, vira um acordo verificável. Por isso o trabalho pesado é coletar e citar bem, e o artefato sai de um template fixo para ficar sempre igual de um projeto para outro.

## Visão geral do fluxo

```text
0. Ambiente        conectores Google, Python, ffmpeg/Node quando precisar
1. Delimitar       qual projeto, novo ou existente, quais telas
2. Coletar         reuniões + reuniões vizinhas + documentos + visual  ->  WORK/insumos.md
3. Vídeo           só quando a fala aponta para a tela (com permissão)
4. Decisões        D1..Dn com tipo, trecho literal e explicação
5. Montar          template.html + partes/  ->  preview.html
6. Validar         validate.py  ->  publicar.html (imagens embutidas) + teste.html
7. Publicar        Artifact privado; state.json guarda o link
8. Entregar        link, contagem de decisões e perguntas em aberto na conversa
```

## 1. Delimitar o projeto

As pastas de empresa no Drive costumam ter vários projetos. A skill trabalha só no que foi pedido e escolhe sozinha quando o nome da reunião aponta claramente para uma pasta. Ela pergunta numa única rodada, e só o que bloqueia.

São três casos:

| Caso | De onde sai a tela | Abas por tela |
|---|---|---|
| Projeto novo | mockup, TO BE, design system | Como vai ficar |
| Refatoração | documentos + sistema atual como referência | Como vai ficar, Como está hoje |
| Ajustes num sistema que já roda | o próprio sistema, capturado localmente | Como vai ficar, Como está hoje, Antes e depois |

## 2. Coleta

O inventário vai para `WORK/insumos.md`, com um id por fonte: `R` reunião, `A` arquivo ou documento, `V` visual. Os ids `D` ficam reservados para as decisões.

- **Reunião.** A skill acha o evento na Agenda (`search_events`), e nos anexos estão as Anotações do Gemini (resumo e transcrição com horários) e a gravação. Se a Agenda falhar ou estourar a cota, ela busca no Drive pelo padrão de nome do Meet.
- **Reuniões vizinhas.** Ela procura também as reuniões posteriores do mesmo projeto, porque alinhamentos dos dias seguintes costumam mudar o que foi combinado. Quando duas fontes discordam, vale a mais recente, e a decisão cita as duas.
- **Documentos.** `read_file_content` lê Docs, PDF, DOCX, planilhas e apresentações.
- **Visual.** Tokens de cor, fonte, raio e densidade saem do design system, do projeto de exemplo ou do código do sistema atual (`index.css`, `tailwind.config`, tema e rotas).

A skill **não transcreve áudio**. Se faltar a transcrição de uma reunião importante, ela pede ao usuário que a coloque na pasta do projeto.

## 3. Vídeo, só quando acrescenta algo

A transcrição não mostra a tela. A gravação entra quando a call percorre o sistema atual ou quando a fala aponta para algo visual ("esse filtro aqui").

1. A skill pede permissão dizendo o nome, o tamanho e o destino do arquivo.
2. Baixa pelo Chrome do usuário; nunca por `download_file_content`, que devolve base64 e estoura o contexto.
3. `frames.py` monta folhas de quadros por horário ou por troca de tela, e com elas ela alinha cada bloco da transcrição à tela que estava aberta.

O vídeo serve para entender o pedido e não entra no artefato.

## 4. Decisões

Antes de desenhar, a skill escreve a lista de decisões. Cada uma tem:

- `tipo`: `reuniao`, `documento`, `referencia`, `inferencia` ou `aberto`;
- `trechos`: cópia literal com a referência que permite achar o original (`14:53`, `RN-07`, página);
- `explicacao`: uma ou duas frases na linguagem de quem aprova;
- em sistema existente, `mudanca`: `altera`, `nova` ou `remove`. Só o que muda é marcado.

O que a skill completou por bom senso é `inferencia`, com a justificativa. As dúvidas reais viram `aberto`, com pergunta, recomendação e quem decide, e aparecem só no card da decisão. A lista de perguntas vai na conversa, não no documento.

## 5. O template e o motor

`assets/template.html` tem blocos fixos e blocos editáveis:

```text
<title>                     EDITAR   nome da prévia (2 a 4 palavras)
<style id="btp-shell">      FIXO     visual da página, legenda, cards, kit .app-*
<style id="app-theme">      EDITAR   tokens --app-* do design system do cliente
<style id="app-css">        EDITAR   componentes que o kit não cobre
<script id="btp-data">      EDITAR   projeto, fontes, telas, decisões (JSON)
<template data-screen>      EDITAR   uma por tela, HTML com data-d="D4" nos elementos
<template data-shared>      EDITAR   partes repetidas (menu lateral, cabeçalho)
<script id="app-js">        EDITAR   interações específicas
<script id="btp-engine">    FIXO     motor
```

O motor (versão 2) cuida de:

- tracejado na cor do tipo e badge clicável em cada `data-d`;
- cards de decisão com o trecho da fonte, a explicação e os chips de mudança;
- modo **Documento** (telas e decisões em sequência) e modo **Protótipo** (navegação por `data-goto`, abas `data-tabs`, janelas `data-open`/`data-panel`, filtros, avisos de formulário);
- abas **Como vai ficar**, **Como está hoje** e **Antes e depois**, esta com um comparador deslizante sobre duas imagens;
- `larguraMinima` + `ajustar`: a tela é desenhada na largura real (ex.: 1366 px) e encolhe com zoom para caber na moldura, como um print, sem o sistema trocar de layout;
- modo de captura `#so-T01`: mostra só a tela, sem marcações, para tirar o print de "como vai ficar";
- tema claro e escuro da página, com a prévia sempre no tema do produto.

Em prévias grandes, cada bloco fica num arquivo em `WORK/partes/` (`titulo.txt`, `tema.css`, `app.css`, `data.json`, `telas.html`, `app.js`), e `assemble.py` monta o `preview.html` sem tocar no motor.

## 6. Sistema existente: a prévia sai do próprio sistema

Detalhado em [`references/existente.md`](../references/existente.md):

1. **Rodar localmente.** Sem perguntar, a skill pode rodar `npm run dev` e entrar com as contas de teste que o projeto documenta, em `localhost`. Pede permissão antes de `npm install`, de subir containers, de recriar o banco ou de editar `.env.local`. Nunca usa credencial de produção. Se o `.env.local` não bate com o ambiente, ela passa as variáveis só para o processo e avisa.
2. **Capturar** com `capturar.mjs`, que controla um Chrome sem janela pelo protocolo DevTools, usando o WebSocket nativo do Node 22+. Um roteiro JSON faz login, visita cada tela e salva o `print` (como está hoje), o `html` (a marcação real, com as classes do `<html>`/`<body>` anotadas) e o `css` (todo o CSSOM aplicado).
3. **Prender o CSS** com `escopo_css.py`:
   - prefixa todos os seletores com `.app-real` e troca `:root`, `html` e `body` pelo escopo;
   - converte `position: fixed` em `absolute` e as unidades `vh` em `var(--btp-vh)`;
   - remove `@font-face`; as fontes vêm do Google Fonts.

   O `app.css` final é `sistema.css` seguido de `ajustes.css`, que contém só o que muda.
4. **Montar as telas** com um `montar_telas.py` do projeto. Ele limpa ids, links internos e comentários do React, extrai o menu como parte compartilhada, aplica só as mudanças pedidas sobre a marcação real e põe `data-d` no elemento mudado.
5. **Gerar o "depois"**: o mesmo roteiro aponta para `teste.html#so-Txx`, na mesma largura e no mesmo estado do print de hoje (janela aberta, por exemplo). Com `hoje` e `depois` preenchidos, aparece a aba Antes e depois.
6. **Medir em vez de adivinhar.** Um passo `js` devolve `scrollWidth` contra `clientWidth`. Foi assim que a skill descobriu que uma tabela ficava 55 px mais larga que 1366, e essa consequência virou uma decisão `aberto`.

No fim, a skill encerra o servidor que subiu e informa o que mudou no ambiente.

## 7. Validação e publicação

`validate.py WORK/preview.html --out WORK/publicar.html --local WORK/teste.html`:

- confere se o motor está inteiro e na versão atual, e avisa quando a prévia é antiga (`upgrade_engine.py` troca só o motor);
- cruza ids de telas, decisões e fontes, além de tipos, trechos, marcações `data-d`, destinos de navegação e imagens;
- recusa vídeo;
- só grava as cópias se não houver erro: `publicar.html` com as imagens de `img/` embutidas em base64 e `teste.html` para conferência local.

Depois, a skill tira um print do `teste.html` com o Chrome sem janela, corrige o que aparecer e publica com a ferramenta Artifact, com o ícone `layout`, em modo privado. O `state.json` guarda o projeto, o link, a versão e o `modifiedTime` de cada fonte.

## 8. Atualização

Com `state.json` existente, ou um link de artefato passado pelo usuário, o pedido é tratado como atualização:

1. lê o artefato publicado e usa essa versão como base (alguém pode ter mexido);
2. coleta só as fontes novas ou alteradas, e lê também os comentários do artefato;
3. aumenta a versão, acrescenta uma linha ao histórico, marca as decisões novas ou mudadas com `novo` e registra quais decisões substituem quais;
4. valida e publica no mesmo link.

## Lições que viraram regra

| Problema encontrado | Regra na skill |
|---|---|
| React apagava o texto digitado antes da hidratação | esperar ~3 s depois do campo aparecer |
| Navegar só mudando o `#` não recarregava a página | `capturar.mjs` passa por `about:blank` antes |
| A moldura de ~1200 px fazia a tabela virar cartões | `larguraMinima: 1366` + `ajustar` |
| Painel de abas fora do bloco das abas não trocava | o motor sobe no DOM para achar os `data-tabpane` |
| Cabeçalho em grid encolhia para o conteúdo | `grid-template-columns: minmax(0, 1fr)` |
| Vídeo deixava o artefato pesado demais | artefato só com imagens; o validador recusa vídeo |
| `\b` dentro de heredoc virava caractere invisível | cuidado com caracteres de controle em scripts gerados |
| No Windows, `python` é atalho da Microsoft Store | usar `py -3` e caminhos `C:/...` |
