# Relatório: o penhasco da memória virtual

Copie este arquivo para `entrega/RELATORIO-<id>.md` e preencha. Seja breve: o relatório
cabe em uma página. Valores e tabelas prontos estão em `resultados/resumo_<id>.md`.

## 1. Identificação

- Dupla (id): 4819
- Integrantes: Jose Milton e Luiza Costa
- SO e versão: Windows 11
- CPU: Intel Core i5-11400H (11ª geração)
- RAM total: 31,78 GB
- RAM disponível (available) no passo 1.1: 19,29 GB
- Tamanho da página: 4096 B

## 2. Hipótese (escrita ANTES de rodar o 02)

- Alternativa escolhida (A, B, C ou D): B
- Bloco em que esperamos o salto: 32 GB
- Justificativa (1 frase, usando a tabela de latências do slide): Apesar do acesso ao SSD ser mais lento que a RAM, acreditamos que a velocidade do SSD atual limitará o aumento do tempo 

## 3. Medição: tabela do slide (saída do 02)

| Bloco | ms/MB (mediana) | major faults | swap ativo? |
|---|---|---|---|
| 256 MB | 0,338 | n/d |Nao |
| 512 MB | 0,345 | n/d | Nao |
| 1 GB | 0,328 | n/d | Nao |
| 2 GB | 0,323 | n/d | Nao |
| 4 GB | 0,280| n/d | Nao |
| 8 GB | 0,280 | n/d | Nao |

Em qual linha o ms/MB explodiu? 32GB           Salto em relação aos blocos pequenos: 2,8x

A hipótese se confirmou? (sim/não e por quê, 1 frase): Sim, aproximadamente. O tempo por MB aumentou cerca de 2,8 vezes no bloco de 32 GB, próximo da previsão de aumento de 2 vezes.

## 4. Ponto de quebra (saída do 03) e gráfico

- Ponto de quebra (mediana das repetições): 33920 MB
- IC 95% do ponto de quebra:  [3019, 64821] MB
- Quebra / RAM disponível: 1,10 (1,0 significa "bateu")
- Bateu com a RAM disponível?  Não exatamente. O ponto de quebra ficou acima da RAM disponível, pois o Windows também utiliza memória virtual e paginação, permitindo ultrapassar a RAM física antes de ocorrer uma degradação acentuada.

![grafico](resultados/grafico_03_penhasco_4819.png)

## 5. TLB (saída do 04)

- Previsão antes de rodar: o custo sobe a partir do passo de 4096 bytes.
- Resultado: o custo sobe a partir do passo de 4096 bytes (4 KB), aproximadamente 1,93x em relação ao passo de 1024 bytes.
- Explicação (1 a 2 frases): - Conforme o passo entre os acessos aumenta, o programa passa a acessar regiões mais distantes da memória, aumentando a possibilidade de ocorrerem TLB misses. Isso exige novas consultas às tabelas de páginas, aumentando o tempo médio de acesso à memória.

## 6. Discussão (Think-Pair-Share)

- Resposta individual (CPU melhor ou mais RAM? Use o gráfico):  Escolheria aumentar a quantidade de RAM, pois os resultados demonstraram que o desempenho caiu significativamente quando o bloco atingiu 32 GB, momento em que o swap ficou ativo. Nesse cenário, uma CPU melhor não resolveria o gargalo causado pela falta de memória física, enquanto mais RAM permitiria manter mais dados disponíveis sem depender tanto da memória virtual.
- Uma diferença observada em relação à dupla de outro SO, e uma explicação: Comparando os resultados do Windows com os da dupla que utilizou macOS, observamos que o ponto de quebra ocorreu em 11776MB no outro sistema, enquanto no nosso experimento foi de 33.920 MB. Essa diferença pode estar relacionada ao gerenciamento de memória virtual, à utilização da RAM pelo próprio sistema operacional e às estratégias de paginação de cada sistema.

## 7. As 4 perguntas obrigatórias

1. **O que foi medido?** Foi medido o desempenho do acesso à memória em diferentes situações, analisando o tempo necessário para processar blocos de tamanhos variados, o ponto em que ocorre uma queda significativa de desempenho e o custo dos acessos conforme aumenta o passo entre eles, relacionado ao funcionamento da TLB.

2. **Como foi medido?** (ferramenta, métrica, repetições, o que confirma o swap): As medições foram realizadas por meio de scripts em Python fornecidos na atividade. Foram analisados o tempo por MB nos testes de blocos, o ponto de quebra do desempenho e o tempo por acesso no experimento da TLB. Os testes utilizaram repetições e medianas para reduzir a influência de variações momentâneas. Também foi observado o estado do swap durante os experimentos. No Windows, a quantidade de major faults não foi disponibilizada pelo script, sendo registrada como não disponível.

3. **Por que esse resultado?** (use os termos minor fault, major fault e swap): O desempenho caiu porque, ao aumentar a quantidade de dados, o sistema passou a sofrer maior pressão sobre a memória RAM. Quando a memória física se torna insuficiente, o sistema operacional pode utilizar o swap, movimentando páginas entre a RAM e o armazenamento secundário. Esse processo pode provocar major faults, que possuem um custo maior que os minor faults, aumentando o tempo de acesso e prejudicando o desempenho. No nosso experimento, essa situação ficou evidente no bloco de 32 GB, quando o tempo por MB aumentou aproximadamente três vezes e o swap ficou ativo.

4. **Qual teoria explica?** Os resultados são explicados pela teoria de memória virtual, paginação e hierarquia de memória. A memória virtual permite que o sistema operacional gerencie espaços de memória maiores que a RAM física, utilizando o armazenamento secundário como apoio. Entretanto, como o SSD possui latência maior que a RAM, a movimentação frequente de páginas pode provocar uma queda significativa no desempenho. Além disso, a TLB acelera a tradução de endereços virtuais para físicos, reduzindo o custo dos acessos à memória.
