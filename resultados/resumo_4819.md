# Resumo dos resultados: 4819

- Máquina: Windows (Windows 11 (10.0.26200)), 11th Gen Intel(R) Core(TM) i5-11400H @ 2.70GHz, RAM 31.8 GB, página 4096 bytes
- RAM disponível anotada na etapa 1: 19.29 GB

## Parte 1: blocos (tabela do slide)

| Bloco | ms/MB (mediana) | IC 95% | major faults | swap ativo? |
|---|---|---|---|---|
| 256 MB | 0.338 | [0.295, 0.368] | n/d | não |
| 512 MB | 0.345 | [0.327, 0.362] | n/d | não |
| 1 GB | 0.328 | [0.298, 0.347] | n/d | não |
| 2 GB | 0.323 | [0.287, 0.340] | n/d | não |
| 4 GB | 0.280 | [0.277, 0.282] | n/d | não |
| 8 GB | 0.280 | [0.273, 0.285] | n/d | não |
| 16 GB | 0.301 | 1 execução | n/d | não |
| 32 GB | 0.912 | 1 execução | n/d | sim |

Base (blocos que cabem): 0.326 ms/MB; pior bloco 32 GB: 3x a base. RAM disponível no início: 19599 MB.

## Parte 2a: ponto de quebra (varredura fina)

| Repetição | Disponível no início | Ponto de quebra | Quebra / disponível | Salto |
|---|---|---|---|---|
| 1 | 26513 MB | não detectado | - | - |
| 2 | 28547 MB | 31488 MB | 1.10 | 17x |
| 3 | 28838 MB | 36352 MB | 1.26 | 11x |

Ponto de quebra: média 33920 MB, mediana 33920 MB, desvio 3439 MB, mín 31488, máx 36352, IC 95% [3019, 64821] MB (n=2). RAM total: 32547 MB.

## Parte 2b: passo e TLB

| Passo | Páginas distintas | ns/acesso (mediana) | IC 95% |
|---|---|---|---|
| 64 B | 128 | 1.65 | [1.64, 1.70] |
| 256 B | 512 | 2.75 | [2.71, 2.87] |
| 1 KB | 2048 | 3.02 | [2.98, 3.05] |
| 4 KB | 8192 | 5.87 | [5.86, 6.09] |
| 16 KB | 8192 | 6.41 | [6.39, 6.60] |
| 64 KB | 8192 | 8.59 | [8.53, 8.82] |

Pior passo: 64 KB, 5.2x o menor passo. Página desta máquina: 4 KB.

