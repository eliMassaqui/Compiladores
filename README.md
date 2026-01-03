Para entender o que está acontecendo no seu sistema, precisamos olhar para a "mágica" que ocorre entre o momento em que você digita em Python e o LED do seu Arduino começa a piscar.

O processo é dividido em três camadas principais: a ***Interface***, a ***Tradução*** e a ***Comunicação*** com o Hardware.

1. A Camada de Interface (PyQt6)
Quando você clica no botão, a interface não "congela" porque usamos Multithreading.

O programa cria um "trabalhador" (CompileWorker) que roda em segundo plano.

Este trabalhador envia sinais (Signals) para a barra de progresso, informando em qual etapa ele está.

2. A "Investigação" e Tradução (AST)
Esta é a parte mais técnica. O Python não envia o código diretamente para o Arduino. Ele usa um módulo chamado ast (Abstract Syntax Tree).

Decomposição: O motor lê seu código Python e o transforma em uma "árvore" de lógica.

Mapeamento: Ele percorre essa árvore procurando por padrões. Se ele encontra digital_write(13, 1), ele traduz para a string de texto digitalWrite(13, HIGH);.

Geração de Arquivo: Após traduzir tudo, ele cria fisicamente um arquivo .ino na sua pasta Documents\Wandi Studio\....

3. O Ciclo de Gravação (Arduino-CLI)
Agora que temos um código C++ (Arduino nativo), precisamos transformá-lo em eletricidade para o chip.

Localização Dinâmica: O sistema busca o executável arduino-cli.exe em vários lugares do seu PC até encontrar o correto, garantindo que funcione em qualquer computador.

Compilação: O arduino-cli pega aquele arquivo .ino e o transforma em um binário (zeros e uns).

Upload: Ele "empurra" esse binário através do cabo USB para a porta COM5, gravando definitivamente na memória da placa.

Resumo do Fluxo de Dados:
Usuário: Digita Python e clica em Upload.

Engine: Analisa a lógica (AST) -> Gera texto C++ -> Salva arquivo .ino.

Arduino-CLI: Lê o arquivo .ino -> Compila -> Grava no Hardware.

UI: Recebe o log de sucesso e exibe o uso de memória no console hacker.
