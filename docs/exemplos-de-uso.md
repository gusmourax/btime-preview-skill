# Exemplos de uso e quando vale a pena

A btime-preview rende mais **entre a reunião e o início do desenvolvimento**: transforma "o que foi falado" em "isto é o que vamos construir, confirma?". Ela é útil quando existe uma conversa ou um documento que precisa virar tela, e alguém precisa aprovar essa tela sabendo de onde veio cada coisa.

## Exemplos

### 1. Depois do kickoff de um projeto novo

> "Usa a btime-preview com a pasta do Drive do projeto Portal Fornecedores."

A skill lê a transcrição do kickoff, o AS IS, o TO BE e o mockup. As telas saem com cada regra ligada ao trecho que a pediu, e as dúvidas viram perguntas para a próxima reunião. Com isso, o cliente valida o escopo antes de qualquer linha de código.

### 2. Validar uma refatoração

> "Gera a prévia do novo Módulo Financeiro a partir da call de 21/10."

Cada tela mostra **como vai ficar** e **como está hoje**. O cliente vê que a coluna X saiu porque ele mesmo pediu às 14:53, e não porque o time decidiu sozinho.

### 3. Pedido de ajustes num sistema que já roda

> "Analisa a call de hoje e usa a skill de prévia com o projeto `<pasta-do-código>`."

A prévia é o **sistema real**: HTML e CSS capturados localmente, com só o que foi pedido mudado, mais a aba **Antes e depois**. Serve para confirmar com quem pediu se o time entendeu certo, antes de abrir a tarefa para o desenvolvimento.

### 4. Atualizar depois da reunião seguinte

> "Teve outra call com o cliente, atualiza a prévia."

A skill lê só o que é novo, marca as decisões que mudaram e mantém o mesmo link. O cliente acompanha a evolução no mesmo lugar, com histórico de versões.

### 5. Reorganizar telas: juntar, dividir, mover ou tirar

> "Na call pediram para a Auditoria virar uma aba de Movimentações, separar Itens de Cadastros e tirar a página Alertas. Gera a prévia."

A prévia abre com o **Mapa das telas**: o menu de hoje de um lado, o novo do outro, com setas como "junta 2 telas", "divide em 2 telas", "muda de lugar" e "sai do sistema", cada uma com a decisão que a pediu. Cada tela nova diz de onde veio, e a comparação deixa escolher qual tela de hoje comparar. Cada tela que sai tem uma ficha com o print de hoje e o destino do que ela fazia. O validador avisa se alguma tela do menu atual ficou sem destino.

### 6. Resolver uma divergência entre documentos

Se o mockup diz uma coisa e o documento mais recente diz outra, a prévia segue o mais recente e mostra os dois trechos lado a lado na decisão. A divergência fica visível em vez de se perder.

### 7. Preparar a pauta da reunião de validação

As decisões `aberto` já vêm com pergunta, recomendação e quem decide. A lista vai na conversa e pode virar rascunho de e-mail ou pauta, enquanto a prévia mostra o que cada resposta muda na tela.

## Quando ela é realmente útil

- **Há uma fonte para rastrear**: reunião transcrita, TO BE, AS IS, ata. O diferencial é a citação; sem fonte, ela vira só um gerador de mockup.
- **Alguém de fora do time precisa aprovar.** Liderança ou cliente não leem especificação, mas entendem uma tela clicável com a explicação embaixo.
- **O risco é de entendimento, não de execução**: pedidos ambíguos ("já venha filtrado"), falas que apontam para a tela ("esse filtro aqui") e regras espalhadas por vários documentos.
- **Vai haver mais de uma rodada.** O mesmo link evolui a cada reunião.
- **O sistema existe e roda localmente.** Aí a prévia mostra exatamente como fica no produto real, e não uma aproximação.

## Quando não compensa

- **Ajuste trivial e já entendido** ("muda a cor do botão"): é mais rápido fazer direto no código.
- **Sem nenhuma fonte escrita ou gravada**: quase tudo seria `inferencia`, e a prévia perde o valor de prova.
- **Exploração visual livre** ("me mostra três ideias de dashboard"): uma ferramenta de design ou um protótipo solto atende melhor.
- **O entregável é o código**: a skill gera a prévia para validar, não implementa a mudança no projeto.
- **Sistema existente que não roda localmente**: ainda funciona com prints, mas perde a fidelidade da captura real. Isso é dito na entrega.
