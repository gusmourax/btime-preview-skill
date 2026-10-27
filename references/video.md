# Assistir à gravação

O Claude não reproduz vídeo. "Assistir" aqui é: baixar a gravação, extrair quadros nos momentos certos com `scripts/frames.py`, ler os quadros com a ferramenta Read e alinhá-los com a transcrição pelo horário.

## Quando vale a pena
- **Refatoração**: a call quase sempre percorre o sistema atual com tela compartilhada. Os quadros viram a aba "Como está hoje" e mostram exatamente o botão ou coluna de que a fala trata.
- **Falas dêiticas**: "isso aqui sai", "esse card", "coloca lá em cima". Sem o quadro, a decisão fica ambígua.

Se a transcrição basta e o projeto é novo, não baixe.

## 1. Pedir permissão

Antes de qualquer download, pergunte em uma frase com nome, tamanho e destino. O tamanho vem de `get_file_metadata` (`fileSize`). Exemplo:

> Para ver as telas mostradas na call, preciso baixar a gravação "Modulo Financeiro - Clinica Aurora - 2026/10/21 - Recording" (212 MB) do Drive para `~/btime-preview/hub-financeiro/video/`. Ela é apagada depois que eu extrair os quadros. Posso?

## 2. Baixar

`download_file_content` do MCP do Drive devolve o arquivo em base64 dentro da conversa: não serve para vídeo. Use o Chrome do usuário, que já está logado no Google:

1. Carregue as ferramentas do Chrome (skill `claude-in-chrome`) e abra uma aba nova.
2. Navegue para `https://drive.usercontent.google.com/download?id=<FILE_ID>&export=download&confirm=t`. Se a conta não for a padrão do navegador, acrescente `&authuser=<email do usuário>`.
3. Arquivos grandes podem abrir a página "Não é possível verificar se há vírus neste arquivo". Clique em "Fazer o download assim mesmo" / "Download anyway". Não clique em nada mais na página.
4. O arquivo cai na pasta de Downloads do usuário (`~/Downloads`). Espere terminar sem polling manual: rode em segundo plano (`run_in_background`) um laço curto que termina quando o `.mp4` existe e não há `.crdownload` correspondente, por exemplo
   ```bash
   cd ~/Downloads; until ls -t *.mp4 2>/dev/null | head -1 | grep -q . && ! ls *.crdownload >/dev/null 2>&1; do sleep 5; done; ls -t *.mp4 | head -1
   ```
5. Mova para `WORK/video/` (uma pasta só para ele) e feche a aba que abriu.

Se o Chrome não estiver disponível: entregue ao usuário o link acima, peça para ele clicar e avisar, e siga do passo 4.

Gravações que não são do Drive (YouTube, Loom, Vimeo) baixam com `yt-dlp -o "WORK/video/%(title)s.%(ext)s" <url>`, também com permissão.

## 3. Extrair quadros

`PY SKILL_DIR/scripts/frames.py <video> --out WORK/frames [modos]`

- `--at 04:12 14:53 21:13`: um quadro em cada horário da transcrição em que se fala de tela. É o modo principal. O script soma 2 s (`--offset`) porque a tela costuma aparecer logo depois da fala.
- `--scenes --start 03:50 --end 23:00 --max 40`: um quadro a cada troca de tela compartilhada. Bom para descobrir todas as telas mostradas. Se vier pouco, baixe `--threshold` (0.06); se vier demais (câmera mexendo), suba (0.2).
- `--every 30`: varredura a cada 30 s, quando não se sabe onde olhar.
- `--width 1280` é o padrão; suba para 1600 se o texto da tela não estiver legível.

O script imprime `WORK/frames/frames.md` com caminho e horário de cada quadro. Leia os quadros em paralelo com Read (vários na mesma mensagem) e anote, para cada tela do sistema atual, o melhor quadro.

## 4. Usar na prévia

- Copie os quadros escolhidos para `WORK/img/` com nomes estáveis (`t01-hoje.jpg`) e referencie em `telas[].hoje`:
  `{ "img": "img/t01-hoje.jpg", "legenda": "Conciliação na produção, mostrada na call", "fonte": "R1", "ref": "14:53" }`
- Antes de usar, confira o quadro: se aparecer dado sensível (nome de paciente, CPF, saldo pessoal), recorte com ffmpeg (`-vf crop=w:h:x:y`) ou desfoque a região (`boxblur`), ou não use.
- Uma decisão pode citar o vídeo como trecho: `{ "fonte": "R1", "ref": "16:05 (vídeo)", "texto": "Na tela, a linha 'REND PAGO APLIC AUT' aparece como Descartado." }`. Deixe claro na explicação que é descrição do quadro, não fala.

## 5. Transcrição

A skill não transcreve áudio. As falas citadas saem sempre da transcrição que está nos documentos do projeto: Anotações do Gemini (Google Doc) ou `... - Transcript` (Google Doc ou .docx, na pasta "Gravações & Transcrições"). Procure pelo mesmo título da gravação. Se não existir, avise o usuário qual reunião está sem transcrição e peça que ele a coloque na pasta; use o vídeo só para quadros das telas.

## 6. Limpar

Depois de extrair os quadros, apague `WORK/video/` (o vídeo é grande e já está no Drive). Mantenha `WORK/frames/` e `WORK/img/` para as próximas versões.
