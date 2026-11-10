# Roteiro do aluno: o penhasco da memória virtual

Duração: 85 min (08h35 às 10h00). Trabalho em duplas, com Pair Programming.

| Horário | Etapa | Entregável parcial |
|---|---|---|
| 08h35 a 08h45 | Preparação | `resultados/identificacao.txt` |
| 08h45 a 09h15 | Parte 1: hipótese e medição guiada | `resultados/02_blocos_<id>.csv` |
| 09h15 a 09h40 | Parte 2: penhasco fino, TLB e gráficos | `resultados/grafico_03_penhasco_<id>.png` |
| 09h40 a 09h52 | Discussão Think-Pair-Share | anotações no relatório |
| 09h52 a 10h00 | Relatório e entrega | `entrega/RELATORIO-<id>.md` |

## Papéis da dupla

- **Piloto**: digita os comandos e edita os arquivos.
- **Navegador**: lê o roteiro em voz alta, confere os checkpoints, anota valores e pensa nas perguntas.

O Navegador não fica parado: é ele quem diz "antes de rodar, qual é a nossa hipótese?".
As trocas de papel estão marcadas com **TROCA DE PAPEL**. Usem uma única máquina para as
medições (a do Piloto da Preparação) para que todos os CSVs sejam da mesma máquina.

## Convenções

- Comandos com o ambiente virtual **ativo** e o terminal na **raiz** do repositório.
- `<id>` é o identificador da dupla (ex.: `dupla07`).
- No Windows, `python` só funciona com o ambiente ativo; fora dele use `py -3`.
- Todo script aceita `--help`. Os de medição aceitam `--rapido` para máquinas lentas.

---

## Preparação (08h35 a 08h45, 10 min)

**Objetivo:** deixar a máquina pronta e registrar o identificador da dupla.

**Papéis:** Aluno A é Piloto; Aluno B é Navegador.

**Comandos:** siga a seção "Instalação" do [README.md](README.md) (clonar, criar e ativar o
`.venv`, `pip install`). Depois:

```
python scripts/00_check_env.py --id <id>
```

**O que observar:** o tamanho da página (4096 bytes na maioria dos PCs; 16384 nos Macs com
Apple Silicon) e a RAM disponível. Anotem os dois.

**Reflexão:** o slide diz que a página tem "tipicamente 4 KB". Qual é o tamanho na sua máquina?

**Checkpoint:** a última linha diz `Ambiente OK` e existe o arquivo `resultados/identificacao.txt`.
Se houver `FALHA`, veja "Problemas comuns" no fim deste roteiro antes de chamar o professor.

---

## Parte 1: hipótese e medição guiada (08h45 a 09h15, 30 min)

### 1.1 Quanta RAM livre você tem de verdade? (08h45 a 08h50)

**Objetivo:** obter a linha de base (o `free -h` do slide) e praticar a leitura da etiqueta DDR.

```
python scripts/01_inspecionar_memoria.py --mts 3200 --cl 16
```

Se o script mostrar a especificação da sua RAM (macOS e Windows costumam mostrar), rode de
novo com a taxa e a CL dela. Se a CL não aparecer, use o exemplo do slide.

**O que observar:**
- "RAM disponível" (available) versus "RAM free". Qual é a que importa e por quê?
- A latência calculada: `T = 2 x CL / (MT/s) x 10^3` ns.

**Reflexão:** uma DDR4-3600 CL18 tem latência menor que uma DDR4-3200 CL16? Calcule com
`--mts 3600 --cl 18` e compare.

**Checkpoint:** existe `resultados/01_memoria_<id>.csv`. A RAM disponível está anotada no relatório.

### 1.2 Hipótese escrita, antes de rodar (08h50 a 08h55)

**Objetivo:** comprometer-se com uma previsão (é ela que torna a medição um experimento).

