---
name: btime-preview
description: Gera um artefato com a prévia interativa das telas de um sistema (projeto novo ou refatoração) a partir dos insumos do projeto, com cada tela e componente marcados por um tracejado que aponta para a decisão que os justifica e o trecho original da fonte logo abaixo. Coleta sozinha reuniões do Google Agenda/Meet (Anotações do Gemini, transcrições, gravações em vídeo), documentos do Google Drive, design system, URL de projeto de exemplo, prints e o que mais o usuário mandar. Use sempre que o usuário quiser ver como as telas vão ficar, montar protótipo ou mockup a partir de reunião ou documentação, transformar call/kickoff/alinhamento em telas, validar escopo de telas com cliente, ou mencionar "btime-preview", "prévia das telas", "como vai ficar" — mesmo que não diga "artefato" nem "protótipo".
---

# btime-preview

Transforma o que foi conversado e documentado num projeto em uma página navegável: cada tela aparece como uma prévia clicável no visual do produto, e tudo o que existe na prévia está ligado, por um tracejado colorido, a uma decisão numerada com o trecho literal da reunião ou do documento que a pediu. Quem lê consegue, em segundos, ver a tela e conferir de onde ela veio.

O valor da skill está na rastreabilidade. Uma prévia bonita sem fonte vira opinião; com o trecho e o horário da call, vira um acordo verificável. Por isso o trabalho pesado é coletar e citar bem, e o artefato sai de um template fixo para ficar sempre igual de um projeto para outro.

Quem lê o documento é a liderança interna ou o cliente que pediu o sistema, para validar as telas. Por isso ele precisa ser claro e objetivo: a prévia e, abaixo dela, cada decisão com explicação curta e o trecho da fonte. Nada de pauta, lista de pendências ou anotações de trabalho no documento; isso fica na conversa com o usuário.

Caminhos usados abaixo:
- `SKILL_DIR` é a pasta desta skill (onde está este arquivo).
- `PY` é o Python: `py -3` no Windows (o comando `python` costuma ser um atalho quebrado da Microsoft Store), `python3` no macOS/Linux. No Windows, passe caminhos aos scripts no formato `C:/Users/...`, não `/c/Users/...`.
- `WORK` é a pasta de trabalho do projeto: `~/btime-preview/<slug-do-projeto>/`. Ela guarda insumos, quadros de vídeo, a prévia e o `state.json`, para que a próxima reunião atualize o mesmo artefato em vez de criar outro.

## Fluxo

### 0. Preparar o ambiente (uma vez por máquina, sem perguntar o que não precisa)

1. **Conectores do Google.** Carregue de uma vez com `ToolSearch` e `select:mcp__claude_ai_Google_Drive__search_files,mcp__claude_ai_Google_Drive__read_file_content,mcp__claude_ai_Google_Drive__get_file_metadata,mcp__claude_ai_Google_Calendar__search_events,mcp__claude_ai_Google_Calendar__get_event`. Se o prefixo for outro, procure os nomes na lista de ferramentas diferidas (busca por palavra-chave costuma não trazer essas ferramentas). Se não existirem, não há instalação possível pela máquina: diga ao usuário para conectar em claude.ai → Configurações → Conectores (Google Drive, Google Agenda, Gmail) e depois rodar `/mcp` aqui. Enquanto isso, siga com o que ele colar ou enviar.
2. **Ferramentas de vídeo e navegador.** Rode `PY SKILL_DIR/scripts/check_env.py` (código 0: quadros de vídeo prontos; 1: falta ffmpeg). Ele diz se ffmpeg/ffprobe (quadros da gravação da reunião), Node e Chrome/Edge (o `capturar.mjs`, que tira prints e o HTML das telas) estão disponíveis. Só instale quando um passo for de fato precisar de vídeo: aí peça permissão uma única vez, dizendo o que vai instalar (ex.: "ffmpeg via winget, ~100 MB"), e rode `check_env.py --install`. O vídeo serve só para ver as telas mostradas; `scripts/frames.py` extrai os quadros com ffmpeg, sem depender de outra skill.
3. **Transcrição.** A skill não transcreve áudio. O texto de toda reunião vem da transcrição que já está nos documentos do projeto (Anotações do Gemini, Transcript do Meet em .docx ou Google Doc). Se uma reunião importante não tiver transcrição nos documentos, diga ao usuário qual é e peça que ele a coloque na pasta do projeto; enquanto isso, siga com as outras fontes.

