# Resumo dos resultados: 278

- Máquina: Linux (Ubuntu 26.04.1 LTS (kernel 7.0.0-42-generic)), Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz, RAM 7.2 GB, página 4096 bytes
- RAM disponível anotada na etapa 1: 6.54 GB

## Parte 1: blocos (tabela do slide)

| Bloco | ms/MB (mediana) | IC 95% | major faults | swap ativo? |
|---|---|---|---|---|
| 256 MB | 0.477 | [0.472, 0.482] | 0 | não |
| 512 MB | 0.476 | [0.473, 0.479] | 0 | não |
| 1 GB | 0.472 | [0.470, 0.472] | 0 | não |
| 2 GB | 0.470 | [0.470, 0.471] | 0 | não |
| 4 GB | 0.471 | [0.470, 0.472] | 0 | não |
| 8.2 GB | 1.268 | 1 execução | 73 | sim |

Base (blocos que cabem): 0.472 ms/MB; pior bloco 8.2 GB: 3x a base. RAM disponível no início: 6682 MB.

## Parte 2a: ponto de quebra (varredura fina)

| Repetição | Disponível no início | Ponto de quebra | Quebra / disponível | Salto |
|---|---|---|---|---|
| 1 | 6645 MB | 6656 MB | 1.00 | 11x |
| 2 | 6779 MB | 6656 MB | 0.98 | 11x |
| 3 | 6785 MB | 6656 MB | 0.98 | 14x |

Ponto de quebra: média 6656 MB, mediana 6656 MB, desvio 0 MB, mín 6656, máx 6656, IC 95% [6656, 6656] MB (n=3). RAM total: 7370 MB.

## Parte 2b: passo e TLB

| Passo | Páginas distintas | ns/acesso (mediana) | IC 95% |
|---|---|---|---|
| 64 B | 128 | 2.11 | [2.09, 2.11] |
| 256 B | 512 | 2.84 | [2.81, 2.85] |
| 1 KB | 2048 | 3.18 | [3.15, 3.18] |
| 4 KB | 8192 | 4.62 | [4.58, 4.62] |
| 16 KB | 8192 | 5.30 | [5.25, 5.33] |
| 64 KB | 8192 | 7.58 | [7.53, 7.61] |

Pior passo: 64 KB, 3.6x o menor passo. Página desta máquina: 4 KB.