Vamos alocar e tocar (escrever em) blocos de memória cada vez maiores, medindo o tempo por MB:
256 MB, 512 MB, 1 GB, 2 GB, ... até passar da RAM. Quando o bloco ultrapassar a RAM
disponível, o tempo por MB vai:

- (A) continuar praticamente igual, o SO gerencia isso bem;
- (B) aumentar cerca de 2x, swap em SSD é rápido hoje;
- (C) aumentar de 10x a 100x ou mais;
- (D) diminuir, o SO ativa otimizações para blocos grandes.

Escrevam no relatório (seção 2): a alternativa, **em qual bloco** vocês acham que o tempo vai
mudar (usem a RAM disponível do passo 1.1) e uma frase de justificativa usando a tabela de
latências do slide (RAM: 80 ns; SSD NVMe: 50 000 ns).

**Checkpoint:** a hipótese está escrita no relatório **antes** do passo 1.3.

### 1.3 O experimento (08h55 a 09h07)

**Objetivo:** medir o tempo por MB, os page faults pesados (major faults) e a atividade de swap.

1. Salvem o que estiver aberto e fechem programas pesados.
2. Abram um **segundo terminal**, ativem o ambiente e deixem o monitor rodando:

   ```
   python scripts/monitor_memoria.py
   ```

   As colunas `si`/`so` são MB/s trazidos do swap e enviados para o swap (como no `vmstat 1`).
   No Windows, acompanhem a coluna "swap usado". Quem quiser pode usar também a ferramenta
   nativa (veja "Monitoramento nativo" no fim do roteiro).

3. No primeiro terminal:

   ```
   python scripts/02_tocar_blocos.py
   ```

   Máquina lenta ou com pouca bateria: `python scripts/02_tocar_blocos.py --rapido`.

O script mede cada bloco que cabe na RAM com 1 aquecimento + 5 repetições e mostra mediana e
intervalo de confiança de 95%. Blocos maiores que 80% da RAM disponível rodam uma vez só.
Ele para sozinho no primeiro bloco em que o tempo por MB passar de 10x o dos blocos pequenos,
ou se um bloco passar de 90 s. Em uma máquina de 8 GB leva menos de 1 minuto.

**O que observar:**
- No monitor: a RAM disponível caindo e, nos blocos grandes, `so` (swap out) subindo.
- No resultado: a coluna `ms/MB`. Ela fica estável e de repente salta?
- A coluna `major faults` (no Windows aparece `n/d`, porque o Windows não separa faltas leves de pesadas).

**TROCA DE PAPEL (cerca de 09h00):** Aluno B assume como Piloto a partir daqui.

**Checkpoint:** existem `resultados/02_blocos_<id>.csv` e `resultados/02_blocos_resumo_<id>.csv`.

### 1.4 Registre a medição (09h07 a 09h15)

**Objetivo:** preencher a tabela do slide "Registre a medição".

Copiem para o relatório (seção 3), a partir da saída do 02, uma linha por bloco: ms/MB
(mediana), major faults, swap ativo.

**Reflexão:**
1. Em qual linha o ms/MB explodiu? Comparem com a RAM disponível anotada no passo 1.1.
2. A hipótese de vocês se confirmou? O salto foi de quantas vezes?
3. Por que os blocos pequenos têm intervalo de confiança e os grandes não?

**Checkpoint:** a tabela da seção 3 do relatório está preenchida.

---

## Parte 2: penhasco fino, TLB e gráficos (09h15 a 09h40, 25 min)

### 2.1 Encontre o penhasco (09h15 a 09h25)

**Objetivo:** localizar o ponto de quebra com precisão de 256 MB (item 1 do "Mão na massa").

Em vez de vários blocos, o script reserva uma região grande e a toca em fatias de 256 MB,
medindo cada fatia. As fatias lentas aparecem marcadas com `*`. São 3 varreduras; cada uma
para cerca de 1 GB depois de detectar o penhasco.

```
python scripts/03_penhasco_fino.py
```