### 1. Entender o pedido e delimitar o projeto

Descubra, pelo que o usuário já disse e pelos insumos, antes de perguntar:
- **Qual projeto.** Pastas de empresa no Drive costumam ter vários projetos (ex.: "Módulo Financeiro", "Módulo Estoque", "Hub Financeiro"). Trabalhe só no projeto pedido. Se o usuário passou a pasta da empresa, liste as subpastas: quando o nome da reunião ou do pedido aponta claramente para uma ou mais pastas (um projeto e a evolução dele, por exemplo), use-as e diga quais usou; pergunte só se houver projetos diferentes concorrendo.
- **Projeto novo, refatoração ou ajustes num sistema existente.**
  - *Novo*: não há sistema; as telas saem do mockup, do design system e dos documentos.
  - *Refatoração*: o sistema vai ser refeito; cada tela ganha a aba "Como está hoje" (print, quadro da gravação ou captura) e as decisões descrevem o que muda.
  - *Existente com ajustes*: o sistema roda, o código está disponível e o pedido é mudar telas que já existem. Leia `references/existente.md`: a prévia sai do HTML e do CSS reais capturados do sistema rodando localmente, com o print de hoje, o print da versão nova e a aba "Antes e depois". O artefato usa só imagens: vídeo pesa demais na página. Use `"tipo": "refatoracao"` em `btp-data`. Se o pedido muda a estrutura (tela que muda de lugar, se junta com outra, se divide ou sai), a prévia ganha o Mapa das telas: veja a seção 7.1 de `references/existente.md`.
- **Quais telas e para quem.** Se a reunião deixou claro, siga; se não, proponha a lista de telas e confirme antes de desenhar.

Pergunte só o que bloqueia. Uma rodada curta de perguntas (com `AskUserQuestion`) é melhor que várias.

### 2. Coletar os insumos

Monte um inventário em `WORK/insumos.md`, uma linha por fonte, com id, tipo, título, data, link e o que foi lido. Prefixos de id: `R` reunião, `A` arquivo/documento, `V` visual (design system, projeto de exemplo, print, URL). As decisões usam `D`, então nunca use `D` para fonte.

Leia `references/coleta.md` para o passo a passo de cada origem. O essencial:
- **Reuniões.** Ache o evento na Agenda (`search_events` pelo nome e pela data). Os anexos do evento trazem as "Anotações do Gemini" (resumo, decisões, próximas etapas e a transcrição completa com horários) e a gravação. Leia o documento inteiro, incluindo a aba de transcrição: as citações saem de lá, com o horário do bloco.
- **Reuniões vizinhas.** Depois de achar a reunião pedida, procure as outras do mesmo projeto, principalmente as posteriores: alinhamentos e devolutivas dos dias seguintes costumam mudar o que foi combinado. Busque no Drive por palavras do título e do cliente, com `createdTime` a partir da data da reunião, e na pasta "Gravações & Transcrições" do projeto. Use as que forem do mesmo escopo e diga ao usuário quais entraram.
- **Documentos.** Liste a pasta do projeto no Drive e leia o que define escopo e regra: requisitos, TO BE/AS IS, documentação técnica, cronograma, atas. Docs, PDF, DOCX, planilhas e apresentações saem com `read_file_content`.
- **Visual.** Design system, Figma exportado, URL do projeto de exemplo, prints, código do sistema atual (em refatoração, `index.css`/`tailwind.config`/tema e o menu de rotas valem ouro). Extraia tokens: cores, fontes, raios, densidade, padrão de menu.
- **O que o usuário mandar direto** (arquivos, prints, texto colado) entra no inventário com o mesmo cuidado.

Quando duas fontes discordarem, vale a mais recente; registre na decisão que ela substitui a anterior e cite as duas.

### 3. Assistir ao vídeo quando ele acrescenta algo

