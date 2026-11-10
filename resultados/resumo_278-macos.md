# Resumo dos resultados: 278-macos

- Máquina: macOS (macOS 27.2), Apple M4, RAM 16.0 GB, página 16384 bytes
- RAM disponível anotada na etapa 1: 6.31 GB

## Parte 1: blocos (tabela do slide)

| Bloco | ms/MB (mediana) | IC 95% | major faults | swap ativo? |
|---|---|---|---|---|
| 256 MB | 0.057 | [0.055, 0.059] | 0 | não |
| 512 MB | 0.056 | [0.055, 0.058] | 0 | não |
| 1 GB | 0.056 | [0.055, 0.057] | 0 | não |
| 2 GB | 0.056 | [0.056, 0.057] | 0 | não |
| 4 GB | 0.056 | [0.048, 0.074] | 0 | não |
| 8 GB | 0.201 | 1 execução | 0 | sim |
| 16 GB | 0.438 | 1 execução | 0 | sim |
| 20 GB | 0.472 | 1 execução | 0 | sim |

Base (blocos que cabem): 0.056 ms/MB; pior bloco 20 GB: 8x a base. RAM disponível no início: 6601 MB.

## Parte 2a: ponto de quebra (varredura fina)

| Repetição | Disponível no início | Ponto de quebra | Quebra / disponível | Salto |
|---|---|---|---|---|
| 1 | 11357 MB | 10240 MB | 0.90 | 11x |
| 2 | 11692 MB | 10496 MB | 0.90 | 15x |
| 3 | 11380 MB | 14592 MB | 1.28 | 11x |

Ponto de quebra: média 11776 MB, mediana 10496 MB, desvio 2442 MB, mín 10240, máx 14592, IC 95% [5709, 17843] MB (n=3). RAM total: 16384 MB.

## Parte 2b: passo e TLB

| Passo | Páginas distintas | ns/acesso (mediana) | IC 95% |
|---|---|---|---|
| 64 B | 32 | 0.86 | [0.86, 0.87] |
| 256 B | 128 | 0.90 | [0.89, 0.90] |
| 1 KB | 512 | 0.99 | [0.98, 0.99] |
| 4 KB | 2048 | 0.95 | [0.94, 0.95] |
| 16 KB | 8192 | 3.27 | [3.01, 3.25] |
| 64 KB | 8192 | 1.89 | [1.81, 1.89] |

Pior passo: 16 KB, 3.8x o menor passo. Página desta máquina: 16 KB.

