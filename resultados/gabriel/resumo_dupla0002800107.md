# Resumo dos resultados: dupla0002800107

- Máquina: Linux (Linux Mint 22.3 (kernel 7.0.0-42-generic)), Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz, RAM 7.6 GB, página 4096 bytes
- RAM disponível anotada na etapa 1: 3.48 GB

## Parte 1: blocos (tabela do slide)

| Bloco | ms/MB (mediana) | IC 95% | major faults | swap ativo? |
|---|---|---|---|---|
| 256 MB | 0.448 | [0.388, 0.490] | 0 | não |
| 512 MB | 0.381 | [0.373, 0.399] | 0 | não |
| 1 GB | 0.364 | [0.361, 0.367] | 0 | não |
| 2 GB | 0.383 | [0.363, 0.421] | 0 | sim |
| 4.2 GB | 5.647 | 1 execução | 0 | sim |

Base (blocos que cabem): 0.382 ms/MB; pior bloco 4.2 GB: 15x a base. RAM disponível no início: 3483 MB.

## Parte 2a: ponto de quebra (varredura fina)

| Repetição | Disponível no início | Ponto de quebra | Quebra / disponível | Salto |
|---|---|---|---|---|
| 1 | 4799 MB | não detectado | - | - |
| 2 | 5519 MB | não detectado | - | - |
| 3 | 5512 MB | não detectado | - | - |
## Parte 2b: passo e TLB

| Passo | Páginas distintas | ns/acesso (mediana) | IC 95% |
|---|---|---|---|
| 64 B | 128 | 1.92 | [1.93, 2.09] |
| 256 B | 512 | 2.44 | [2.28, 3.22] |
| 1 KB | 2048 | 3.09 | [2.95, 4.25] |
| 4 KB | 8192 | 4.46 | [4.36, 4.84] |
| 16 KB | 8192 | 5.10 | [4.87, 5.90] |
| 64 KB | 8192 | 7.09 | [6.99, 8.06] |

Pior passo: 64 KB, 3.7x o menor passo. Página desta máquina: 4 KB.