A transcrição não mostra a tela. Assista à gravação quando: o projeto é refatoração e a call percorre o sistema atual; ou a fala aponta para algo visual ("esse botão aqui", "essa coluna sai"). O vídeo não substitui a transcrição: citações de fala saem sempre do documento de transcrição do projeto. Antes de baixar, peça permissão com nome, tamanho e destino do arquivo. O passo a passo (download pelo Chrome do usuário, quadros por horário ou por troca de tela, limpeza) está em `references/video.md`. Nunca use `download_file_content` do Drive para vídeo: ele devolve base64 e estoura o contexto.

### 4. Destilar as decisões

Antes de desenhar, escreva a lista de decisões. Cada decisão é algo que faz uma tela ou um componente existir ou ser de um jeito. Para cada uma:
- **tipo**: `reuniao` (decidido ou pedido em reunião), `documento` (regra escrita), `referencia` (vem do design system, do projeto de exemplo ou do sistema atual), `inferencia` (proposta sua, sem trecho que a peça) ou `aberto` (precisa de decisão; a prévia mostra uma suposição).
- **trechos**: cópia literal da fonte, com a referência que deixa achar o original (horário `14:53`, seção `RN-07`, página). Corte com `[...]`, mas não reescreva palavras dentro das aspas. Transcrição automática tem erros; cite como está e, se algo ficar ilegível, explique na decisão.
- **explicacao**: uma ou duas frases dizendo o que a prévia faz por causa disso, na linguagem de quem vai aprovar (sem siglas internas nem detalhes de implementação).

Seja honesto com os tipos. Tudo o que você completou por bom senso (estado vazio, campo extra, ordem de colunas) é `inferencia`, com a justificativa. Uma prévia em que tudo parece decidido engana quem vai aprovar. Dúvidas reais viram `aberto`, com pergunta, recomendação e quem decide; aparecem só no card da própria decisão, junto da tela que depende dela. O documento não tem seção de pontos em aberto.

### 5. Montar o artefato a partir do template

Copie `SKILL_DIR/assets/template.html` para `WORK/preview.html` e leia `references/artefato.md` antes de editar. O template já tem o motor (marcações, badges, cards de decisão, modo protótipo, fontes, tema claro/escuro) e já cumpre o contrato de página do Artifact (título, tokens, tema escuro, margens laterais). Se a ferramenta Artifact pedir `quickstart` ou a skill `artifact-design` antes de escrever o arquivo, faça, mas mantenha o template. Edite com substituições exatas dentro de cada bloco; o motor nunca é recortado nem reescrito. Você edita só:
1. `<title>`: nome do projeto em 2 a 4 palavras (ex.: "Prévia Hub Financeiro").
2. `<style id="app-theme">`: os tokens `--app-*` com o design system do cliente.
3. `<script id="btp-data">`: projeto, fontes, telas e decisões. Apague a chave `"exemplo"`.
4. Um `<template data-screen="Txx">` por tela, com a prévia em HTML usando o kit `.app-*` (ou, em sistema existente, a marcação real capturada; veja `references/existente.md`), e `data-d="D4"` em cada elemento que uma decisão justifica. O que se repete em todas as telas (menu lateral, cabeçalho) fica num `<template data-shared="menu">` e entra em cada tela com `<div data-use="menu" data-active="conciliacao"></div>`.
5. Opcionalmente `<style id="app-css">` e `<script id="app-js">` para componentes e interações que o kit não cobre.

Em prévias grandes (mais de três telas), escreva cada bloco num arquivo em `WORK/partes/` (`titulo.txt`, `tema.css`, `app.css`, `data.json`, `telas.html`, `app.js`) e monte com `PY SKILL_DIR/scripts/assemble.py WORK`. O script encaixa as partes no template atual sem tocar no motor; para ajustar, edite a parte e monte de novo. Listas longas e repetitivas (os tipos de demanda, uma matriz de permissões) saem melhor geradas no `app.js` a partir de um array do que escritas à mão no HTML.

