"""Etapa 4 (Parte 2): "Mate a TLB" variando o passo entre acessos.

Lemos sempre a MESMA quantidade de bytes (--acessos, padrão 8192 leituras de 1 byte),
mudando só a distância (passo) entre eles:
    passo 64     -> várias leituras caem na mesma página  (poucas páginas, TLB acerta)
    passo 4096   -> 1 leitura por página de 4 KB           (milhares de páginas)
    passo 65536  -> 1 leitura a cada 16 páginas de 4 KB
Como são poucas linhas de cache no total (8192 x 64 B = 512 KB), os dados cabem
no cache em todos os casos; o que muda é quantas TRADUÇÕES de página a CPU precisa.
Quando as páginas visitadas passam do que a TLB guarda, cada leitura vira um TLB
miss + page walk, e o tempo por acesso sobe.

Detalhe técnico: somamos um deslocamento de 64 bytes que gira a cada acesso para que
os endereços não caiam todos no mesmo conjunto do cache (isso mediria outro efeito).

Uso:
    python scripts/04_passo_tlb.py
    python scripts/04_passo_tlb.py --rapido
    python scripts/04_passo_tlb.py --passos 64,4096,65536 --repeticoes 20
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

try:
    import numpy as np
except ImportError:
    comum.erro("numpy não encontrado. Ative o ambiente virtual e rode: python -m pip install -r requirements.txt")

LINHA = 64  # bytes por linha de cache (valor típico)

CAMPOS = ["id", "so", "so_versao", "arquitetura", "cpu", "nucleos_logicos", "ram_total_mb",
          "tamanho_pagina_bytes", "python", "data_hora", "script", "parametros",
          "passo_bytes", "acessos", "paginas_distintas", "extensao_mb", "repeticao", "voltas",
          "tempo_s", "ns_por_acesso"]
CAMPOS_RESUMO = ["id", "so", "tamanho_pagina_bytes", "passo_bytes", "paginas_distintas", "extensao_mb",
                 "n", "media", "mediana", "desvio", "minimo", "maximo", "ic95_inf", "ic95_sup"]


def indices(passo: int, acessos: int) -> "np.ndarray":
    """Endereço do k-ésimo acesso: k*passo + deslocamento girando de 64 em 64 dentro do passo."""
    k = np.arange(acessos, dtype=np.int64)
    if passo <= LINHA:
        return k * passo
    return k * passo + (k * LINHA) % passo


def main() -> int:
    comum.preparar_console()
    p = argparse.ArgumentParser(description="Mede o custo de acesso conforme o passo cruza páginas (TLB).")
    p.add_argument("--id", help="identificador da dupla (padrão: o salvo pelo 00_check_env.py)")
    p.add_argument("--passos", default="64,256,1024,4096,16384,65536",
                   help="passos em bytes, separados por vírgula (padrão 64,256,1024,4096,16384,65536)")
    p.add_argument("--acessos", type=int, default=8192, help="leituras por volta (padrão 8192)")
    p.add_argument("--repeticoes", type=int, help="medições por passo (padrão 20; --rapido: 10)")
    p.add_argument("--aquecimento", type=int, default=3, help="medições descartadas por passo (padrão 3)")
    p.add_argument("--voltas", type=int, help="voltas por medição (padrão 500; --rapido: 200)")
    p.add_argument("--rapido", action="store_true", help="menos repetições e voltas")
    args = p.parse_args()

    try:
        passos = sorted({int(x) for x in args.passos.split(",") if x.strip()})
    except ValueError:
        comum.erro("--passos deve ser uma lista de inteiros, ex.: 64,4096,65536")
    if not passos or min(passos) < 1 or args.acessos < 64:
        comum.erro("use passos >= 1 e --acessos >= 64.")
    repeticoes = args.repeticoes or (10 if args.rapido else 20)
    voltas = args.voltas or (200 if args.rapido else 500)

    ident = comum.obter_id(args.id)
    pagina = comum.TAMANHO_PAGINA
    extensao = args.acessos * max(passos) + pagina
    try:
        regiao = comum.alocar(extensao)
    except comum.ErroAlocacao as exc:
        comum.erro(f"{exc} Reduza --acessos ou o maior passo.")
    dados = np.frombuffer(regiao, dtype=np.uint8)

    # Prepara os índices de cada passo e toca as páginas usadas (tira page faults da medição).
    conjuntos = {}
    for passo in passos:
        idx = indices(passo, args.acessos)
        dados[idx] = 1
        conjuntos[passo] = idx

    parametros = (f"passos={','.join(map(str, passos))} acessos={args.acessos} repeticoes={repeticoes} "
                  f"aquecimento={args.aquecimento} voltas={voltas} rapido={args.rapido}")
    meta = comum.metadados(ident, "04_passo_tlb", parametros)
    print("Experimento: custo por acesso conforme o passo")
    print(f"  página = {pagina} bytes | {args.acessos} leituras por volta | {voltas} voltas por medição"
          f" | {repeticoes} repetições\n")

    def medir(passo: int) -> float:
        idx = conjuntos[passo]
        t0 = time.perf_counter_ns()
        for _ in range(voltas):
            dados[idx].sum()  # leitura dos bytes nos endereços escolhidos
        return (time.perf_counter_ns() - t0) / 1e9

    destino = comum.RESULTADOS / f"04_passo_{ident}.csv"
    escritor = comum.EscritorCSV(destino, CAMPOS)
    valores: dict[int, list[float]] = {s: [] for s in passos}
    try:
        for passo in passos:  # aquecimento
            for _ in range(args.aquecimento):
                medir(passo)
        for rep in range(1, repeticoes + 1):
            ordem = passos[:]
            random.shuffle(ordem)  # ordem aleatória evita que um passo seja sempre medido "depois" de outro
            for passo in ordem:
                tempo = medir(passo)
                ns = tempo * 1e9 / (voltas * args.acessos)
                valores[passo].append(ns)
                paginas = len(np.unique(conjuntos[passo] // pagina))
                escritor.escrever({**meta, "passo_bytes": passo, "acessos": args.acessos,
                                   "paginas_distintas": paginas,
                                   "extensao_mb": args.acessos * passo / comum.MB, "repeticao": rep,
                                   "voltas": voltas, "tempo_s": tempo, "ns_por_acesso": ns})
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário (Ctrl+C). As medições feitas foram salvas.")
    finally:
        escritor.fechar()
        del dados
        regiao.close()

    resumos = []
    print(f"{'passo':>8} | {'páginas':>8} | {'extensão':>10} | {'ns/acesso (mediana)':>19} | IC 95% da média")
    print("-" * 78)
    for passo in passos:
        if not valores[passo]:
            continue
        est = comum.estatisticas(valores[passo])
        paginas = len(np.unique(conjuntos[passo] // pagina))
        ext_mb = args.acessos * passo / comum.MB
        resumos.append({"id": ident, "so": meta["so"], "tamanho_pagina_bytes": pagina, "passo_bytes": passo,
                        "paginas_distintas": paginas, "extensao_mb": ext_mb, **est})
        print(f"{passo:>8} | {paginas:>8} | {ext_mb:>7.1f} MB | {est['mediana']:>19.2f} | "
              f"[{comum.fmt(est['ic95_inf'], 2)}, {comum.fmt(est['ic95_sup'], 2)}]")
    resumo_csv = comum.RESULTADOS / f"04_passo_resumo_{ident}.csv"
    comum.salvar_csv(resumo_csv, resumos, CAMPOS_RESUMO)
    print(f"\nMedições: {destino.relative_to(comum.RAIZ)}")
    print(f"Resumo:   {resumo_csv.relative_to(comum.RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
