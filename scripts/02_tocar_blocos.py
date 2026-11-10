"""Etapa 2 (Parte 1): o experimento do slide, bloco a bloco.

Aloca um bloco de memória virtual, toca todas as páginas e mede o tempo por MB.
Repete aumentando o bloco (256 MB, 512 MB, 1 GB, 2 GB, ...) até ultrapassar a RAM.
É a versão em Python do programa vm.c do slide, com as mesmas grandezas da
tabela "Registre a medição": ms/MB, major faults e swap ativo.

Uso:
    python scripts/02_tocar_blocos.py                 # padrão
    python scripts/02_tocar_blocos.py --rapido        # máquinas lentas
    python scripts/02_tocar_blocos.py --modo pagina   # 1 byte por página, igual ao C do slide

Segurança: blocos acima de 80% da RAM disponível rodam uma única vez; o script
para no primeiro bloco em que o tempo por MB "explode" e também se um bloco
passar de --tempo-max segundos. Ctrl+C interrompe e mantém o que já foi salvo.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

PEDACO = 64 * comum.MB  # o bloco é tocado em pedaços para checar o tempo e permitir Ctrl+C

CAMPOS = ["id", "so", "so_versao", "arquitetura", "cpu", "nucleos_logicos", "ram_total_mb",
          "tamanho_pagina_bytes", "python", "data_hora", "script", "parametros",
          "modo", "tamanho_mb", "repeticao", "disponivel_inicial_mb", "acima_da_disponivel",
          "tocado_mb", "tempo_s", "ms_por_mb", "faltas_menores", "faltas_maiores", "faltas_total",
          "swap_in_delta_mb", "swap_out_delta_mb", "swap_usado_delta_mb", "disponivel_depois_mb",
          "interrompido"]

CAMPOS_RESUMO = ["id", "so", "modo", "tamanho_mb", "n", "media", "mediana", "desvio", "minimo",
                 "maximo", "ic95_inf", "ic95_sup", "faltas_maiores_media", "swap_ativo"]


def lista_tamanhos(inicio_mb: int, limite_mb: int) -> list[int]:
    """256, 512, 1024, ... dobrando até o limite; o próprio limite entra como último bloco."""
    tamanhos = []
    t = inicio_mb
    while t < limite_mb * 0.9:
        tamanhos.append(t)
        t *= 2
    tamanhos.append(limite_mb)
    return tamanhos


def medir_bloco(tamanho_mb: int, tocador: comum.Tocador, tempo_max: float) -> dict:
    """Aloca, toca e libera um bloco. Retorna tempos e contadores."""
    n_bytes = tamanho_mb * comum.MB
    bloco = comum.alocar(n_bytes)  # pode lançar ErroAlocacao
    mv = memoryview(bloco)
    mem_antes = comum.ler_memoria()
    faltas_antes = comum.ler_faltas()
    interrompido = 0
    pos = 0
    ultimo_aviso = time.perf_counter()

    t0 = time.perf_counter_ns()
    while pos < n_bytes:
        fim = min(pos + PEDACO, n_bytes)
        tocador.tocar(mv, pos, fim)
        pos = fim
        decorrido = (time.perf_counter_ns() - t0) / 1e9
        if decorrido > tempo_max:
            interrompido = 1
            break
        if time.perf_counter() - ultimo_aviso > 5:  # progresso para blocos demorados
            print(f"      ... {pos // comum.MB} de {tamanho_mb} MB ({decorrido:.0f} s)", flush=True)
            ultimo_aviso = time.perf_counter()
    t1 = time.perf_counter_ns()

    faltas = comum.diferenca_faltas(faltas_antes, comum.ler_faltas())
    swap = comum.diferenca_swap(mem_antes, comum.ler_memoria())
    mv.release()
    bloco.close()  # devolve a memória ao SO
    tocado_mb = pos / comum.MB
    tempo_s = (t1 - t0) / 1e9
    return {
        "tocado_mb": tocado_mb,
        "tempo_s": tempo_s,
        "ms_por_mb": tempo_s * 1000 / tocado_mb,
        "faltas_menores": faltas["menores"],
        "faltas_maiores": faltas["maiores"],
        "faltas_total": faltas["total"],
        **swap,
        "disponivel_depois_mb": comum.ler_memoria()["disponivel_mb"],
        "interrompido": interrompido,
    }


def main() -> int:
    comum.preparar_console()
    p = argparse.ArgumentParser(description="Mede o tempo por MB ao tocar blocos cada vez maiores.")
    p.add_argument("--id", help="identificador da dupla (padrão: o salvo pelo 00_check_env.py)")
    p.add_argument("--repeticoes", type=int, help="repetições por bloco que cabe na RAM (padrão 5; --rapido: 3)")
    p.add_argument("--aquecimento", type=int, default=1, help="execuções descartadas antes de medir (padrão 1)")
    p.add_argument("--modo", choices=["cheio", "pagina"], default="cheio",
                   help="cheio: página inteira com dados aleatórios (padrão); pagina: 1 byte por página")
    p.add_argument("--limite", type=float, default=1.25,
                   help="maior bloco = LIMITE x RAM total (padrão 1.25)")
    p.add_argument("--tamanhos", help="lista de tamanhos em MB separados por vírgula (substitui a lista automática)")
    p.add_argument("--fator-lento", type=float, default=10.0,
                   help="para quando ms/MB >= FATOR x o valor dos blocos pequenos (padrão 10)")
    p.add_argument("--tempo-max", type=float, help="segundos máximos por bloco (padrão 90; --rapido: 60)")
    p.add_argument("--rapido", action="store_true", help="menos repetições e blocos iniciais maiores")
    p.add_argument("--forcar", action="store_true", help="ignora o teto de segurança do swap no Linux")
    args = p.parse_args()

    repeticoes = args.repeticoes or (3 if args.rapido else 5)
    tempo_max = args.tempo_max or (60.0 if args.rapido else 90.0)
    if repeticoes < 1 or args.aquecimento < 0:
        comum.erro("--repeticoes deve ser >= 1 e --aquecimento >= 0.")

    ident = comum.obter_id(args.id)
    limite_mb, avisos = comum.limite_seguro_mb(args.limite, args.forcar)
    if args.tamanhos:
        try:
            tamanhos = [int(x) for x in args.tamanhos.split(",") if x.strip()]
        except ValueError:
            comum.erro("--tamanhos deve ser uma lista de inteiros em MB, ex.: 256,512,1024")
    else:
        tamanhos = lista_tamanhos(512 if args.rapido else 256, limite_mb)

    disp_inicial = comum.ler_memoria()["disponivel_mb"]
    zona_segura = 0.8 * disp_inicial
    parametros = (f"modo={args.modo} repeticoes={repeticoes} aquecimento={args.aquecimento} "
                  f"limite={args.limite} fator_lento={args.fator_lento} tempo_max={tempo_max} "
                  f"rapido={args.rapido}")
    meta = comum.metadados(ident, "02_tocar_blocos", parametros)

    print("Experimento: tocar blocos de memória cada vez maiores")
    print(f"  RAM total {meta['ram_total_mb'] / 1024:.1f} GB | disponível agora {disp_inicial / 1024:.1f} GB"
          f" | página {comum.TAMANHO_PAGINA} bytes | modo '{args.modo}'")
    print(f"  Blocos (MB): {', '.join(str(t) for t in tamanhos)}")
    print(f"  Blocos até {zona_segura:.0f} MB: aquecimento + {repeticoes} repetições. Acima disso: 1 execução.")
    for aviso in avisos:
        print(f"  AVISO: {aviso}")
    print("  Deixe o monitor rodando em outro terminal (python scripts/monitor_memoria.py).\n")

    tocador = comum.Tocador(args.modo)
    destino = comum.RESULTADOS / f"02_blocos_{ident}.csv"
    escritor = comum.EscritorCSV(destino, CAMPOS)
    resumos = []
    medianas_base = []

    try:
        # Aquecimento global: carrega o código e "acorda" o alocador do SO.
        medir_bloco(64, tocador, tempo_max)
        print(f"{'Bloco':>9} | {'ms/MB (mediana)':>15} | {'IC 95% da média':>19} | {'major faults':>12} | swap ativo?")
        print("-" * 80)
        for tamanho in tamanhos:
            cabe = tamanho <= zona_segura
            n_rep = repeticoes if cabe else 1
            if cabe:
                for _ in range(args.aquecimento):
                    medir_bloco(tamanho, tocador, tempo_max)
            else:
                print(f"  {tamanho} MB passa de 80% da RAM disponível: a máquina pode ficar lenta...", flush=True)
            valores, maiores, swap_ativo, interrompido = [], [], False, False
            for rep in range(1, n_rep + 1):
                try:
                    r = medir_bloco(tamanho, tocador, tempo_max)
                except comum.ErroAlocacao as exc:
                    print(f"  {tamanho} MB: {exc}")
                    interrompido = True
                    break
                linha = {**meta, "modo": args.modo, "tamanho_mb": tamanho, "repeticao": rep,
                         "disponivel_inicial_mb": round(disp_inicial),
                         "acima_da_disponivel": int(tamanho > disp_inicial), **r}
                escritor.escrever(linha)
                valores.append(r["ms_por_mb"])
                if r["faltas_maiores"] != "":
                    maiores.append(r["faltas_maiores"])
                saida_swap = r["swap_out_delta_mb"] if r["swap_out_delta_mb"] != "" else r["swap_usado_delta_mb"]
                swap_ativo = swap_ativo or (saida_swap != "" and saida_swap > 1)
                interrompido = interrompido or bool(r["interrompido"])
            if not valores:
                break
            est = comum.estatisticas(valores)
            media_maiores = statistics.fmean(maiores) if maiores else ""
            resumos.append({"id": ident, "so": meta["so"], "modo": args.modo, "tamanho_mb": tamanho, **est,
                            "faltas_maiores_media": media_maiores, "swap_ativo": "sim" if swap_ativo else "não"})
            ic = f"[{comum.fmt(est['ic95_inf'])}, {comum.fmt(est['ic95_sup'])}]" if est["n"] > 1 else "(1 execução)"
            maj = f"{media_maiores:.0f}" if media_maiores != "" else "n/d"
            marca = "  <- interrompido (tempo máximo)" if interrompido else ""
            print(f"{tamanho:>6} MB | {est['mediana']:>15.3f} | {ic:>19} | {maj:>12} | "
                  f"{'sim' if swap_ativo else 'não'}{marca}", flush=True)

            if cabe:
                medianas_base.append(est["mediana"])
            base = statistics.median(medianas_base) if medianas_base else None
            if interrompido:
                print("\nParando: o bloco passou do tempo máximo. Isso já é o penhasco.")
                break
            if base and est["mediana"] >= args.fator_lento * base and not cabe:
                print(f"\nParando: {est['mediana']:.2f} ms/MB é {est['mediana'] / base:.0f}x o valor dos blocos"
                      f" que cabem na RAM ({base:.3f} ms/MB). Penhasco encontrado.")
                break
            if not cabe:
                time.sleep(3)  # dá um respiro ao sistema antes do próximo bloco grande
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário (Ctrl+C). As medições feitas até aqui foram salvas.")
    finally:
        escritor.fechar()

    if resumos:
        resumo_csv = comum.RESULTADOS / f"02_blocos_resumo_{ident}.csv"
        comum.salvar_csv(resumo_csv, resumos, CAMPOS_RESUMO)
        print(f"\nMedições: {destino.relative_to(comum.RAIZ)}")
        print(f"Resumo:   {resumo_csv.relative_to(comum.RAIZ)}")
        print(f"RAM disponível no início: {disp_inicial:.0f} MB. Em qual linha o ms/MB explodiu?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
