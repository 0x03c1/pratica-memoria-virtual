"""Análise: lê os CSVs, calcula estatísticas e gera gráficos em resultados/.

Modo individual (sua dupla):
    python scripts/analise.py
    python scripts/analise.py --id dupla07

Modo consolidação (turma): junta CSVs de várias máquinas e compara os SOs.
    python scripts/analise.py --consolidar pasta_da_turma
    python scripts/analise.py --consolidar pasta1 pasta2 resultados
A pasta pode ter subpastas; são lidos os arquivos 02_blocos_*.csv, 03_penhasco_*.csv
e 04_passo_*.csv (os *_resumo_* são ignorados, pois tudo é recalculado).
Saída da consolidação: resultados/turma/.
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

try:
    import matplotlib

    matplotlib.use("Agg")  # gera arquivos PNG sem abrir janelas (funciona em qualquer SO)
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
except ImportError:
    comum.erro("matplotlib não encontrado. Ative o ambiente virtual e rode: python -m pip install -r requirements.txt")

# Aparência: cores fixas por SO (a cor segue o SO, nunca a ordem), traços finos, grade discreta.
CORES_SO = {"Linux": "#2a78d6", "macOS": "#eb6834", "Windows": "#1baf7a"}
CORES_SERIE = ["#2a78d6", "#eb6834", "#1baf7a"]
COR_OUTRA = "#8a8984"
TEXTO, TEXTO_2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
    "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO_2, "axes.titlecolor": TEXTO,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.labelsize": 10,
    "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "grid.color": GRADE, "grid.linewidth": 0.8,
    "axes.grid": True, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "font.size": 10, "lines.linewidth": 2,
})


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def num(valor, padrao=None):
    try:
        x = float(valor)
        return padrao if math.isnan(x) else x
    except (TypeError, ValueError):
        return padrao


def parametro(linha: dict, nome: str, padrao: float) -> float:
    for parte in linha.get("parametros", "").split():
        if parte.startswith(nome + "="):
            return num(parte.split("=", 1)[1], padrao)
    return padrao


def rel(caminho: Path) -> str:
    """Caminho relativo ao repositório quando possível (fica mais curto na tela)."""
    try:
        return str(caminho.relative_to(comum.RAIZ))
    except ValueError:
        return str(caminho)


def salvar_figura(fig, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(caminho, dpi=130)
    plt.close(fig)
    print(f"  gráfico: {rel(caminho)}")


def rotulo_mb(mb: float) -> str:
    if mb >= 1024:
        gb = mb / 1024
        return f"{gb:g} GB" if gb == int(gb) else f"{gb:.1f} GB"
    return f"{mb:.0f} MB"


def titulo(ax, principal: str, ident: str, so: str) -> None:
    """Título à esquerda e, abaixo dele, a identificação da máquina em cinza."""
    ax.set_title(principal, loc="left", pad=20)
    ax.text(0, 1.02, f"{ident} | {so}", transform=ax.transAxes, color=TEXTO_2, fontsize=9)


def rotulo_bytes(b: float) -> str:
    return f"{b / 1024:g} KB" if b >= 1024 else f"{b:g} B"


# ---------------------------------------------------------------------------
# Cálculos (servem para o modo individual e para a turma)
# ---------------------------------------------------------------------------
def analisar_blocos(linhas: list[dict]) -> dict:
    por_tamanho = defaultdict(list)
    for l in linhas:
        por_tamanho[int(num(l["tamanho_mb"]))].append(l)
    disp = num(linhas[0]["disponivel_inicial_mb"])
    tabela = []
    for tam in sorted(por_tamanho):
        grupo = por_tamanho[tam]
        est = comum.estatisticas([num(g["ms_por_mb"]) for g in grupo])
        maiores = [num(g["faltas_maiores"]) for g in grupo if num(g["faltas_maiores"]) is not None]
        swap_ativo = any(comum.houve_swap(num(g["swap_out_delta_mb"]), num(g["swap_usado_delta_mb"]))
                         for g in grupo)
        tabela.append({"tamanho_mb": tam, **est,
                       "faltas_maiores_media": statistics.fmean(maiores) if maiores else "",
                       "swap_ativo": "sim" if swap_ativo else "não",
                       "acima_da_disponivel": "sim" if tam > disp else "não"})
    base_lista = [t["mediana"] for t in tabela if t["n"] > 1] or [tabela[0]["mediana"]]
    base = statistics.median(base_lista)
    pior = max(tabela, key=lambda t: t["mediana"])
    return {"tabela": tabela, "disponivel_mb": disp, "base": base,
            "pior_tamanho_mb": pior["tamanho_mb"], "razao_salto": pior["mediana"] / base}


def analisar_penhasco(linhas: list[dict]) -> dict:
    """Recalcula o ponto de quebra de cada repetição a partir da coluna 'lenta'."""
    consecutivas = int(parametro(linhas[0], "consecutivas", 3))
    por_rep = defaultdict(list)
    for l in linhas:
        por_rep[int(num(l["repeticao"]))].append(l)
    reps = []
    for rep in sorted(por_rep):
        fatias = sorted(por_rep[rep], key=lambda l: num(l["inicio_mb"]))
        disp = num(fatias[0]["disponivel_inicial_mb"])
        seguidas, quebra = 0, None
        for i, f in enumerate(fatias):
            seguidas = seguidas + 1 if f["lenta"] == "1" else 0
            if seguidas >= consecutivas:
                quebra = num(fatias[i - consecutivas + 1]["inicio_mb"])
                break
        if quebra is None and seguidas >= 1:  # mesma regra do 03: fatias lentas no fim da varredura
            quebra = num(fatias[len(fatias) - seguidas]["inicio_mb"])
        ms = [num(f["ms_por_mb"]) for f in fatias]
        base = comum.base_penhasco(ms, [num(f["fim_mb"]) for f in fatias], disp)  # mesma regra do 03
        r = {"repeticao": rep, "disponivel_mb": disp, "base": base, "quebra_mb": quebra,
             "x": [num(f["fim_mb"]) for f in fatias], "y": ms}
        if quebra is not None:
            pos = [num(f["ms_por_mb"]) for f in fatias if num(f["inicio_mb"]) >= quebra]
            r["pos_quebra"] = statistics.median(pos)
            r["razao_salto"] = r["pos_quebra"] / base
        reps.append(r)
    quebras = [r["quebra_mb"] for r in reps if r["quebra_mb"] is not None]
    return {"reps": reps, "ram_total_mb": num(linhas[0]["ram_total_mb"]),
            "quebra_est": comum.estatisticas(quebras),
            "disponivel_est": comum.estatisticas([r["disponivel_mb"] for r in reps]),
            "razao_est": comum.estatisticas([r["razao_salto"] for r in reps if "razao_salto" in r])}


def analisar_passo(linhas: list[dict]) -> dict:
    por_passo = defaultdict(list)
    paginas = {}
    for l in linhas:
        p = int(num(l["passo_bytes"]))
        por_passo[p].append(num(l["ns_por_acesso"]))
        paginas[p] = int(num(l["paginas_distintas"]))
    tabela = [{"passo_bytes": p, "paginas_distintas": paginas[p], **comum.estatisticas(v)}
              for p, v in sorted(por_passo.items())]
    menor = tabela[0]["mediana"]
    pior = max(tabela, key=lambda t: t["mediana"])
    return {"tabela": tabela, "pagina": int(num(linhas[0]["tamanho_pagina_bytes"])),
            "razao_tlb": pior["mediana"] / menor, "pior_passo": pior["passo_bytes"]}


# ---------------------------------------------------------------------------
# Gráficos individuais
# ---------------------------------------------------------------------------
def grafico_blocos(res: dict, ident: str, so: str, destino: Path) -> None:
    t = res["tabela"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = list(range(len(t)))
    meds = [r["mediana"] for r in t]
    erros = [[max(0.0, r["mediana"] - r["ic95_inf"]) if r["n"] > 1 else 0 for r in t],
             [max(0.0, r["ic95_sup"] - r["mediana"]) if r["n"] > 1 else 0 for r in t]]
    cores = [CORES_SERIE[0] if r["acima_da_disponivel"] == "não" else CORES_SERIE[1] for r in t]
    ax.bar(xs, meds, width=0.6, color=cores, yerr=erros, ecolor=TEXTO_2, capsize=3)
    for x, m in zip(xs, meds):
        ax.annotate(f"{m:.2f}", (x, m), xytext=(0, 4), textcoords="offset points", ha="center",
                    color=TEXTO, fontsize=9)
    ax.set_xticks(xs, [rotulo_mb(r["tamanho_mb"]) for r in t])
    ax.set_xlabel("Bloco alocado e tocado")
    ax.set_ylabel("ms por MB tocado (mediana)")
    titulo(ax, "O penhasco: tempo por MB conforme o bloco cresce", ident, so)
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Line2D([], [], color=CORES_SERIE[0], lw=8, label="bloco cabe na RAM disponível"),
                       Line2D([], [], color=CORES_SERIE[1], lw=8,
                              label=f"bloco maior que a disponível ({rotulo_mb(round(res['disponivel_mb']))})")],
              loc="upper left")
    salvar_figura(fig, destino)


def grafico_penhasco(res: dict, ident: str, so: str, destino: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, r in enumerate(res["reps"]):
        cor = CORES_SERIE[i] if i < len(CORES_SERIE) else COR_OUTRA
        ax.plot([x / 1024 for x in r["x"]], r["y"], color=cor, lw=1.6, marker="o", ms=3,
                label=f"repetição {r['repeticao']}")
        if r["quebra_mb"] is not None:
            ax.axvline(r["quebra_mb"] / 1024, color=cor, ls=":", lw=1.2)
    disp = res["reps"][0]["disponivel_mb"] / 1024
    ax.axvline(disp, color=TEXTO_2, ls="--", lw=1.2)
    ax.annotate("RAM disponível\nno início", (disp, 1), xycoords=("data", "axes fraction"),
                xytext=(4, -4), textcoords="offset points", va="top", fontsize=8, color=TEXTO_2)
    ax.axvline(res["ram_total_mb"] / 1024, color=TEXTO, ls="-.", lw=1)
    ax.annotate("RAM total", (res["ram_total_mb"] / 1024, 1), xycoords=("data", "axes fraction"),
                xytext=(4, -4), textcoords="offset points", va="top", fontsize=8, color=TEXTO)
    ax.set_yscale("log")
    ax.set_xlabel("Memória já tocada (GB)")
    ax.set_ylabel("ms por MB (escala log)")
    titulo(ax, "Varredura fina: onde a memória deixa de caber", ident, so)
    ax.legend(loc="upper left", title="pontilhado = ponto de quebra", title_fontsize=8)
    salvar_figura(fig, destino)


def grafico_passo(res: dict, ident: str, so: str, destino: Path) -> None:
    t = res["tabela"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = [r["passo_bytes"] for r in t]
    meds = [r["mediana"] for r in t]
    erros = [[max(0.0, r["mediana"] - r["ic95_inf"]) for r in t], [max(0.0, r["ic95_sup"] - r["mediana"]) for r in t]]
    ax.errorbar(xs, meds, yerr=erros, color=CORES_SERIE[0], marker="o", ms=6, capsize=3)
    for r in t:
        ax.annotate(f"{r['paginas_distintas']} pág.", (r["passo_bytes"], r["mediana"]), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8, color=TEXTO_2)
    ax.axvline(res["pagina"], color=TEXTO_2, ls="--", lw=1.2)
    ax.annotate(f"tamanho da página\n({rotulo_bytes(res['pagina'])})", (res["pagina"], 0.05),
                xycoords=("data", "axes fraction"), xytext=(4, 0), textcoords="offset points", fontsize=8,
                color=TEXTO_2)
    ax.set_xscale("log", base=2)
    ax.set_xticks(xs, [rotulo_bytes(x) for x in xs])
    ax.set_ylim(0, max(r["ic95_sup"] for r in t) * 1.18)
    ax.set_xlabel("Passo entre leituras (mesmo número de leituras em todos)")
    ax.set_ylabel("ns por acesso (mediana, IC 95%)")
    titulo(ax, "Mate a TLB: custo por acesso conforme o passo", ident, so)
    salvar_figura(fig, destino)


# ---------------------------------------------------------------------------
# Modo individual
# ---------------------------------------------------------------------------
def modo_individual(pasta: Path, ident: str) -> int:
    saida = comum.RESULTADOS  # a saída vai sempre para resultados/, mesmo lendo de outra pasta
    saida.mkdir(exist_ok=True)
    print(f"Analisando os resultados de '{ident}' em {pasta}\n")
    linhas_md = [f"# Resumo dos resultados: {ident}", ""]
    achou = False

    arq = pasta / f"01_memoria_{ident}.csv"
    if arq.exists():
        m = comum.ler_csv(arq)[0]
        linhas_md += [f"- Máquina: {m['so']} ({m['so_versao']}), {m['cpu']}, RAM {num(m['ram_total_mb']) / 1024:.1f} GB,"
                      f" página {m['tamanho_pagina_bytes']} bytes",
                      f"- RAM disponível anotada na etapa 1: {num(m['ram_disponivel_mb']) / 1024:.2f} GB", ""]

    arq = pasta / f"02_blocos_{ident}.csv"
    if arq.exists() and (linhas := comum.ler_csv(arq)):
        achou = True
        so = linhas[0]["so"]
        res = analisar_blocos(linhas)
        campos = ["tamanho_mb", "n", "media", "mediana", "desvio", "minimo", "maximo", "ic95_inf", "ic95_sup",
                  "faltas_maiores_media", "swap_ativo", "acima_da_disponivel"]
        comum.salvar_csv(saida / f"analise_02_blocos_{ident}.csv", res["tabela"], campos)
        print("Parte 1: blocos")
        print(f"  {'bloco':>8} | {'n':>2} | {'média':>7} | {'mediana':>7} | {'desvio':>7} | {'mín':>7} | {'máx':>7} | IC 95%")
        linhas_md += ["## Parte 1: blocos (tabela do slide)", "",
                      "| Bloco | ms/MB (mediana) | IC 95% | major faults | swap ativo? |", "|---|---|---|---|---|"]
        for r in res["tabela"]:
            ic = f"[{comum.fmt(r['ic95_inf'])}, {comum.fmt(r['ic95_sup'])}]" if r["n"] > 1 else "1 execução"
            print(f"  {rotulo_mb(r['tamanho_mb']):>8} | {r['n']:>2} | {r['media']:7.3f} | {r['mediana']:7.3f} | "
                  f"{r['desvio']:7.3f} | {r['minimo']:7.3f} | {r['maximo']:7.3f} | {ic}")
            maj = f"{r['faltas_maiores_media']:.0f}" if r["faltas_maiores_media"] != "" else "n/d"
            linhas_md.append(f"| {rotulo_mb(r['tamanho_mb'])} | {r['mediana']:.3f} | {ic} | {maj} | {r['swap_ativo']} |")
        msg = (f"Base (blocos que cabem): {res['base']:.3f} ms/MB; pior bloco {rotulo_mb(res['pior_tamanho_mb'])}:"
               f" {res['razao_salto']:.0f}x a base. RAM disponível no início: {res['disponivel_mb']:.0f} MB.")
        print("  " + msg)
        linhas_md += ["", msg, ""]
        grafico_blocos(res, ident, so, saida / f"grafico_02_blocos_{ident}.png")
        print()

    arq = pasta / f"03_penhasco_{ident}.csv"
    if arq.exists() and (linhas := comum.ler_csv(arq)):
        achou = True
        so = linhas[0]["so"]
        res = analisar_penhasco(linhas)
        print("Parte 2a: penhasco fino")
        linhas_md += ["## Parte 2a: ponto de quebra (varredura fina)", "",
                      "| Repetição | Disponível no início | Ponto de quebra | Quebra / disponível | Salto |",
                      "|---|---|---|---|---|"]
        tabela = []
        for r in res["reps"]:
            if r["quebra_mb"] is None:
                print(f"  rep {r['repeticao']}: penhasco não detectado")
                linhas_md.append(f"| {r['repeticao']} | {r['disponivel_mb']:.0f} MB | não detectado | - | - |")
                continue
            print(f"  rep {r['repeticao']}: quebra em {r['quebra_mb']:.0f} MB (disponível {r['disponivel_mb']:.0f} MB,"
                  f" razão {r['quebra_mb'] / r['disponivel_mb']:.2f}); salto {r['razao_salto']:.0f}x")
            linhas_md.append(f"| {r['repeticao']} | {r['disponivel_mb']:.0f} MB | {r['quebra_mb']:.0f} MB | "
                             f"{r['quebra_mb'] / r['disponivel_mb']:.2f} | {r['razao_salto']:.0f}x |")
            tabela.append({"repeticao": r["repeticao"], "disponivel_mb": r["disponivel_mb"],
                           "ponto_quebra_mb": r["quebra_mb"], "base_ms_por_mb": r["base"],
                           "pos_quebra_ms_por_mb": r["pos_quebra"], "razao_salto": r["razao_salto"]})
        q = res["quebra_est"]
        if q["n"]:
            msg = (f"Ponto de quebra: média {q['media']:.0f} MB, mediana {q['mediana']:.0f} MB, desvio "
                   f"{q['desvio']:.0f} MB, mín {q['minimo']:.0f}, máx {q['maximo']:.0f}, IC 95% "
                   f"[{q['ic95_inf']:.0f}, {q['ic95_sup']:.0f}] MB (n={q['n']}). RAM total: {res['ram_total_mb']:.0f} MB.")
            print("  " + msg)
            linhas_md += ["", msg, ""]
        comum.salvar_csv(saida / f"analise_03_penhasco_{ident}.csv", tabela,
                         ["repeticao", "disponivel_mb", "ponto_quebra_mb", "base_ms_por_mb",
                          "pos_quebra_ms_por_mb", "razao_salto"])
        grafico_penhasco(res, ident, so, saida / f"grafico_03_penhasco_{ident}.png")
        print()

    arq = pasta / f"04_passo_{ident}.csv"
    if arq.exists() and (linhas := comum.ler_csv(arq)):
        achou = True
        so = linhas[0]["so"]
        res = analisar_passo(linhas)
        comum.salvar_csv(saida / f"analise_04_passo_{ident}.csv", res["tabela"],
                         ["passo_bytes", "paginas_distintas", "n", "media", "mediana", "desvio", "minimo",
                          "maximo", "ic95_inf", "ic95_sup"])
        print("Parte 2b: passo e TLB")
        linhas_md += ["## Parte 2b: passo e TLB", "", "| Passo | Páginas distintas | ns/acesso (mediana) | IC 95% |",
                      "|---|---|---|---|"]
        for r in res["tabela"]:
            print(f"  passo {r['passo_bytes']:>6} B: {r['paginas_distintas']:>5} páginas, {r['mediana']:.2f} ns/acesso"
                  f" [{r['ic95_inf']:.2f}, {r['ic95_sup']:.2f}]")
            linhas_md.append(f"| {rotulo_bytes(r['passo_bytes'])} | {r['paginas_distintas']} | {r['mediana']:.2f} | "
                             f"[{r['ic95_inf']:.2f}, {r['ic95_sup']:.2f}] |")
        msg = (f"Pior passo: {rotulo_bytes(res['pior_passo'])}, {res['razao_tlb']:.1f}x o menor passo. "
               f"Página desta máquina: {rotulo_bytes(res['pagina'])}.")
        print("  " + msg)
        linhas_md += ["", msg, ""]
        grafico_passo(res, ident, so, saida / f"grafico_04_passo_{ident}.png")
        print()

    if not achou:
        comum.erro(f"nenhum CSV de medição encontrado para '{ident}' em {pasta}. Rode antes os scripts 02, 03 e 04.")
    destino_md = saida / f"resumo_{ident}.md"
    destino_md.write_text("\n".join(linhas_md) + "\n", encoding="utf-8")
    print(f"Resumo para o relatório: {rel(destino_md)}")
    return 0


# ---------------------------------------------------------------------------
# Modo consolidação (turma)
# ---------------------------------------------------------------------------
def coletar(pastas: list[Path], prefixo: str) -> dict[str, list[dict]]:
    """Agrupa as linhas por id. Se um id aparecer em mais de um arquivo, fica o mais recente."""
    escolhidos: dict[str, tuple[str, list[dict]]] = {}
    for pasta in pastas:
        for arq in sorted(pasta.rglob(f"{prefixo}_*.csv")):
            if "_resumo_" in arq.name:
                continue
            try:
                linhas = comum.ler_csv(arq)
            except (OSError, UnicodeDecodeError) as exc:
                print(f"  AVISO: não consegui ler {arq} ({exc}); ignorado.")
                continue
            if not linhas or "id" not in linhas[0]:
                print(f"  AVISO: {arq} está vazio ou sem a coluna 'id'; ignorado.")
                continue
            ident, quando = linhas[0]["id"], linhas[0].get("data_hora", "")
            if ident not in escolhidos or quando > escolhidos[ident][0]:
                escolhidos[ident] = (quando, linhas)
    return {k: v[1] for k, v in escolhidos.items()}


def modo_turma(pastas: list[Path]) -> int:
    for p in pastas:
        if not p.is_dir():
            comum.erro(f"pasta não encontrada: {p}")
    saida = comum.RESULTADOS / "turma"
    blocos, penhascos, passos = coletar(pastas, "02_blocos"), coletar(pastas, "03_penhasco"), coletar(pastas, "04_passo")
    ids = sorted(set(blocos) | set(penhascos) | set(passos))
    if not ids:
        comum.erro("nenhum CSV de medição (02_blocos_*, 03_penhasco_*, 04_passo_*) encontrado nas pastas indicadas.")
    print(f"Consolidando {len(ids)} máquina(s): {', '.join(ids)}\n")

    tabela, curvas_penhasco, curvas_passo = [], [], []
    for ident in ids:
        qualquer = (blocos.get(ident) or penhascos.get(ident) or passos.get(ident))[0]
        linha = {"id": ident, "so": qualquer["so"], "so_versao": qualquer["so_versao"], "cpu": qualquer["cpu"],
                 "arquitetura": qualquer["arquitetura"], "ram_total_mb": num(qualquer["ram_total_mb"]),
                 "tamanho_pagina_bytes": int(num(qualquer["tamanho_pagina_bytes"]))}
        if ident in blocos:
            rb = analisar_blocos(blocos[ident])
            linha.update({"base_ms_por_mb": rb["base"], "salto_blocos": rb["razao_salto"],
                          "disponivel_mb": rb["disponivel_mb"]})
        if ident in penhascos:
            rp = analisar_penhasco(penhascos[ident])
            q = rp["quebra_est"]
            if q["n"]:
                disp = rp["disponivel_est"]["mediana"]
                linha.update({"quebra_mediana_mb": q["mediana"], "quebra_sobre_disponivel": q["mediana"] / disp,
                              "quebra_sobre_ram_total": q["mediana"] / rp["ram_total_mb"],
                              "salto_penhasco": rp["razao_est"]["mediana"]})
            r0 = rp["reps"][0]
            curvas_penhasco.append((linha["so"], [x / rp["ram_total_mb"] for x in r0["x"]],
                                    [y / r0["base"] for y in r0["y"]]))
        if ident in passos:
            rt = analisar_passo(passos[ident])
            linha["razao_tlb"] = rt["razao_tlb"]
            base = rt["tabela"][0]["mediana"]
            curvas_passo.append((linha["so"], [r["passo_bytes"] for r in rt["tabela"]],
                                 [r["mediana"] / base for r in rt["tabela"]]))
        tabela.append(linha)

    campos = ["id", "so", "so_versao", "cpu", "arquitetura", "ram_total_mb", "tamanho_pagina_bytes",
              "disponivel_mb", "base_ms_por_mb", "salto_blocos", "quebra_mediana_mb", "quebra_sobre_disponivel",
              "quebra_sobre_ram_total", "salto_penhasco", "razao_tlb"]
    comum.salvar_csv(saida / "resumo_turma.csv", tabela, campos)

    # Estatísticas por SO
    metricas = ["base_ms_por_mb", "salto_blocos", "quebra_sobre_disponivel", "quebra_sobre_ram_total",
                "salto_penhasco", "razao_tlb"]
    por_so = []
    print(f"{'SO':>8} | {'máquinas':>8} | {'métrica':>24} | {'mediana':>8} | {'média':>8} | IC 95%")
    print("-" * 86)
    for so in sorted({l["so"] for l in tabela}):
        grupo = [l for l in tabela if l["so"] == so]
        for m in metricas:
            est = comum.estatisticas([l[m] for l in grupo if m in l])
            if not est["n"]:
                continue
            por_so.append({"so": so, "metrica": m, **est})
            print(f"{so:>8} | {len(grupo):>8} | {m:>24} | {est['mediana']:8.3f} | {est['media']:8.3f} | "
                  f"[{comum.fmt(est['ic95_inf'])}, {comum.fmt(est['ic95_sup'])}]")
    comum.salvar_csv(saida / "resumo_por_so.csv", por_so,
                     ["so", "metrica", "n", "media", "mediana", "desvio", "minimo", "maximo", "ic95_inf", "ic95_sup"])
    print(f"\n  tabelas: {rel(saida / 'resumo_turma.csv')}, {rel(saida / 'resumo_por_so.csv')}")

    legenda_so = [Line2D([], [], color=c, lw=2, label=s) for s, c in CORES_SO.items()
                  if any(l["so"] == s for l in tabela)]
    if curvas_penhasco:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for so, x, y in curvas_penhasco:
            ax.plot(x, y, color=CORES_SO.get(so, COR_OUTRA), lw=1.4, alpha=0.85)
        ax.axvline(1.0, color=TEXTO, ls="-.", lw=1)
        ax.annotate("RAM total", (1.0, 1), xycoords=("data", "axes fraction"), xytext=(4, -4),
                    textcoords="offset points", va="top", fontsize=8, color=TEXTO)
        ax.set_yscale("log")
        ax.set_xlabel("Memória tocada / RAM total da máquina")
        ax.set_ylabel("ms/MB dividido pelo início (log)")
        ax.set_title("Turma: o penhasco em cada máquina (1ª repetição)")
        ax.legend(handles=legenda_so, loc="upper left")
        salvar_figura(fig, saida / "grafico_turma_penhasco.png")
    if curvas_passo:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for so, x, y in curvas_passo:
            ax.plot(x, y, color=CORES_SO.get(so, COR_OUTRA), lw=1.4, marker="o", ms=4, alpha=0.85)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("Passo entre leituras (bytes)")
        ax.set_ylabel("ns/acesso dividido pelo menor passo")
        ax.set_title("Turma: efeito da TLB por máquina")
        ax.legend(handles=legenda_so, loc="upper left")
        salvar_figura(fig, saida / "grafico_turma_passo.png")
    com_quebra = [l for l in tabela if "quebra_sobre_disponivel" in l]
    if com_quebra:
        fig, ax = plt.subplots(figsize=(8, 4.0))
        sos = sorted({l["so"] for l in com_quebra})
        for i, so in enumerate(sos):
            vals = [l["quebra_sobre_disponivel"] for l in com_quebra if l["so"] == so]
            ax.scatter(vals, [i] * len(vals), s=60, color=CORES_SO.get(so, COR_OUTRA), edgecolor=FUNDO, lw=2, zorder=3)
            ax.scatter([statistics.median(vals)], [i], marker="|", s=400, color=TEXTO, zorder=4)
        ax.axvline(1.0, color=TEXTO_2, ls="--", lw=1.2)
        ax.set_yticks(range(len(sos)), sos)
        ax.set_ylim(-0.6, len(sos) - 0.4)
        ax.set_xlabel("Ponto de quebra / RAM disponível no início (1.0 = 'bateu')")
        ax.set_title("Turma: o penhasco aparece onde a 'available' prevê? (traço = mediana)")
        ax.grid(axis="y", visible=False)
        salvar_figura(fig, saida / "grafico_turma_quebra.png")
    return 0


def main() -> int:
    comum.preparar_console()
    p = argparse.ArgumentParser(description="Gera estatísticas e gráficos dos experimentos.")
    p.add_argument("--id", help="identificador da dupla (padrão: o salvo pelo 00_check_env.py)")
    p.add_argument("--pasta", default=str(comum.RESULTADOS), help="pasta de onde ler os CSVs (padrão: resultados); a saída vai sempre para resultados/")
    p.add_argument("--consolidar", nargs="+", metavar="PASTA",
                   help="junta CSVs de várias máquinas (pastas) e compara os SOs; saída em resultados/turma/")
    args = p.parse_args()
    if args.consolidar:
        return modo_turma([Path(x).expanduser().resolve() for x in args.consolidar])
    return modo_individual(Path(args.pasta).expanduser().resolve(), comum.obter_id(args.id))


if __name__ == "__main__":
    sys.exit(main())
