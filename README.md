## Sobre a Implementação Realizada

Este repositório contém apenas a parte da atividade que consegui implementar até o momento. As entregas incluem:

---

## 1. Firmware (`main.c`)

O código localizado na pasta **firmware** implementa um console básico via UART para interação com o sistema embarcado. As principais funcionalidades desenvolvidas foram:

### Leitura de comandos via UART
- Leitura não bloqueante de caracteres (`f_leitura_linha()`).
- Tratamento de backspace e nova linha.
- Echo automático dos caracteres.
- Buffer estático para armazenamento da linha digitada.

### Parser simples de comandos
- Função `f_pegar_token()` para separar comandos por espaço.
- Interpretação baseada em `strcmp()`.

### Comandos implementados
- `ajuda`: exibe a lista de comandos.
- `reset`: reinicia o processador via `ctrl_reset_write(1)`.
- `led_cmd`: alterna o estado do LED conectado ao CSR `leds_out`.

### Estrutura geral
- Inicialização da UART.
- Inicialização de interrupções.
- Loop principal responsável por processar comandos.
- Exibição de prompt e mensagem inicial.

Até o momento, não há integração com TensorFlow Lite Micro, carregamento de modelos, ou execução de inferência.

---

## 2. SoC LiteX (`colorlight_i5.py`)

O arquivo na pasta **litex** contém a configuração do SoC baseado na plataforma Colorlight i5. A implementação concluída inclui:

### Estrutura de clock
- Módulo `_ClkMgr` responsável por:
  - `sys_clk`
  - `sys2x_clk` (SDRAM)
  - `sys_ps_clk` (SDRAM em modo half-rate)
  - Clocks opcionais para USB e HDMI
- Configuração de PLLs e domínio de clock principal.

### Configuração do SoC
- Instanciação do `SoCCore`.
- Implementação do periférico de LEDs via `LedChaser`.
- Interligação dos elementos principais do SoC.

### Periféricos implementados
- **SPI Master**, com pinos remapeados para pads específicos da placa.
- **I2C Master**, também com remapeamento de pinos.
- **GPIOOut** para controle de reset externo (ex.: módulo LoRa).
- **Flash SPI** com detecção automática.
- **SDRAM** com PHY M12L64322A e ajustes de banda.

### Suporte adicional
- Módulos opcionais: Ethernet, Vídeo HDMI, Etherbone.
- Configuração por argumentos via `LiteXArgumentParser`.

---

## 3. Pinos Utilizados no Projeto

A tabela abaixo descreve os pinos atualmente utilizados pelo sistema.  
Os nomes lógicos são definidos no LiteX e mapeados para pads físicos da Colorlight i5.

Preencha conforme o mapeamento real do seu projeto.

### UART (Console)
| Sinal | Pino da Placa | Observações |
|-------|----------------|-------------|
| TX    | PREENCHER      | Saída UART para o computador |
| RX    | PREENCHER      | Entrada UART do computador   |

### LEDs
| Sinal      | Pino da Placa | Observações |
|------------|----------------|-------------|
| leds_out   | PREENCHER      | LED utilizado no comando `led_cmd` |

### SPI Master
| Sinal | Pino da Placa | Observações |
|-------|----------------|-------------|
| MOSI  | PREENCHER      | Usado para dispositivo externo |
| MISO  | PREENCHER      | Usado para dispositivo externo |
| SCK   | PREENCHER      | Clock do barramento SPI |
| CS    | PREENCHER      | Chip Select do periférico |

### I2C Master
| Sinal | Pino da Placa | Observações |
|-------|----------------|-------------|
| SDA   | PREENCHER      | Dados I2C |
| SCL   | PREENCHER      | Clock I2C |

### GPIO / Reset Externo
| Sinal           | Pino da Placa | Observações |
|------------------|----------------|-------------|
| lora_reset_n_out | PREENCHER      | Controle de reset para módulo externo |

### SDRAM
| Sinal | Pinos da Placa | Observações |
|--------|--------------------|-------------|
| DQ     | PREENCHER          | Barramento de dados |
| A      | PREENCHER          | Barramento de endereços |
| CLK    | PREENCHER          | Clock SDRAM |
| WE/CS  | PREENCHER          | Sinais de controle |

> Observação: a quantidade exata de pinos depende da memória M12L64322A da placa.

---

## 4. Etapas Não Concluídas

As seguintes partes da atividade **ainda não foram implementadas**:

- Criação e treinamento do modelo de machine learning.
- Quantização do modelo e preparação para TFLite Micro.
- Port do TFLM para arquitetura VexRiscv/LiteX.
- Makefile para compilação cruzada do TFLM.
- Carregamento do modelo no firmware.
- Execução da inferência.
- Controle dos LEDs baseado no resultado do modelo.
- Demonstração final em vídeo.

Este documento descreve exclusivamente a parte do projeto desenvolvida até o momento.

---
