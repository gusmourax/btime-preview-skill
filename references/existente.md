# Projeto existente: ajustes num sistema que já roda

Use este caminho quando o sistema já existe, o código está disponível (pasta local ou repositório) e o pedido é mudar telas que já estão no ar. Aqui não há mockup: a prévia sai do próprio sistema. A tela é o HTML real, com o CSS real, e só o que foi pedido muda. Cada tela mostra três coisas: **como vai ficar** (interativo), **como está hoje** (print do sistema) e **antes e depois** (linha deslizante sobre os dois prints). O artefato não leva vídeo: pesa demais na página. O comportamento novo se vê clicando na prévia.

## Sumário
1. Ler o pedido e a gravação
2. Rodar o sistema localmente
3. Capturar o "como está hoje" (capturar.mjs)
4. Prender o CSS do sistema na prévia (escopo_css.py)
5. Montar as telas da versão nova a partir do HTML capturado
6. Decisões: marcar só o que muda
7. Gerar o "como vai ficar" e conferir
   7.1 Quando telas mudam de lugar, se juntam, se dividem ou saem
8. Tamanho, privacidade e cuidados

## 1. Ler o pedido e a gravação

Nesses pedidos a fala quase sempre aponta para a tela ("esses filtros aqui", "isso aqui pode sumir"), então a gravação é necessária para saber de qual elemento se fala. Peça permissão para baixar (references/video.md), monte uma folha de quadros a cada 3 ou 4 segundos e alinhe cada bloco da transcrição com a tela que estava aberta:

```bash
ffmpeg -v error -i WORK/video/gravacao.mp4 -vf "fps=1/4,scale=640:-1,drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6:fontfile='C\:/Windows/Fonts/arial.ttf',tile=3x4" -fps_mode vfr WORK/folhas/folha-%02d.jpg
```

Os horários dos blocos da transcrição marcam o começo da fala; um bloco longo pode percorrer várias telas. Anote, para cada pedido, a tela, o elemento e o horário.

A gravação costuma mostrar produção, com nomes, e-mails e valores reais. Ela serve para entender o pedido, não para ilustrar a prévia: o "como está hoje" sai do sistema rodando com dados de teste (passo 3). Só use quadro da gravação quando não houver como rodar o sistema, e aí corte ou borre os dados pessoais.

## 2. Rodar o sistema localmente

Leia o README e o que ele aponta (`.env.example`, scripts de seed, contas de teste). Em geral:
- **O que pode sem perguntar:** ler o projeto, rodar o servidor de desenvolvimento (`npm run dev`) quando as dependências já estão instaladas, entrar com as contas de teste que o próprio projeto documenta (seed, README, fixtures) em `localhost`.
- **O que pede permissão antes:** instalar dependências (`npm install`), subir containers (`supabase start`, `docker compose up`), qualquer comando que apague ou recrie dados (`supabase db reset`, migrations), e mexer em arquivos do projeto (inclusive `.env.local`).
- **O que nunca fazer:** entrar em produção ou staging com credencial real, ou usar senha que não seja de teste.

Se o `.env.local` não bate com o ambiente que está rodando (porta, chave), não edite o arquivo: suba o servidor com as variáveis certas só no processo, por exemplo `eval "$(supabase status -o env | grep -E '^(API_URL|ANON_KEY|SERVICE_ROLE_KEY)=')"` e `NEXT_PUBLIC_SUPABASE_URL=$API_URL ... npm run dev`. Avise o usuário da divergência. Se você subiu o servidor, encerre-o no fim (pare a tarefa e confira se o processo `node` filho também saiu).

Se não der para rodar (sem banco, sem seed, sem acesso), use prints que o usuário mandar ou quadros da gravação tratados, e monte as telas lendo os componentes no código. A prévia perde fidelidade; diga isso na entrega.

## 3. Capturar o "como está hoje" (capturar.mjs)

`scripts/capturar.mjs` controla um Chrome sem janela por um roteiro JSON (`node capturar.mjs ROTEIRO.json --saida WORK`; leia o cabeçalho do script para todos os passos). Num roteiro só, faça login, visite cada tela e salve:
- `print`: o print da tela (vai em `tela.hoje[].img`);
- `html` com `"seletor": ".casca"` (ou o contêiner raiz do app) e `"body"` quando houver janela aberta: a marcação real, sem scripts, com um comentário `<!-- raiz: ... -->` no topo listando as classes do `<html>`/`<body>` (fontes do next/font, tema);
- `css` uma vez: todo o CSS aplicado (CSSOM).

