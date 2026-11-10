# Resumo dos resultados: lhass

- Máquina: Linux (Ubuntu 26.04.1 LTS (kernel 7.0.0-42-generic)), 11th Gen Intel(R) Core(TM) i5-11400H @ 2.70GHz, RAM 15.4 GB, página 4096 bytes
- RAM disponível anotada na etapa 1: 11.20 GB

## Parte 1: blocos (tabela do slide)

| Bloco | ms/MB (mediana) | IC 95% | major faults | swap ativo? |
|---|---|---|---|---|
| 256 MB | 0.336 | [0.331, 0.345] | 0 | não |
| 512 MB | 0.351 | [0.348, 0.353] | 0 | não |
| 1 GB | 0.334 | [0.332, 0.336] | 0 | não |
| 2 GB | 0.353 | [0.336, 0.371] | 0 | não |
| 4 GB | 0.344 | [0.340, 0.352] | 0 | não |
| 8 GB | 0.340 | [0.338, 0.341] | 0 | sim |
| 13 GB | 0.479 | 1 execução | 2 | sim |

Base (blocos que cabem): 0.342 ms/MB; pior bloco 13 GB: 1x a base. RAM disponível no início: 11322 MB.

## Parte 2a: ponto de quebra (varredura fina)

| Repetição | Disponível no início | Ponto de quebra | Quebra / disponível | Salto |
|---|---|---|---|---|
| 1 | 12749 MB | não detectado | - | - |
| 2 | 13164 MB | não detectado | - | - |
| 3 | 13414 MB | 17920 MB | 1.34 | 14x |

Ponto de quebra: média 17920 MB, mediana 17920 MB, desvio 0 MB, mín 17920, máx 17920, IC 95% [17920, 17920] MB (n=1). RAM total: 15765 MB.

## Parte 2b: passo e TLB

| Passo | Páginas distintas | ns/acesso (mediana) | IC 95% |
|---|---|---|---|
| 64 B | 128 | 0.98 | [0.98, 0.98] |
| 256 B | 512 | 2.03 | [2.03, 2.04] |
| 1 KB | 2048 | 3.13 | [3.12, 3.14] |
| 4 KB | 8192 | 3.82 | [3.82, 3.85] |
| 16 KB | 8192 | 4.31 | [4.30, 4.37] |
| 64 KB | 8192 | 5.50 | [5.49, 5.53] |

Pior passo: 64 KB, 5.6x o menor passo. Página desta máquina: 4 KB.