Máquina lenta: `python scripts/03_penhasco_fino.py --rapido` (fatias de 512 MB, 2 varreduras).

**O que observar:**
- O ponto de quebra de cada repetição e a razão "quebra / disponível". Bateu com 1,0?
- A coluna "disponível" durante a varredura: ela cai até zero e fica lá, ou o SO "arruma" espaço?
- As três repetições dão o mesmo ponto? Por que a segunda pode ser diferente da primeira?

**Reflexão:** se o penhasco veio bem depois da RAM disponível, de onde o SO tirou memória?
(Pista: olhe o que aconteceu com os outros programas abertos e com o "swap usado" no monitor.)

**Checkpoint:** existem `resultados/03_penhasco_<id>.csv` e `resultados/03_penhasco_resumo_<id>.csv`.

### 2.2 Mate a TLB (09h25 a 09h30)

**Objetivo:** medir o custo de pular de página em página (item 2 do "Mão na massa").

**Antes de rodar**, escrevam no relatório (seção 5): o script faz sempre 8192 leituras, mudando
só o passo entre elas (64 B, 256 B, 1 KB, 4 KB, 16 KB, 64 KB). Com qual passo o custo por
acesso deve subir, considerando o tamanho de página da sua máquina?

```
python scripts/04_passo_tlb.py
```

Leva poucos segundos. Máquina lenta: `--rapido`.

**O que observar:** a coluna "páginas" (quantas páginas distintas as 8192 leituras visitam) e
a coluna `ns/acesso`. O salto acontece onde o número de páginas fica grande demais para a TLB.

**Reflexão:** todas as leituras somam só 512 KB de dados, que cabem no cache. Então por que o
passo grande é mais lento? (Pista: slide "Página, tabela de páginas e TLB".)

**Checkpoint:** existem `resultados/04_passo_<id>.csv` e `resultados/04_passo_resumo_<id>.csv`.

**TROCA DE PAPEL (cerca de 09h30):** Aluno A volta a ser Piloto.

### 2.3 Análise e gráficos (09h30 a 09h40)

**Objetivo:** gerar as estatísticas e os gráficos para o relatório.

```
python scripts/analise.py
```

O script imprime, para cada experimento, média, mediana, desvio-padrão, mínimo, máximo e
IC 95%, e gera em `resultados/`:

- `grafico_02_blocos_<id>.png`: barras de ms/MB por bloco (a versão de vocês do gráfico do slide);
- `grafico_03_penhasco_<id>.png`: ms/MB por fatia (escala log), com a RAM disponível, a RAM total e os pontos de quebra;
- `grafico_04_passo_<id>.png`: ns/acesso por passo, com o tamanho da página marcado;
- `resumo_<id>.md`: tabelas prontas para copiar para o relatório.

**O que observar:** no gráfico 03, há só "rápido" e "lento", ou existe uma zona intermediária
entre a RAM disponível e o penhasco? O eixo y é logarítmico: cada linha de grade é 10x.

**Envio para a turma:** enviem os arquivos `resultados/0*_<id>.csv` (os 01, 02, 03 e 04) para a
pasta compartilhada que o professor indicar. É com eles que a turma compara os três SOs.

**Checkpoint:** existem os três `grafico_0X_..._<id>.png` e o `resumo_<id>.md`, e os CSVs foram enviados.

---

## Discussão Think-Pair-Share (09h40 a 09h52, 12 min)

**Think (09h40 a 09h43, individual):** cada aluno responde sozinho, por escrito:
"O seu serviço está lento. O htop mostra CPU a 30% e swap ativo. Você compra uma CPU melhor ou
mais RAM? Justifique com o **seu** gráfico."

**Pair (09h43 a 09h47):** juntem-se a uma dupla que usou **outro sistema operacional**.
Comparem: base em ms/MB, ponto de quebra / RAM disponível, tamanho do salto e o passo em que a
TLB "morreu". Para comparar no computador, copiem os CSVs da outra dupla para uma pasta (por
exemplo `dados/turma/`) junto com os seus e rodem:

