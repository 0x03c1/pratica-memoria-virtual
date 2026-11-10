# Dados de exemplo

Medições de referência no mesmo formato que os scripts geram. Servem para conhecer os
arquivos, testar a análise e comparar com os seus números. **Não use estes dados como se fossem
seus no relatório.**

| Pasta | Origem | Máquina |
|---|---|---|
| `macos-m1-8gb-real/` | **medição real**, feita com os scripts deste repositório | macOS 27.2, Apple M1, 8 GB, página de 16 KB, Python 3.15 |
| `linux-x86-8gb-SINTETICO/` | **dados sintéticos** (ilustrativos, não medidos) | Linux x86, 8 GB, página de 4 KB (hipotética) |
| `windows-x86-8gb-SINTETICO/` | **dados sintéticos** (ilustrativos, não medidos) | Windows 11 x86, 8 GB, página de 4 KB (hipotética) |

Os dados sintéticos foram gerados a partir das faixas de valores esperadas para cada SO, para
mostrar o formato dos arquivos e o comportamento qualitativo que a teoria prevê. Eles são
identificados em todas as linhas: o `id` termina em `SINTETICO`, a coluna `cpu` começa com
`SINTETICO` e a coluna `parametros` começa com `SINTETICO=1`. Serão substituídos por medições
reais da turma.

## Como usar

Comparar os três SOs (gera tabelas e gráficos em `resultados/turma/`):

```
python scripts/analise.py --consolidar dados/exemplo
```

Ver a análise individual da medição real do macOS:

```
python scripts/analise.py --pasta dados/exemplo/macos-m1-8gb-real --id exemplo-macos-m1
```

Em ambos os casos a saída (tabelas, gráficos e `resumo_<id>.md`) vai para `resultados/`; esta
pasta não é alterada.
