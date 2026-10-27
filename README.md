# btime-preview

Skill do [Claude Code](https://claude.com/claude-code) que transforma o que foi conversado e documentado num projeto em uma **prévia navegável das telas**, publicada como Artifact no claude.ai.

Cada tela aparece no visual do produto, clicável, e tudo o que existe nela tem um tracejado colorido que aponta para uma **decisão numerada**, com a explicação e o **trecho literal da fonte** logo abaixo (fala da reunião com horário, seção do documento, token do design system). Quem aprova vê a tela e confere de onde ela veio.

O documento é feito para validação com a liderança interna ou com o cliente que pediu o sistema: claro e objetivo, sem pauta nem lista de pendências.

## O que ela faz

- **Coleta sozinha os insumos**: reuniões do Google Agenda/Meet (Anotações do Gemini e transcrição), documentos do Google Drive (requisitos, AS IS / TO BE, atas), design system, URL de projeto de exemplo, prints e o código do sistema atual.
- **Destila as decisões**, cada uma classificada pela origem:

  | Tipo | Significa |
  |---|---|
  | `reuniao` | decidido ou pedido em reunião |
  | `documento` | regra escrita num documento do projeto |
  | `referencia` | vem do design system, do exemplo ou do sistema atual |
  | `inferencia` | proposta sem trecho que a peça (a prévia admite isso) |
  | `aberto` | precisa de decisão; a prévia mostra uma suposição |

- **Monta as telas** num template fixo, que é sempre igual de um projeto para outro, com modo documento (tela + decisões) e modo protótipo (navegação, abas, janelas, filtros).
- **Em sistema que já existe**, captura o sistema rodando localmente e mostra cada tela em três abas: **Como vai ficar**, **Como está hoje** e **Antes e depois** (linha deslizante sobre os dois prints). Só o que foi pedido muda.
- **Valida e publica** o Artifact (privado), e na reunião seguinte atualiza o mesmo link.

Mais detalhes em [docs/como-funciona.md](docs/como-funciona.md). Exemplos e quando vale a pena usar estão em [docs/exemplos-de-uso.md](docs/exemplos-de-uso.md).

## Instalação

A pasta deste repositório é a própria skill. Clone dentro das skills do usuário:

```bash
git clone https://github.com/gusmourax/btime-preview-skill.git ~/.claude/skills/btime-preview
```

No Windows: `git clone https://github.com/gusmourax/btime-preview-skill.git "%USERPROFILE%\.claude\skills\btime-preview"`.

O nome da pasta de destino precisa ser `btime-preview`, o mesmo do `name` no `SKILL.md`. Abra uma sessão nova do Claude Code; a skill aparece como `btime-preview`. Para atualizar, rode `git pull` nessa pasta.

### Requisitos

| O quê | Para quê | Obrigatório |
|---|---|---|
| Claude Code com Artifacts | publicar a prévia | sim |
| Conectores **Google Drive** e **Google Agenda** (claude.ai → Configurações → Conectores, depois `/mcp`) | ler reuniões e documentos | sim, para coletar sozinha |
| Python 3 (`py -3` no Windows) | montar e validar o artefato | sim |
| ffmpeg / ffprobe | quadros da gravação da reunião | só quando o vídeo for necessário |
| Node 22+ e Chrome ou Edge | capturar o sistema atual (`capturar.mjs`) e conferir a prévia | só para sistema existente |

`scripts/check_env.py` diz o que está pronto e o que falta. Com `--install`, instala o ffmpeg, mas a skill sempre pede permissão antes.

## Como usar

Basta pedir em linguagem natural. A skill entra quando o assunto é ver como as telas vão ficar:

```text
Usa a btime-preview com a pasta do Drive do projeto <link>.
Gera a prévia das telas a partir da call "Kickoff Portal Fornecedores" de ontem.
Analisa a call de hoje e usa a skill de prévia com o projeto <pasta-do-código>.
Teve outra reunião, atualiza a prévia.
```

A skill pergunta só o que bloqueia: qual projeto, quando a pasta tem vários, e a lista de telas, quando a reunião não deixou claro. Ela também pede permissão antes de baixar, instalar ou enviar qualquer coisa.

## Estrutura

```text
SKILL.md                 fluxo principal (o que o Claude lê quando a skill é acionada)
references/
  coleta.md              como achar e ler reuniões, documentos e referências visuais
  video.md               quando e como usar a gravação (download com permissão, quadros)
  artefato.md            contrato do template: blocos, btp-data, marcações, kit de componentes
  existente.md           caminho para sistema que já roda: captura, CSS real, antes e depois
assets/
  template.html          template do artefato com o motor (btp-shell + btp-engine, versão 2)
scripts/
  check_env.py           confere conectores, Python, ffmpeg, Node e navegador
  frames.py              extrai quadros da gravação por horário ou por troca de tela
  capturar.mjs           roteiro de navegador sem janela (prints, HTML, CSS) via CDP
  escopo_css.py          prende o CSS do sistema atual dentro da prévia (.app-real)
  assemble.py            monta preview.html a partir de WORK/partes/
  validate.py            valida o artefato e gera a cópia para publicar (imagens embutidas)
  upgrade_engine.py      troca o motor de uma prévia antiga pelo atual
docs/                    esta documentação (o Claude não precisa dela para rodar a skill)
```

O trabalho de cada projeto fica fora do repositório, em `~/btime-preview/<slug-do-projeto>/`: insumos, partes, prints, a prévia e o `state.json` com o link do artefato.

## Cuidados embutidos

- Citação é sempre literal; paráfrase fica na explicação.
- A skill não transcreve áudio: o texto das reuniões vem das transcrições que já estão nos documentos do projeto.
- O artefato leva só imagens, sem vídeo, e fica privado.
- Os dados das telas são fictícios. Nada da gravação de produção nem dados reais de clientes finais entra na página.
- Num sistema existente, ela usa só contas de teste do próprio projeto, em `localhost`. Senhas não ficam nos roteiros (`${ENV:VAR}`) e ela não mexe em `.env` nem no banco sem permissão.
