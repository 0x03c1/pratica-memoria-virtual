"""Etapa 3 (Parte 2): encontre o penhasco com precisão de 256 MB.

Em vez de vários blocos separados, aloca UMA região grande e a toca em fatias
de --passo-mb, medindo o tempo de cada fatia. Enquanto a memória já tocada cabe
na RAM, cada fatia custa o mesmo; quando deixa de caber, cada página nova exige
expulsar outra para o disco e o tempo por MB salta. A posição desse salto é o
"ponto de quebra", que você vai comparar com a RAM disponível do 01.

Uso:
    python scripts/03_penhasco_fino.py               # padrão: fatias de 256 MB, 3 repetições
    python scripts/03_penhasco_fino.py --rapido      # fatias de 512 MB, 2 repetições

Segurança: depois de detectar o penhasco, o script avança só mais --alem-mb e para.
Também para se uma repetição passar de --tempo-max segundos. Ctrl+C mantém o que foi salvo.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

CAMPOS = ["id", "so", "so_versao", "arquitetura", "cpu", "nucleos_logicos", "ram_total_mb",
          "tamanho_pagina_bytes", "python", "data_hora", "script", "parametros",
          "modo", "repeticao", "fatia", "inicio_mb", "fim_mb", "ms_por_mb", "disponivel_inicial_mb",
          "disponivel_mb", "faltas_menores", "faltas_maiores", "faltas_total",
          "swap_in_delta_mb", "swap_out_delta_mb", "swap_usado_delta_mb", "lenta"]

CAMPOS_RESUMO = ["id", "so", "modo", "repeticao", "disponivel_inicial_mb", "ram_total_mb",
                 "base_ms_por_mb", "ponto_quebra_mb", "quebra_sobre_disponivel", "quebra_sobre_ram_total",
                 "pos_quebra_ms_por_mb", "razao_salto", "parou_por"]


def base_da_varredura(medidas: list[dict], disp_inicial: float) -> float | None:
    """Tempo típico (mediana) das fatias que certamente cabem na RAM."""
    seguras = [m["ms_por_mb"] for m in medidas[1:5] if m["fim_mb"] <= 0.6 * disp_inicial]
    if len(seguras) < 2:
        seguras = [m["ms_por_mb"] for m in medidas[:2]]
    return statistics.median(seguras) if len(seguras) >= 2 else None


def varrer(rep: int, args, tocador, limite_mb: int, meta: dict, escritor) -> dict:
    # Reserva a região inteira (só memória virtual; nada vai para a RAM ainda).
    tamanho_mb = limite_mb
    while True:
        try:
            regiao = comum.alocar(tamanho_mb * comum.MB)
            break
        except comum.ErroAlocacao as exc:
            tamanho_mb = comum.arredondar_mb(tamanho_mb * 0.85, args.passo_mb)
            if tamanho_mb < 4 * args.passo_mb:
                comum.erro(str(exc))
            print(f"  Não coube reservar a região; tentando {tamanho_mb} MB.")
    mv = memoryview(regiao)
    disp_inicial = comum.ler_memoria()["disponivel_mb"]
    passo = args.passo_mb * comum.MB
    medidas: list[dict] = []
    base = None
    seguidas = 0
    quebra_mb = None
    parou_por = "limite"
    t_inicio = time.perf_counter()
    print(f"\nRepetição {rep}: disponível {disp_inicial:.0f} MB, região reservada {tamanho_mb} MB")

    for fatia, inicio in enumerate(range(0, tamanho_mb * comum.MB, passo)):
        fim = min(inicio + passo, tamanho_mb * comum.MB)
        mem_antes = comum.ler_memoria()
        faltas_antes = comum.ler_faltas()
        t0 = time.perf_counter_ns()
        tocador.tocar(mv, inicio, fim)
        t1 = time.perf_counter_ns()
        faltas = comum.diferenca_faltas(faltas_antes, comum.ler_faltas())
        mem_depois = comum.ler_memoria()
        swap = comum.diferenca_swap(mem_antes, mem_depois)
        ms_mb = (t1 - t0) / 1e6 / ((fim - inicio) / comum.MB)
        m = {"inicio_mb": inicio // comum.MB, "fim_mb": fim // comum.MB, "ms_por_mb": ms_mb}
        medidas.append(m)

        if base is None and len(medidas) >= 3:
            base = base_da_varredura(medidas, disp_inicial)
        lenta = int(base is not None and ms_mb >= args.fator_lento * base)
        seguidas = seguidas + 1 if lenta else 0
        if quebra_mb is None and seguidas >= args.consecutivas:
            quebra_mb = medidas[-args.consecutivas]["inicio_mb"]
            print(f"  >>> penhasco detectado em {quebra_mb} MB; avançando mais {args.alem_mb} MB e parando.")

        escritor.escrever({**meta, "modo": args.modo, "repeticao": rep, "fatia": fatia, **m,
                           "disponivel_inicial_mb": round(disp_inicial),
                           "disponivel_mb": round(mem_depois["disponivel_mb"]),
                           "faltas_menores": faltas["menores"], "faltas_maiores": faltas["maiores"],
                           "faltas_total": faltas["total"], **swap, "lenta": lenta})
        marca = " *" if lenta else ""
        print(f"  {m['fim_mb']:>7} MB  {ms_mb:9.3f} ms/MB  disponível {mem_depois['disponivel_mb']:>7.0f} MB{marca}",
              flush=True)

        if quebra_mb is not None and m["fim_mb"] >= quebra_mb + args.alem_mb:
            parou_por = "penhasco"
            break
        if time.perf_counter() - t_inicio > args.tempo_max:
            parou_por = "tempo"
            print(f"  Tempo máximo ({args.tempo_max:.0f} s) atingido nesta repetição.")
            break

    mv.release()
    regiao.close()

    # Swap pequeno: a varredura pode bater no limite logo depois de atravessar a RAM, sem
    # completar --consecutivas fatias lentas. Se as últimas fatias estão todas lentas, o
    # penhasco começou no início dessa sequência final.
    if quebra_mb is None and seguidas >= 1 and base:
        quebra_mb = medidas[-seguidas]["inicio_mb"]
        parou_por += " (penhasco nas últimas fatias)"
        print(f"  >>> penhasco nas últimas {seguidas} fatia(s), a partir de {quebra_mb} MB.")

    ram_total = meta["ram_total_mb"]
    resumo = {"id": meta["id"], "so": meta["so"], "modo": args.modo, "repeticao": rep,
              "disponivel_inicial_mb": round(disp_inicial), "ram_total_mb": ram_total,
              "base_ms_por_mb": base, "parou_por": parou_por}
    if quebra_mb is not None and base:
        pos = [x["ms_por_mb"] for x in medidas if x["inicio_mb"] >= quebra_mb]
        pos_mediana = statistics.median(pos)
        resumo.update({"ponto_quebra_mb": quebra_mb,
                       "quebra_sobre_disponivel": quebra_mb / disp_inicial,
                       "quebra_sobre_ram_total": quebra_mb / ram_total,
                       "pos_quebra_ms_por_mb": pos_mediana,
                       "razao_salto": pos_mediana / base})
    return resumo


def main() -> int:
    comum.preparar_console()
    p = argparse.ArgumentParser(description="Localiza o ponto em que a memória deixa de caber na RAM.")
    p.add_argument("--id", help="identificador da dupla (padrão: o salvo pelo 00_check_env.py)")
    p.add_argument("--passo-mb", type=int, help="tamanho de cada fatia em MB (padrão 256; --rapido: 512)")
    p.add_argument("--repeticoes", type=int, help="quantas varreduras completas (padrão 3; --rapido: 2)")
    p.add_argument("--modo", choices=["cheio", "pagina"], default="cheio",
                   help="cheio: página inteira com dados aleatórios (padrão); pagina: 1 byte por página")
    p.add_argument("--limite", type=float, default=1.25, help="região máxima = LIMITE x RAM total (padrão 1.25)")
    p.add_argument("--fator-lento", type=float, default=8.0,
                   help="fatia 'lenta' = ms/MB >= FATOR x o valor inicial (padrão 8)")
    p.add_argument("--consecutivas", type=int, default=3,
                   help="fatias lentas seguidas para declarar o penhasco (padrão 3)")
    p.add_argument("--alem-mb", type=int, default=1024, help="quanto avançar depois do penhasco (padrão 1024)")
    p.add_argument("--tempo-max", type=float, default=120.0, help="segundos máximos por repetição (padrão 120)")
    p.add_argument("--rapido", action="store_true", help="fatias maiores e menos repetições")
    p.add_argument("--forcar", action="store_true", help="ignora o teto de segurança do swap no Linux")
    args = p.parse_args()

    args.passo_mb = args.passo_mb or (512 if args.rapido else 256)
    repeticoes = args.repeticoes or (2 if args.rapido else 3)
    if args.passo_mb < 16 or repeticoes < 1 or args.consecutivas < 1:
        comum.erro("valores inválidos: --passo-mb >= 16, --repeticoes >= 1, --consecutivas >= 1.")

    ident = comum.obter_id(args.id)
    limite_mb, avisos = comum.limite_seguro_mb(args.limite, args.forcar)
    limite_mb = comum.arredondar_mb(limite_mb, args.passo_mb)
    parametros = (f"modo={args.modo} passo_mb={args.passo_mb} repeticoes={repeticoes} limite={args.limite} "
                  f"fator_lento={args.fator_lento} consecutivas={args.consecutivas} alem_mb={args.alem_mb} "
                  f"tempo_max={args.tempo_max} rapido={args.rapido}")
    meta = comum.metadados(ident, "03_penhasco_fino", parametros)

    print("Experimento: varredura fina em busca do penhasco")
    print(f"  RAM total {meta['ram_total_mb']} MB | fatias de {args.passo_mb} MB | até {limite_mb} MB"
          f" | modo '{args.modo}' | {repeticoes} repetição(ões)")
    for aviso in avisos:
        print(f"  AVISO: {aviso}")
    print("  Fatias marcadas com * estão lentas (>= "
          f"{args.fator_lento:g}x o início).")

    tocador = comum.Tocador(args.modo)
    destino = comum.RESULTADOS / f"03_penhasco_{ident}.csv"
    escritor = comum.EscritorCSV(destino, CAMPOS)
    resumos = []
    try:
        # Aquecimento: um toque pequeno, descartado.
        aquec = comum.alocar(128 * comum.MB)
        tocador.tocar(memoryview(aquec), 0, 128 * comum.MB)
        aquec.close()
        for rep in range(1, repeticoes + 1):
            resumos.append(varrer(rep, args, tocador, limite_mb, meta, escritor))
            if rep < repeticoes:
                time.sleep(5)  # respiro entre varreduras
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário (Ctrl+C). As fatias medidas foram salvas.")
    finally:
        escritor.fechar()

    if not resumos:
        return 0
    resumo_csv = comum.RESULTADOS / f"03_penhasco_resumo_{ident}.csv"
    comum.salvar_csv(resumo_csv, resumos, CAMPOS_RESUMO)

    print("\nResumo por repetição:")
    for r in resumos:
        if r.get("ponto_quebra_mb"):
            print(f"  rep {r['repeticao']}: quebra em {r['ponto_quebra_mb']} MB "
                  f"({r['quebra_sobre_disponivel']:.2f}x a disponível, {r['quebra_sobre_ram_total']:.2f}x a RAM total);"
                  f" {r['base_ms_por_mb']:.3f} -> {r['pos_quebra_ms_por_mb']:.3f} ms/MB ({r['razao_salto']:.0f}x)")
        else:
            print(f"  rep {r['repeticao']}: penhasco não detectado (parou por {r['parou_por']}). "
                  "Tente --limite maior ou feche menos programas.")
    quebras = [r["ponto_quebra_mb"] for r in resumos if r.get("ponto_quebra_mb")]
    if len(quebras) >= 2:
        est = comum.estatisticas(quebras)
        print(f"  Ponto de quebra: média {est['media']:.0f} MB, mediana {est['mediana']:.0f} MB, "
              f"desvio {est['desvio']:.0f} MB, IC95 [{est['ic95_inf']:.0f}, {est['ic95_sup']:.0f}] MB")
    print(f"\nFatias: {destino.relative_to(comum.RAIZ)}")
    print(f"Resumo: {resumo_csv.relative_to(comum.RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
