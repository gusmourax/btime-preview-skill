# Coleta de insumos

Como achar e ler cada tipo de insumo. As ferramentas do Google vivem como MCP diferido: carregue de uma vez com `ToolSearch` (`select:` com os nomes completos que aparecerem na lista, por exemplo `mcp__claude_ai_Google_Drive__search_files,mcp__claude_ai_Google_Drive__read_file_content,mcp__claude_ai_Google_Drive__get_file_metadata,mcp__claude_ai_Google_Calendar__search_events,mcp__claude_ai_Google_Calendar__get_event`).

## Sumário
1. Reuniões (Agenda, Meet, Gemini)
2. Pastas do projeto no Drive
3. Documentos
4. Visual: design system, projeto de exemplo, sistema atual
5. E-mail (opcional)
6. Inventário

## 1. Reuniões

O usuário costuma passar algo como "Call Modulo Financeiro - Clinica Aurora - Quarta-feira, 21 de outubro⋅10:00 – 10:30am". Esse é o título e a data do evento na Agenda.

1. `search_events` com o título sem o dia da semana (ex.: `Modulo Financeiro Aurora`). A busca é semântica e pode falhar com o texto inteiro; se vier vazia, tente palavras menores (`Modulo Financeiro`), sem acentos, ou só o cliente. A API da Agenda tem cota curta: se responder "Resource has been exhausted", não insista; vá direto para a busca no Drive (passo 3).
2. O evento traz `attachments` com:
   - **"Anotações do Gemini"** (Google Doc). Tem duas abas: "Observações" (resumo, decisões alinhadas, próximas etapas, detalhes com links de horário) e "Transcrição" (blocos `### 00:14:53` com falas por pessoa). `read_file_content` devolve as duas abas juntas.
   - **Gravação** (`video/mp4`, normalmente 100 a 500 MB). Veja `video.md`.
3. Se o evento não tiver anexos, procure no Drive pelo título: `title contains 'Modulo Financeiro' and title contains 'Aurora'`. Os arquivos do Meet seguem o padrão `<título> - AAAA/MM/DD HH:MM GMT-03:00 - Recording` e `... - Anotações do Gemini` (ou `... - Transcript` em contas antigas).
4. Cópias em pastas do projeto podem ser **atalhos** (`application/vnd.google-apps.shortcut`). Leia o arquivo original, achado pela busca por título.

### Como citar uma reunião
- `ref` é o horário do bloco da transcrição onde a fala está (`14:53`). Se a fala estiver no meio de um bloco longo, use o horário do bloco mesmo; quem abrir acha a fala ali.
- `quem` é o nome do interlocutor como aparece na transcrição.
- `link` do trecho pode ser o link de horário que o próprio Gemini coloca na aba Observações (`...#heading=h.xxxx`) quando ele existir para aquele bloco; senão, o link do documento.
- As "Decisões" e "Próximas etapas" do Gemini são resumo automático, não fala. Use-as para achar o assunto, mas cite a fala da transcrição. Se só o resumo tiver a informação, cite o resumo e diga na explicação que é resumo do Gemini.
- Transcrição automática erra nomes e termos ("Sport Clinic" vira "esporte clínico", "DRE" vira "DR"). Cite literal e, quando importar, esclareça na explicação.

### Várias reuniões
Ordene por data. A mais recente vence quando há conflito; registre na decisão nova qual ela substitui. Procure ativamente as reuniões posteriores à pedida (devolutivas, "tirar dúvidas", planejamento): busque no Drive `title contains '<cliente>' and createdTime > '<data da reunião>'` e liste a pasta de gravações do projeto.

O peso de uma fala depende de quem fala e do que diz, não de o cliente estar na sala. Muitas calls são internas, com o líder do projeto repassando ao time o que o cliente quer. Vale como `reuniao`: o cliente decidindo ou pedindo; o líder ou responsável do projeto relatando um pedido do cliente ou decidindo algo do seu escopo ("o cliente pediu", "isso sai", "a prioridade é"). Vale como `inferencia` ou `aberto`: ideia levantada sem fechamento ("talvez", "a gente vê depois"), sugestão de quem não decide, ou pedido que depende de confirmação do cliente. Registre o papel em `quem` quando ajudar ("Lucas, líder do projeto").

## 2. Pastas do projeto no Drive

