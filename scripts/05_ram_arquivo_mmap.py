"""Etapa 5 (DESAFIO, opcional): escrever 100 MB em RAM, em arquivo e via mmap.

Item 3 do "Mão na massa" do slide. Mede o tempo para escrever o mesmo volume:
    ram      copiar para um buffer na memória
    arquivo  write() em um arquivo + fsync (garante que chegou ao disco)
    mmap     mapear um arquivo na memória, escrever nele + flush (msync)
Os arquivos temporários ficam em resultados/ e são apagados ao final.

Uso:
    python scripts/05_ram_arquivo_mmap.py
    python scripts/05_ram_arquivo_mmap.py --tamanho-mb 100 --repeticoes 5
"""

from __future__ import annotations

import argparse
import mmap
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

CAMPOS = ["id", "so", "so_versao", "arquitetura", "cpu", "nucleos_logicos", "ram_total_mb",
          "tamanho_pagina_bytes", "python", "data_hora", "script", "parametros",
          "destino", "tamanho_mb", "repeticao", "tempo_s", "mb_por_s"]
CAMPOS_RESUMO = ["id", "so", "destino", "tamanho_mb", "n", "media", "mediana", "desvio", "minimo", "maximo",
                 "ic95_inf", "ic95_sup", "mb_por_s_mediana"]


def escrever_ram(dados: bytes, _caminho: Path) -> None:
    destino = bytearray(len(dados))
    destino[:] = dados


def escrever_arquivo(dados: bytes, caminho: Path) -> None:
    with caminho.open("wb") as arq:
        arq.write(dados)
        arq.flush()
        os.fsync(arq.fileno())  # sem isto, mediríamos só a cópia para o cache do SO


def escrever_mmap(dados: bytes, caminho: Path) -> None:
    with caminho.open("w+b") as arq:
        arq.truncate(len(dados))
        with mmap.mmap(arq.fileno(), len(dados)) as mapa:
            mapa[:] = dados
            mapa.flush()  # msync: força a ida ao disco


METODOS = {"ram": escrever_ram, "arquivo": escrever_arquivo, "mmap": escrever_mmap}


def main() -> int:
    comum.preparar_console()
    p = argparse.ArgumentParser(description="Compara escrever em RAM, em arquivo e via mmap.")
    p.add_argument("--id", help="identificador da dupla (padrão: o salvo pelo 00_check_env.py)")
    p.add_argument("--tamanho-mb", type=int, default=100, help="volume escrito por medição (padrão 100)")
    p.add_argument("--repeticoes", type=int, help="medições por destino (padrão 5; --rapido: 3)")
    p.add_argument("--aquecimento", type=int, default=1, help="execuções descartadas por destino (padrão 1)")
    p.add_argument("--rapido", action="store_true", help="menos repetições")
    args = p.parse_args()
    repeticoes = args.repeticoes or (3 if args.rapido else 5)
    if args.tamanho_mb < 1 or repeticoes < 1:
        comum.erro("--tamanho-mb e --repeticoes devem ser >= 1.")

    ident = comum.obter_id(args.id)
    meta = comum.metadados(ident, "05_ram_arquivo_mmap",
                           f"tamanho_mb={args.tamanho_mb} repeticoes={repeticoes} aquecimento={args.aquecimento}")
    dados = os.urandom(args.tamanho_mb * comum.MB)
    temporario = comum.RESULTADOS / f"_temp_05_{ident}.bin"
    escritor = comum.EscritorCSV(comum.RESULTADOS / f"05_ram_arquivo_mmap_{ident}.csv", CAMPOS)
    valores: dict[str, list[float]] = {m: [] for m in METODOS}
    try:
        for nome, funcao in METODOS.items():
            for _ in range(args.aquecimento):
                funcao(dados, temporario)
            for rep in range(1, repeticoes + 1):
                t0 = time.perf_counter_ns()
                funcao(dados, temporario)
                tempo = (time.perf_counter_ns() - t0) / 1e9
                valores[nome].append(tempo)
                escritor.escrever({**meta, "destino": nome, "tamanho_mb": args.tamanho_mb, "repeticao": rep,
                                   "tempo_s": tempo, "mb_por_s": args.tamanho_mb / tempo})
    except OSError as exc:
        comum.erro(f"falha ao escrever no disco: {exc}")
    finally:
        escritor.fechar()
        temporario.unlink(missing_ok=True)

    resumos = []
    print(f"{'destino':>8} | {'tempo mediano':>13} | {'MB/s':>8}")
    for nome, v in valores.items():
        est = comum.estatisticas(v)
        mbps = args.tamanho_mb / est["mediana"]
        resumos.append({"id": ident, "so": meta["so"], "destino": nome, "tamanho_mb": args.tamanho_mb, **est,
                        "mb_por_s_mediana": mbps})
        print(f"{nome:>8} | {est['mediana'] * 1000:10.1f} ms | {mbps:8.0f}")
    comum.salvar_csv(comum.RESULTADOS / f"05_ram_arquivo_mmap_resumo_{ident}.csv", resumos, CAMPOS_RESUMO)
    print("\nOrdene os três e relacione com a tabela de latências do slide 'Page fault e swap'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
