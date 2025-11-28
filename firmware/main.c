#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <console.h>
#include <generated/csr.h>

/* Função para ler uma linha de caracteres da entrada (UART) */
static char *f_leitura_linha(void)
{
    char input_char[2];
    static char buffer_str[64]; /* Buffer estático para a string lida */
    static int indice_atual = 0;

    /* Verifica se há dados não bloqueantes disponíveis */
    if(readchar_nonblock()) {
        input_char[0] = readchar();
        input_char[1] = 0;
        switch(input_char[0]) {
            case 0x7f: /* DEL */
            case 0x08: /* Backspace */
                if(indice_atual > 0) {
                    indice_atual--;
                    putsnonl("\x08 \x08"); /* Apaga o caractere da tela */
                }
                break;
            case 0x07: /* BEL (Ignorar) */
                break;
            case '\n': /* Nova Linha */
            case 0x0d: /* Retorno de Carro (CR) */
                buffer_str[indice_atual] = 0; /* Finaliza a string */
                putsnonl("\n");
                indice_atual = 0;
                return buffer_str;
            default:
                if(indice_atual < (sizeof(buffer_str) - 1)) {
                    putsnonl(input_char);
                    buffer_str[indice_atual] = input_char[0];
                    indice_atual++;
                }
                break;
        }
    }

    return NULL;
}

/* Função para extrair o próximo token (separado por espaço) de uma string */
static char *f_pegar_token(char **ponteiro_str)
{
    char *separador, *resultado;

    /* Procura o primeiro espaço */
    separador = (char *)strchr(*ponteiro_str, ' ');
    if(separador == NULL) {
        /* Nenhum espaço encontrado, a string restante é o token */
        resultado = *ponteiro_str;
        *ponteiro_str = *ponteiro_str + strlen(*ponteiro_str);
        return resultado;
    }
    /* Termina o token no espaço */
    *separador = 0;
    resultado = *ponteiro_str;
    /* Move o ponteiro_str para depois do espaço */
    *ponteiro_str = separador + 1;
    return resultado;
}

/* Exibe o prompt de comando */
static void f_exibir_prompt(void)
{
    printf("CONSOLE>>");
}

/* Exibe a lista de comandos */
static void f_ajuda(void)
{
    puts("Comandos disponiveis:");
    puts("ajuda    - Exibe esta mensagem");
    puts("reset    - Reinicia o processador");
    puts("led_cmd  - Testa a saida do LED");
}

/* Reinicia o sistema */
static void f_resetar_cpu(void)
{
    ctrl_reset_write(1);
}

/* Alterna o estado do LED */
static void f_alternar_led(void)
{
    int estado_atual;
    printf("Alternando o estado do LED...\n");
    estado_atual = leds_out_read();
    leds_out_write(!estado_atual);
}

/* Função principal de serviço do console */
static void f_servico_console(void)
{
    char *entrada_str;
    char *comando;

    entrada_str = f_leitura_linha();
    if(entrada_str == NULL) return;
    
    comando = f_pegar_token(&entrada_str);

    /* Verificação de comandos usando if/else if com ordem alterada */
    if(strcmp(comando, "reset") == 0) {
        f_resetar_cpu();
    } else if(strcmp(comando, "led_cmd") == 0) {
        f_alternar_led();
    } else if(strcmp(comando, "ajuda") == 0) {
        f_ajuda();
    }
    
    f_exibir_prompt();
}

int main(void)
{
#ifdef CONFIG_CPU_HAS_INTERRUPT
    /* Inicializa as interrupções se suportado */
    irq_setmask(0);
    irq_setie(1);
#endif
    /* Inicializa a UART (terminal) */
    uart_init();

    puts("\nSoftware de Teste do Sistema - Compilado em "__DATE__" "__TIME__"\n");
    printf("Bem-vindo ao Console!\n");
    f_ajuda();
    f_exibir_prompt();

    /* Loop principal */
    while(1) {
        f_servico_console();
    }

    return 0;
}