Pastas de empresa têm uma subpasta por projeto. Padrão comum visto nos projetos btime:
- `Gravações & Transcrições`: atalhos para gravações e anotações do Gemini.
- `Insumos`: material do cliente (planilhas, prints, exemplos, relatórios atuais).
- `Documentos`: documentação técnica, requisitos, TO BE.
- `Cronograma`, `Pré projeto`, `TEP`: planejamento e proposta. Úteis para entender escopo e prioridade, raramente para desenhar tela.

Listar uma pasta: `search_files` com `parentId = '<id>'` e `excludeContentSnippets: true`. Várias pastas de uma vez: `parentId = 'a' or parentId = 'b'`. Desça no máximo dois níveis e só no projeto pedido. O id da pasta está na URL (`drive.google.com/drive/folders/<id>`).

## 3. Documentos

- `read_file_content` lê Google Docs, Slides, Sheets, PDF, DOCX, XLSX, PPTX e imagens. Para planilhas grandes, use as ferramentas do Google Sheets (`get_values`) só nas abas que importam.
- Priorize, nesta ordem: requisitos/TO BE e critérios de aceite; regras de negócio; documentação técnica do sistema atual; cronograma e prioridades; atas.
- Cite com a referência que o documento usa (`CA-12`, `RN-07`, `seção 3.2`, `p. 14`). Sem numeração, use o título da seção.
- Documentos com nome "Cópia de ..." ou versões antigas: prefira o mais recente (`modifiedTime`) e registre no inventário qual foi usado.

## 4. Visual

O objetivo é que a prévia pareça o produto do cliente. Extraia, de onde houver:

- **Design system / guia de marca** (PDF, Figma exportado, site de documentação): cores primária, neutros, sucesso/alerta/erro; fonte e pesos; raio de cantos; altura de botões e inputs.
- **URL de projeto de exemplo ou do sistema atual.** Com o Chrome do usuário (skill `claude-in-chrome`): abra numa aba nova e rode no `javascript_tool` algo como
  ```js
  const cs = el => getComputedStyle(el);
  const b = document.querySelector('button, .btn, [class*=button]');
  ({ body: { bg: cs(document.body).backgroundColor, color: cs(document.body).color, font: cs(document.body).fontFamily },
     button: b && { bg: cs(b).backgroundColor, color: cs(b).color, radius: cs(b).borderRadius, font: cs(b).fontWeight },
     vars: [...document.styleSheets].flatMap(s => { try { return [...s.cssRules] } catch { return [] } })
       .filter(r => r.selectorText === ':root').map(r => r.cssText).join('\n').slice(0, 4000) })
  ```
  Para guardar um print como arquivo (aba "Como está hoje") de uma página pública, use o Chrome sem janela: `chrome --headless --screenshot=<WORK>/img/x.png --window-size=1440,900 <url>` (no Windows, `msedge` também funciona). Página com login: use o quadro da gravação ou peça um print ao usuário.
- **Código do sistema atual** (refatoração com repositório local): `src/index.css`, `tailwind.config.*`, arquivos de tema, componentes de layout e o arquivo de rotas/menu. Eles dão os tokens exatos e a lista real de telas. Antes de usar um repositório, confira no README, no `package.json` e nas rotas se ele é mesmo o sistema em questão: nomes de pasta enganam (um `cliente-hub-financeiro` pode ser outro módulo). O histórico de commits mostra o que já foi implementado ou revertido depois da reunião.
- **Prints e imagens enviados pelo usuário**: leia com Read; copie para `WORK/img/` os que vão para a aba "Como está hoje".

Registre cada referência visual como fonte `V`, e as decisões de visual como tipo `referencia` com trecho (o valor do token, o nome do componente, a legenda do print).

## 5. E-mail (opcional)

Se o usuário mencionar que algo foi combinado por e-mail, `search_threads` no Gmail com o assunto ou o cliente. Cite como fonte `A` (tipo documento) com a data do e-mail. Nunca envie e-mail sem pedido explícito; rascunho só quando o usuário pedir.

## 6. Inventário

`WORK/insumos.md`, uma linha por fonte:

```
| id | tipo | título | data | link | uso |
| R1 | reuniao | Modulo Financeiro - Clinica Aurora | 2026-10-21 | <link anotações> | transcrição completa lida; vídeo: quadros 04:10–22:40 |
| A1 | documento | TO BE V2 | 2026-10-19 | <link> | critérios CA-01 a CA-15 |
| V1 | design | Tema do Hub (src/index.css) | 2026-10-22 | <caminho> | cores --sidebar-*, fonte |
```

O mesmo conjunto vai para `fontes` no `btp-data`. Fontes lidas que não renderam nenhum trecho também entram: mostram o que foi considerado.
