## Sobre a Implementação Realizada

Este repositório contém apenas a parte da atividade que consegui implementar até o momento. As entregas incluem:

---

## 1. Firmware (`main.c`)

O código localizado na pasta **firmware** implementa um console básico via UART para interação com o sistema embarcado. As principais funcionalidades desenvolvidas foram:

### Leitura de comandos via UART
- Implementação da função `f_leitura_linha()` para leitura não bloqueante de caracteres.
- Suporte a backspace, nova linha e buffer estático para armazenamento da entrada.
- Echo dos caracteres digitados ao terminal.

### Parser simples de comandos
- Função `f_pegar_token()` para extrair comandos separados por espaço.
- Lógica de interpretação de comandos utilizando `strcmp()`.

### Comandos implementados
- `ajuda`: exibe a lista de comandos disponíveis.
- `reset`: reinicia o processador via `ctrl_reset_write(1)`.
- `led_cmd`: alterna o estado do LED acessando CSR de `leds_out`.

### Estrutura geral
- Inicialização da UART e interrupções.
- Laço principal chamando o serviço de console.
- Exibição de prompt e mensagem de inicialização.

Até o momento, não foi implementada nenhuma integração com modelo TFLM, carregamento de rede neural, nem lógica de inferência. A implementação cobre apenas a parte básica de console e manipulação de GPIO.

---

## 2. SoC LiteX (`colorlight_i5.py`)

O arquivo na pasta **litex** contém a configuração do SoC baseado na plataforma Colorlight i5, com as seguintes implementações concluídas:

### Estrutura do clock
- Construção do módulo de gerenciamento de clock (`_ClkMgr`) com geração dos domínios:
  - `sys_clk`
  - `sys2x_clk` / `sys_ps_clk` dependendo do modo SDRAM
- Implementação de PLLs adicionais para USB e HDMI (caso habilitados).

### Configuração do SoC
- Instanciação do `SoCCore` com clock, identificação e parâmetros básicos.
- Inclusão opcional do periférico LED via `LedChaser`.

### Periféricos implementados
- **SPI Master** com extensão de pinos customizada.
- **GPIOOut** para controlar reset de rádio LoRa.
- **I2C Master** com pinos modificados.
- **Flash SPI** com detecção automática da memória para i5/i9.
- **SDRAM** com PHY adequado e módulo M12L64322A.

### Suporte adicional
- Opções para Ethernet, Etherbone, framebuffer HDMI e terminal HDMI.
- Configuração via argumentos de linha de comando com `LiteXArgumentParser`.

---

## 3. Etapas Não Concluídas

Até onde foi possível avançar, **não foram implementadas** as seguintes partes da atividade:

- Criação e treinamento do modelo de ML.
- Quantização do modelo e preparação para TFLM.
- Port do TensorFlow Lite Micro para LiteX/VexRiscv.
- Integração do modelo no firmware.
- Inferência e acionamento de LEDs baseado em ML.
- Geração final do bitstream com todas as integrações.
- Demonstração em vídeo.

Este README documenta exclusivamente o que foi desenvolvido até o momento, sem representar a atividade completa.

---
