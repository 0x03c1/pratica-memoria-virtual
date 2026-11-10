# Relatório: o penhasco da memória virtual

Copie este arquivo para `entrega/RELATORIO-<id>.md` e preencha. Seja breve: o relatório
cabe em uma página. Valores e tabelas prontos estão em `resultados/resumo_<id>.md`.

## 1. Identificação

- Dupla (id):
- Integrantes:
- SO e versão:
- CPU:
- RAM total:                GB
- RAM disponível (available) no passo 1.1:                GB
- Tamanho da página:                bytes

## 2. Hipótese (escrita ANTES de rodar o 02)

- Alternativa escolhida (A, B, C ou D):
- Bloco em que esperamos o salto:
- Justificativa (1 frase, usando a tabela de latências do slide):

## 3. Medição: tabela do slide (saída do 02)

| Bloco | ms/MB (mediana) | major faults | swap ativo? |
|---|---|---|---|
| 256 MB | | | |
| 512 MB | | | |
| 1 GB | | | |
| 2 GB | | | |
| 4 GB | | | |
| 8 GB | | | |

Em qual linha o ms/MB explodiu?            Salto em relação aos blocos pequenos:           x

A hipótese se confirmou? (sim/não e por quê, 1 frase):

## 4. Ponto de quebra (saída do 03) e gráfico

- Ponto de quebra (mediana das repetições):            MB
- IC 95% do ponto de quebra:  [            ,            ] MB
- Quebra / RAM disponível:            (1,0 significa "bateu")
- Bateu com a RAM disponível? Se não, por quê?

Gráfico (cole a imagem ou indique o arquivo enviado):

![grafico](../resultados/grafico_03_penhasco_<id>.png)

## 5. TLB (saída do 04)

- Previsão antes de rodar: o custo sobe a partir do passo de            bytes.
- Resultado: o custo sobe a partir do passo de            bytes,            x o passo de 64 B.
- Explicação (1 a 2 frases):

## 6. Discussão (Think-Pair-Share)

- Resposta individual (CPU melhor ou mais RAM? Use o gráfico):
- Uma diferença observada em relação à dupla de outro SO, e uma explicação:

## 7. As 4 perguntas obrigatórias

1. **O que foi medido?**

2. **Como foi medido?** (ferramenta, métrica, repetições, o que confirma o swap)

3. **Por que esse resultado?** (use os termos minor fault, major fault e swap)

4. **Qual teoria explica?**