Quando a mudança é de comportamento (uma janela que abre, uma ordem que muda), tire o print no estado que importa: clique antes (`clicar`) e depois faça o `print` com a janela aberta.

Regras práticas:
- Use a largura de tela em que o problema aparece. Títulos que quebram, filtros que pulam de linha e tabelas que viram cartões dependem da largura; 1366 × 800 (notebook) costuma ser a referência. Grave o "como vai ficar" na mesma largura, senão a comparação engana.
- Senha nunca vai escrita no roteiro: use `${ENV:BTP_SENHA}` e passe a variável na linha de comando a partir do arquivo do projeto onde ela está documentada; não repita o valor na conversa.
- Espere a hidratação antes de digitar (`{ "esperar": 3000 }` depois do campo aparecer), senão o React apaga o que foi digitado.
- `"ocultar": ["nextjs-portal"]` esconde o selo de desenvolvimento do Next em todas as páginas.
- Mantenha o roteiro em `WORK/roteiros/` para refazer as capturas numa atualização.

## 4. Prender o CSS do sistema na prévia (escopo_css.py)

```bash
PY SKILL_DIR/scripts/escopo_css.py WORK/dom/app.css --out WORK/partes/sistema.css --raiz "<classes do comentário raiz>"
```

O script prefixa tudo com `.app-real`, troca `:root/html/body` pelo escopo, transforma `position: fixed` em `absolute` e `vh` em `var(--btp-vh)` (8 px = uma tela de 800 px), tira `@font-face` e mantém `@media`/`@keyframes`. Carregue as fontes do sistema pelo Google Fonts no `app-theme` (Inter, Sora, DM Mono...). O `app.css` final é `sistema.css` seguido de um `ajustes.css` só com o que muda; assim fica claro, no próprio arquivo, o que é a versão nova.

## 5. Montar as telas da versão nova a partir do HTML capturado

Escreva um `WORK/montar_telas.py` do projeto que lê `dom/*.html` e grava `partes/telas.html`. Ele deve:
- **limpar**: comentários do React, `id`/`for`/`aria-labelledby`/`aria-controls` (os templates são montados duas vezes, no documento e no protótipo), atributos com ids do banco, `href` internos (viram `#`), e caminhos de imagem (copie para `WORK/img/`);
- **extrair o menu** (`<aside>`) para um `<template data-shared="menu">`, com `data-item` em cada link, `data-goto` nos que levam a telas da prévia e sem as `<dialog>` fechadas;
- **montar cada tela** como `<div class="app-real"><div class="casca"><div data-use="menu" data-active="..."></div><div class="principal"><main>...</main></div></div></div>`, reaproveitando o `<main>` capturado;
- **aplicar só as mudanças pedidas**, com substituições sobre a marcação real (mover um bloco, tirar um cartão, trocar a ordem das linhas), e pôr `data-d` no elemento mudado;
- **janelas abertas**: a `<dialog open>` capturada vai dentro de `<div class="cx-sobre" data-panel="nome">`, uma camada absoluta com fundo escuro; a janela fica centrada na primeira tela (`top: calc(50 * var(--btp-vh))`), como no sistema.

No `app-js`: marcar `aria-current` no item ativo do menu (`[data-item].on`), impedir que `a[href="#"]` role a página, fazer busca e filtros filtrarem as linhas, ordenar ao clicar no título da coluna quando a mudança é de ordem, e reabrir a janela no evento `btp:enter` (quando a pessoa volta à tela pelo menu).

Em `btp-data`, cada tela leva `"larguraMinima": 1366, "ajustar": true`: a tela é desenhada na largura da captura e encolhe para caber na moldura, como um print. Sem isso, a moldura do documento (cerca de 1200 px) faz o sistema trocar de layout (tabelas viram cartões, filtros quebram) e a prévia mostra outra coisa.

## 6. Decisões: marcar só o que muda

