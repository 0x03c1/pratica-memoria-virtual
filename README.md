# Prática: memória virtual e o penhasco do swap

Infraestrutura de Hardware, Aula 13 (Memória Principal e Memória Virtual).

Nesta prática você vai provocar, de forma controlada, o momento em que a memória de um
programa deixa de caber na RAM, e medir o que acontece com o desempenho. Também vai medir o
custo de "pular de página em página" (a TLB). Tudo roda em macOS, Windows e Linux, com
Python, sem privilégio de administrador.

## A atividade, em 4 passos

| # | O que fazer | Onde |
|---|---|---|
| 1 | Instalar e verificar o ambiente | seção [Instalação](#instalação) deste README |
| 2 | Seguir o roteiro, em dupla | [ROTEIRO.md](ROTEIRO.md) |
| 3 | Preencher o relatório, ao longo da aula | copie [entrega/RELATORIO-MODELO.md](entrega/RELATORIO-MODELO.md) para `entrega/RELATORIO-<id>.md` |
| 4 | Entregar | canal indicado pelo professor |

### O que entregar

| Item | Arquivo (gerado por você) |
|---|---|
| Relatório preenchido | `entrega/RELATORIO-<id>.md` |
| Gráfico do penhasco | `resultados/grafico_02_blocos_<id>.png` e `resultados/grafico_03_penhasco_<id>.png` |
| Medições | `resultados/01_memoria_<id>.csv`, `02_blocos_<id>.csv`, `03_penhasco_<id>.csv`, `04_passo_<id>.csv` |

O núcleo obrigatório do relatório: o gráfico, o ponto de quebra medido e as 4 perguntas respondidas.
`<id>` é o identificador da dupla que o professor passar (ex.: `dupla07`).

## Onde está cada coisa

| Caminho | O que é | Você mexe? |
|---|---|---|
| `README.md` | este arquivo: atividade, instalação, mapa | não |
| `ROTEIRO.md` | passo a passo da aula, com tempos, checkpoints, desafios e problemas comuns por SO | não, só lê |
| `requirements.txt` | dependências com versões fixadas | não |
| `scripts/00_check_env.py` | verifica Python, dependências, SO, CPU, memória; salva o seu `id` | roda |
| `scripts/01_inspecionar_memoria.py` | RAM total e disponível, swap, página; calculadora DDR | roda |
| `scripts/02_tocar_blocos.py` | Parte 1: blocos cada vez maiores, tempo por MB | roda |
| `scripts/03_penhasco_fino.py` | Parte 2: localiza o ponto de quebra em fatias de 256 MB | roda |
| `scripts/04_passo_tlb.py` | Parte 2: custo por acesso conforme o passo (TLB) | roda |
| `scripts/05_ram_arquivo_mmap.py` | desafio opcional: RAM, arquivo ou mmap | roda (opcional) |
| `scripts/monitor_memoria.py` | RAM e swap a cada segundo, num segundo terminal | roda |
| `scripts/analise.py` | estatísticas, gráficos e comparação entre máquinas | roda |
| `scripts/comum.py` | funções compartilhadas pelos scripts | não |
| `dados/exemplo/` | medições de referência dos três SOs (leia o [LEIAME](dados/exemplo/LEIAME.md): só o macOS é medição real) | só consulta |
| `resultados/` | tudo o que os scripts geram (CSV, PNG, resumos); não vai para o Git | é gerado |
| `entrega/RELATORIO-MODELO.md` | modelo do relatório | copia e preenche |

## Atenção antes de rodar

Os scripts `02_tocar_blocos.py` e `03_penhasco_fino.py` deixam a máquina lenta **de propósito**
por alguns segundos.

- Salve seus arquivos e feche programas pesados (navegador com muitas abas, IDEs, jogos).
- Não rode em servidor de produção nem em máquina compartilhada.
- Os scripts param sozinhos logo depois de encontrar o penhasco, e cada bloco tem tempo
  máximo. `Ctrl+C` interrompe a qualquer momento sem perder o que já foi medido.
- Depois do teste, os programas que você deixou abertos podem demorar alguns segundos para
  "acordar" (as páginas deles foram para o swap). Isso é esperado.

## Pré-requisitos

- Python 3.10 ou mais novo (3.12 ou mais novo é o recomendado).
- Git (ou baixe o ZIP pelo botão "Code" do GitHub).
- Cerca de 10 GB livres em disco (o swap usa o disco).
- Uns 300 MB para as dependências (`psutil`, `numpy`, `matplotlib`).

## Instalação

### 1. Obter o repositório

```
git clone https://github.com/0x03c1/pratica-memoria-virtual.git
cd pratica-memoria-virtual
```

Sem Git: botão "Code" > "Download ZIP", extraia e abra um terminal dentro da pasta extraída.

### 2. Criar e ativar o ambiente virtual

**Linux e macOS** (Terminal)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows** (PowerShell)

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se o PowerShell recusar a ativação ("a execução de scripts foi desabilitada"), rode uma vez,
sem precisar de administrador, e repita a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

No Prompt de Comando (cmd) use `.venv\Scripts\activate.bat`.

Se o comando `py` não existir, crie o ambiente com `python -m venv .venv`. Evite `python3` no
Windows: o instalador do python.org não cria esse comando, e ele abre a Microsoft Store.

Com o ambiente ativo, o prompt mostra `(.venv)` e o comando `python` funciona igual nos três
sistemas. Todos os comandos do roteiro assumem o ambiente ativo e o terminal na raiz do repositório.

### 3. Verificar o ambiente

```
python scripts/00_check_env.py --id dupla07
```

Troque `dupla07` pelo seu identificador (só letras, números, `-` e `_`). O resultado deve
terminar com `Ambiente OK`. Linhas `AVISO` não impedem a prática; linhas `FALHA` impedem e
trazem a instrução de correção. Em caso de dúvida, veja "Problemas comuns" no fim do ROTEIRO.

Pronto: continue pelo [ROTEIRO.md](ROTEIRO.md). Todos os scripts aceitam `--help`, e os de
medição aceitam `--rapido` para máquinas lentas.

## Arquivos gerados em `resultados/`

| Arquivo | Gerado por |
|---|---|
| `identificacao.txt` | 00 |
| `01_memoria_<id>.csv` | 01 |
| `02_blocos_<id>.csv`, `02_blocos_resumo_<id>.csv` | 02 |
| `03_penhasco_<id>.csv`, `03_penhasco_resumo_<id>.csv` | 03 |
| `04_passo_<id>.csv`, `04_passo_resumo_<id>.csv` | 04 |
| `05_ram_arquivo_mmap_<id>.csv`, `05_ram_arquivo_mmap_resumo_<id>.csv` | 05 (desafio) |
| `analise_0X_..._<id>.csv`, `grafico_0X_..._<id>.png`, `resumo_<id>.md` | analise.py |
| `turma/` | analise.py --consolidar |

Cada linha de CSV traz os metadados da máquina (SO, versão, CPU, núcleos, RAM, tamanho da
página, versão do Python, data/hora, script e parâmetros). Rodar um script de novo sobrescreve
o CSV daquele script para o mesmo `id`.