A prévia deve ser interativa sempre que der: menu e linhas que navegam (`data-goto`), modais e gavetas (`data-open`/`data-panel`), abas (`data-tabs`), filtros que filtram, formulários que confirmam com aviso (`data-toast-submit`). Use dados fictícios realistas no formato do cliente (R$, datas brasileiras, nomes plausíveis). Não copie dados reais de clientes finais, CPFs ou valores sensíveis vistos em prints ou na gravação.

### 6. Validar e publicar

1. Rode `PY SKILL_DIR/scripts/validate.py WORK/preview.html --out WORK/publicar.html --local WORK/teste.html`. Ele confere se o motor está inteiro, cruza ids, tipos, trechos, marcações, navegação e imagens, e só grava as cópias se não houver erro. Em `publicar.html` as imagens de `img/` vão embutidas, então a publicação não precisa do parâmetro `files`. Corrija todos os erros; leia os avisos e corrija os que fazem sentido.
2. Olhe a página uma vez antes de publicar: pela checagem do ambiente, se houver (ArtifactCheck ou `action: "preview"`), por um roteiro do `scripts/capturar.mjs` (print do documento, de uma tela isolada em `teste.html#so-T01`, cliques no protótipo), ou por um print do `teste.html` com o Chrome sem janela (`chrome` ou `msedge` com `--headless=new --hide-scrollbars --window-size=1300,1600 --virtual-time-budget=4000 --screenshot=WORK/print.png "file:///C:/.../teste.html"`) e Read no PNG. Corrija o que aparecer, sem entrar em ciclo de prints.
3. Publique com a ferramenta Artifact: `file_path` = `WORK/publicar.html`, `icon` = `"layout"`, `description` com uma frase sobre o projeto e as fontes. Se a ferramenta recusar o caminho por estar fora do diretório de trabalho, gere o `--out` no diretório de trabalho atual ou no scratchpad e publique de lá. O artefato nasce privado; não mude isso sem o usuário pedir, porque ele cita reuniões internas.
4. Salve `WORK/state.json` com `{ "projeto", "slug", "artifactUrl", "versao", "fontes": [{id, link, modifiedTime}], "atualizadoEm" }`.

### 7. Entregar

Responda curto: o link, quantas telas e decisões, o que mudou no ambiente do usuário (servidor que você subiu e encerrou, arquivos baixados), quantas são inferência e quantas estão em aberto (liste as perguntas aqui na conversa, já que o documento não tem seção para elas). Ofereça os próximos passos que fazem sentido: ajustar telas, transformar as perguntas em aberto num rascunho de e-mail ou pauta (só rascunho; enviar exige confirmação), ou atualizar a prévia depois da próxima reunião.

## Atualizar uma prévia existente

Se `WORK/state.json` existe (ou o usuário passou o link do artefato), é atualização, não projeto novo:
1. Leia o artefato com `Artifact action: "read"` e use o arquivo devolvido como base (alguém pode ter mexido).
2. Colete só as fontes novas ou alteradas (compare `modifiedTime`). Se houver comentários no artefato (`ArtifactComments`), leia e trate como pedidos de ajuste.
3. Aumente `projeto.versao`, acrescente uma linha em `projeto.historico`, marque decisões novas ou mudadas com `"novo": true` (tire o `novo` das antigas) e registre nas decisões substituídas qual decisão as substitui.
4. Se o `preview.html` veio de uma versão antiga da skill (o validador acusa motor ausente ou desatualizado), copie-o para `preview.bak.html` e rode `PY SKILL_DIR/scripts/upgrade_engine.py WORK/preview.html`, que troca só os blocos `btp-shell` e `btp-engine`.
5. Valide e publique no mesmo `url`, para o link continuar o mesmo.

## Princípios que guiam as escolhas

- **Toda marcação aponta para uma fonte ou admite que não tem.** É isso que diferencia esta prévia de um mockup qualquer.
- **Citação é literal.** Paráfrase vai na explicação, nunca entre aspas.
- **A prévia é o produto do cliente, não um wireframe.** Use as cores, fontes e o padrão de menu reais; o leitor deve reconhecer o sistema.
- **Menos telas, mais completas.** Uma tela bem resolvida, com estados e interações, vale mais que cinco esboços.
- **Peça permissão antes de baixar, instalar ou enviar**; leia, liste e analise sem pedir.