- Cada pedido da call é uma decisão `reuniao` com `"mudanca": "altera" | "nova" | "remove"`. O card mostra "muda", "novo na tela" ou "sai da tela".
- O que continua igual não recebe marcação. Num sistema existente, marcar tudo esconde o que de fato muda.
- Consequências que você precisou decidir (tirar um título que ficou sem sentido, encurtar um rótulo para caber) são `inferencia` ou `aberto`, com o motivo medido ("a tabela fica 55 px mais larga que 1366 px").
- Uma fala ambígua ("já venha filtrado") vira `aberto` com a suposição que a prévia aplicou.
- Quando o comportamento atual está no código (ordenação, regra), cite o trecho do arquivo como fonte `A` (`ref` = caminho do arquivo). É o "antes" escrito.
- Fontes típicas: R1 transcrição, R2 gravação (sem citação, só para localizar as telas), A1 código (commit), V1 sistema local com dados de teste (prints).

## 7. Gerar o "como vai ficar" e conferir

1. Monte (`assemble.py`) e valide (`validate.py --local WORK/teste.html`).
2. O motor tem um modo de captura: `teste.html#so-T01` mostra só a tela T01, sem marcações, na largura da janela. Com um segundo roteiro (`roteiros/captura-depois.json`), tire o print de cada tela, no mesmo estado do print de hoje (mesma janela aberta, mesma largura), em `depois/`.
3. Ponha em cada tela `"depois": [ { "img": "depois/t01.png" } ]`. Com `hoje` e `depois` preenchidos aparece a aba **Antes e depois**.
4. Monte e valide de novo. Olhe pelo menos: uma tela no modo documento (encolhida), uma no protótipo (menu, abas, janelas) e a aba Antes e depois. Meça o que parece apertado com um passo `js` (`scrollWidth` contra `clientWidth`) em vez de adivinhar.

## 7.1 Quando telas mudam de lugar, se juntam, se dividem ou saem

Nem todo pedido fica dentro de uma tela. "Essa auditoria podia ficar dentro de movimentações", "cadastros está grande demais, separa os itens", "alertas pode sair, o sino já resolve" mudam a estrutura do sistema, e a prévia precisa mostrar o que foi para onde, não só como cada tela ficou.

1. **Capture o menu de hoje** e liste as telas atuais em `telasAtuais` (nome e local). É o que permite ao validador apontar uma tela que sumiu sem explicação.
2. **Classifique cada tela da versão nova** com `situacao`: `mesclada`, `dividida`, `movida`, `nova` ou `ajustada` (padrão). Em cada print de `hoje`, diga de qual tela ele é (`tela`) e onde ela fica (`local`).
3. **Capture o "hoje" de todas as telas de origem**: numa mescla, um print de cada tela que se junta; numa divisão, o print da tela original no estado que interessa (a aba que vira tela própria, por exemplo).
4. **Monte as telas novas a partir da marcação real**: uma tela mesclada costuma ser a principal com abas, em que cada aba reaproveita o `<main>` de uma tela de hoje (sem o título dela); uma dividida é a tela original sem as abas que saíram. O menu compartilhado muda junto: itens que saem, itens novos, grupos novos. Se um item do menu só existe em uma tela (a marcação do grupo novo, por exemplo), use um segundo `data-shared` para não repetir o badge em todas.
5. **Tire os prints de depois na mesma ordem dos de hoje**, inclusive o de cada aba de uma tela mesclada (`clicar` na aba antes do `print`, no modo `#so-T01`).
6. **Telas que saem** vão em `removidas`, com o print de hoje, o `destino` (para onde vai o que ela fazia) e a decisão com `"mudanca": "remove"` citando o id `X1`.
7. Elementos que estavam presos à estrutura antiga mudam junto: filtros que ficavam no cabeçalho de uma tela agora com abas vão para dentro da aba certa; um botão que abria uma tela que saiu perde o destino. O validador acusa `data-goto` para tela inexistente.

O contrato completo dos campos está em `references/artefato.md`, seção 2.1.

## 8. Tamanho, privacidade e cuidados

- Só imagens: seis telas com print de hoje e de depois ficam em torno de 2,5 MB (PNG de 1366 × 800 tem 120 a 180 KB). O validador recusa vídeo.
- Dados nas telas: só os fictícios do ambiente local. Nada da gravação de produção entra na página.
- O `.cabecalho-pagina` e outros contêineres do sistema podem ser flex com `justify-content: space-between`; ao trocar para grid nos ajustes, ponha `grid-template-columns: minmax(0, 1fr)`, senão a coluna encolhe para o conteúdo.
- Abas cujo painel fica fora do bloco das abas funcionam: o motor procura os `data-tabpane` subindo a partir das abas.
- Ao final, encerre o servidor que você subiu e diga ao usuário o que ficou rodando ou foi alterado no ambiente.
