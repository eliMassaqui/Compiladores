# Wandi Studio IDE - Como Funciona a Comunicação Python -> Arduino

Este documento descreve o fluxo completo desde a escrita do código em Python até o acionamento físico do hardware Arduino, mostrando as camadas e bibliotecas envolvidas.

---

## 1. Camadas do Sistema

O processo é dividido em três camadas principais: **Interface**, **Tradução** e **Comunicação com o Hardware**.

### 1.1 Interface (PyQt6)

* A interface gráfica não congela graças ao **Multithreading**.
* Um `CompileWorker` é criado para rodar em segundo plano.
* Ele envia sinais (`Signals`) para a barra de progresso, indicando o status de cada etapa.

### 1.2 Tradução (AST - Abstract Syntax Tree)

* O Python **não envia código diretamente** ao Arduino.
* Utilizamos o módulo `ast` para decompor o código em uma **árvore de lógica**.
* **Mapeamento**: cada comando Python é transformado em sua versão C++ para Arduino. Exemplo:

  ```python
  digital_write(13, 1) -> digitalWrite(13, HIGH);
  ```
* **Geração de Arquivo**: cria-se um arquivo `.ino` na pasta `Documents\Wandi Studio\...`.

### 1.3 Ciclo de Gravação (Arduino-CLI)

* O `arduino-cli.exe` é localizado dinamicamente no PC.
* **Compilação**: transforma o arquivo `.ino` em binário.
* **Upload**: envia o binário via USB para a porta COM (ex.: COM5), gravando o código na memória da placa.

### 1.4 Resumo do Fluxo de Dados

| Etapa       | Responsável  | Ação                                     |
| ----------- | ------------ | ---------------------------------------- |
| Usuário     | Interface    | Digita Python e clica em Upload          |
| Engine      | Tradução AST | Analisa lógica -> Gera C++ -> Salva .ino |
| Arduino-CLI | Compilação   | Lê .ino -> Compila -> Grava no Hardware  |
| UI          | Interface    | Exibe logs e uso de memória              |

---

## 2. Bibliotecas Envolvidas

As bibliotecas são divididas conforme a função no sistema.

### 2.1 Bibliotecas de Software (Código Fonte)

| Biblioteca            | Uso                               | Observação                                                  |
| --------------------- | --------------------------------- | ----------------------------------------------------------- |
| `LiquidCrystal_I2C.h` | Controle do Display LCD 16x2 azul | Conecta via barramento I²C usando apenas dois fios de dados |
| `Wire.h`              | Comunicação I²C                   | Gerencia os pinos SDA e SCL do LCD                          |

### 2.2 Bibliotecas de Hardware (Módulos)

| Biblioteca                    | Uso                              | Componente             |
| ----------------------------- | -------------------------------- | ---------------------- |
| `Keypad.h`                    | Gerencia teclado matricial 4x4   | Entrada de usuário     |
| `Servo.h`                     | Controle de servomotores         | Braço Robótico Wandi   |
| `MFRC522.h` ou `RFID.h`       | Leitura de cartão RFID           | Segurança / Core       |
| `Ultrasonic.h` ou `NewPing.h` | Sensor de distância ultrassônico | Detecção de obstáculos |

### 2.3 Bibliotecas de Atuadores e Interface

| Biblioteca          | Uso                                    | Componente Alvo                         |
| ------------------- | -------------------------------------- | --------------------------------------- |
| `Stepper.h`         | Controle de motores de passo           | Esteira / Eixos de precisão Wandi Robot |
| `PySerial` (Python) | Comunicação entre PC e Arduino via USB | Interface PC -> Arduino                 |

---

### 2.4 Resumo de Aplicação Modular

| Biblioteca          | Responsabilidade      | Componente Alvo       |
| ------------------- | --------------------- | --------------------- |
| `LiquidCrystal_I2C` | UI / Display          | Display LCD 16x2      |
| `Keypad`            | Input de Usuário      | Teclado Matricial     |
| `Servo`             | Movimento / Engine    | Braço Robótico Wandi  |
| `MFRC522`           | Segurança / Core      | Leitor de Cartão RFID |
| `Wire`              | Comunicação Low-level | Barramento I2C        |

---

Este README fornece uma visão clara do fluxo e das dependências do sistema, facilitando a compreensão para desenvolvedores e alunos que utilizam a IDE **Wandi Studio**.