```
python scripts/analise.py --consolidar dados/turma
```

Os gráficos e as tabelas comparativas saem em `resultados/turma/`.

**Share (09h47 a 09h52):** o professor projeta a consolidação da turma inteira. Perguntas-guia:
1. Em qual SO o penhasco aparece mais perto da RAM disponível? Por quê?
2. O salto foi do mesmo tamanho em todos? O que muda entre as máquinas (disco, SO, tamanho da página)?
3. Por que nos Macs com Apple Silicon a TLB "morre" com passo de 16 KB e não de 4 KB?

**Checkpoint:** a seção 6 do relatório tem a resposta individual e uma diferença observada entre SOs.

---

## Relatório e entrega (09h52 a 10h00, 8 min)

1. Copiem `entrega/RELATORIO-MODELO.md` para `entrega/RELATORIO-<id>.md` (se ainda não fizeram).
2. Completem as seções em aberto. O núcleo obrigatório, como no slide: **o gráfico do item 1**
   (`grafico_02_blocos` ou `grafico_03_penhasco`), **o ponto de quebra medido** e **as 4 perguntas respondidas**.
3. Entreguem no canal indicado pelo professor: o relatório, os gráficos 02 e 03 e os CSVs 01 a 04.

**Checkpoint final:** `entrega/RELATORIO-<id>.md` preenchido e enviado.

---

## Desafios extras (opcionais, não entram na entrega)

1. **RAM, arquivo ou mmap** (item 3 do "Mão na massa"). Escreva 100 MB nos três destinos e ordene:

   ```
   python scripts/05_ram_arquivo_mmap.py
   ```

   Relacione a ordem com a tabela de latências do slide. Por que o `fsync` é necessário para medir o disco?

2. **O modo literal do slide.** O padrão dos scripts preenche a página inteira com dados aleatórios.
   O programa em C do slide toca só 1 byte por página. Rode:

   ```
   python scripts/02_tocar_blocos.py --modo pagina
   ```

   O penhasco aparece no seu SO? Compare com uma dupla de outro SO e explique a diferença.
   (Pista: o que um SO pode fazer com uma página que é quase toda zero?)

3. **Contadores de hardware (somente Linux).** Se o `perf` estiver instalado e liberado para o seu usuário:

   ```
   perf stat -e dTLB-load-misses,page-faults,major-faults python scripts/04_passo_tlb.py --passos 64 --repeticoes 5
   perf stat -e dTLB-load-misses,page-faults,major-faults python scripts/04_passo_tlb.py --passos 65536 --repeticoes 5
   ```

   Compare os `dTLB-load-misses`. Se aparecer erro de permissão, o desafio não é possível sem
   administrador; pule.

4. **Refine ainda mais.** Rode o 03 com fatias de 128 MB: `python scripts/03_penhasco_fino.py --passo-mb 128`.
   O ponto de quebra muda? E o intervalo de confiança?

5. **Calculadora DDR.** Monte uma tabela com DDR4-2666 CL19, DDR4-3200 CL16, DDR4-3600 CL18 e
   DDR5-6000 CL30 usando `01_inspecionar_memoria.py --mts ... --cl ...`. Qual tem a menor latência?
   E a maior vazão?

---

## Monitoramento nativo (opcional)

O `monitor_memoria.py` funciona nos três SOs. Se quiser comparar com as ferramentas do sistema:

| SO | RAM disponível | Atividade de swap |
|---|---|---|
| Linux | `free -h` (coluna available) | `vmstat 1` (colunas `si` e `so`); `/usr/bin/time -v python scripts/02_tocar_blocos.py` mostra "Major page faults" |
| macOS | Monitor de Atividade > Memória ("Pressão de memória", "Comprimida", "Swap usado") | `vm_stat 1` (colunas `swapins`/`swapouts`); `sysctl vm.swapusage` |
| Windows | Gerenciador de Tarefas > Desempenho > Memória ("Disponível", "Em uso (Compactada)") | Monitor de Recursos (`resmon`) > Memória, coluna "Falhas Graves/s" |

---

## Problemas comuns

### Todos os SOs

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ERRO: a biblioteca 'psutil' não foi encontrada` | ambiente virtual não ativo | ative o `.venv` (o prompt deve mostrar `(.venv)`) |
| `identificador da dupla não definido` | o 00 não foi rodado com `--id` | `python scripts/00_check_env.py --id <id>` |
| `can't open file ... scripts/...` | terminal fora da raiz do repositório | `cd` para a pasta `pratica-memoria-virtual` |
| O 03 diz "penhasco não detectado" | a máquina tem muita RAM livre, ou (Linux) pouco swap em disco para atravessar a RAM | rode `--limite 1.5`; se ainda não detectar, registre isso no relatório (também é resultado) e use os números de uma dupla vizinha na discussão |
| Programas abertos ficam lentos depois do teste | as páginas deles foram para o swap | normal; espere alguns segundos |
| O bloco grande é "interrompido (tempo máximo)" | swap lento (HDD ou disco cheio) | é o penhasco; anote. Não aumente o `--tempo-max` |

### Windows

| Sintoma | O que fazer |
|---|---|
| `python` abre a Microsoft Store ou "não é reconhecido" | use `py -3` para criar o ambiente; depois de ativado, `python` funciona. Ou desative o alias em Configurações > Aplicativos > Aliases de execução |
| `Activate.ps1 não pode ser carregado porque a execução de scripts foi desabilitada` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (vale só para essa janela, sem administrador) |
| Acentos aparecem trocados no terminal | use o Windows Terminal ou rode `chcp 65001` antes; os CSVs não são afetados |
| `não foi possível alocar ... arquivo de paginação` | o Windows não comportou o bloco; o script tenta tamanhos menores. Se persistir: `--limite 1.0` |
| Colunas `major faults`, `si`, `so` aparecem como `n/d` | o Windows não expõe esses contadores sem privilégios; use "swap usado" e o `resmon` |
| Antivírus deixa o `pip install` muito lento | aguarde; ou instale fora do OneDrive (pastas sincronizadas são lentas) |

### macOS

| Sintoma | O que fazer |
|---|---|
| `python: command not found` | use `python3` para criar o ambiente; depois de ativado, `python` funciona |
| Aparece um pedido para instalar "ferramentas de linha de comando" | aceite (ou instale o Python de python.org) e repita |
| "Terminal deseja acessar arquivos na pasta Downloads/Documentos" | clique em Permitir; ou clone o repositório na sua pasta de usuário |
| O penhasco vem muito depois da RAM disponível | esperado no macOS: ele comprime a memória dos outros programas antes de usar o swap. Discuta no relatório |
| Página de 16384 bytes | normal em Apple Silicon (M1, M2, ...). Os scripts usam o tamanho real |

### Linux

| Sintoma | O que fazer |
|---|---|
| `ensurepip is not available` / falta `python3-venv` | peça ao monitor; sem administrador, use `python3 -m pip install --user -r requirements.txt` e rode os scripts com `python3` |
| AVISO "sem swap" no 00 | sem swap o kernel encerra o processo ao passar da RAM (OOM killer). O script para em 90% da disponível; o penhasco não aparece. Junte-se a outra dupla para a Parte 1 |
| O processo some com a mensagem `Killed` | foi o OOM killer. As medições até ali estão salvas no CSV. Rode de novo com `--limite 1.0` |
| AVISO "Swap em zram detectado" (Fedora e outras) | o zram comprime o swap dentro da própria RAM e não ajuda com os dados deste teste; o limite considera só o swap em disco. Se houver pouco swap em disco, o penhasco pode aparecer só nas últimas fatias. Anote no relatório |
| WSL | prefira rodar no Windows nativo: o WSL tem um limite de memória próprio |
