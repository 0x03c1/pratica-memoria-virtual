"""Monitor de memória e swap, a cada segundo (equivale ao 'vmstat 1' do slide).

Deixe rodando em um SEGUNDO terminal enquanto o 02 ou o 03 executam:
    python scripts/monitor_memoria.py
    python scripts/monitor_memoria.py --intervalo 0.5

Colunas:
    disponível   RAM disponível (MB)
    swap usado   quanto do swap/arquivo de paginação está ocupado (MB)
    si / so      MB/s trazidos do swap (swap in) e enviados ao swap (swap out),
                 como as colunas si/so do vmstat. No Windows esses contadores não
                 existem; acompanhe a variação do 'swap usado'.
Encerre com Ctrl+C.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402


def main() -> int:
    comum.preparar_console()
    p = argparse.ArgumentParser(description="Mostra RAM disponível e atividade de swap periodicamente.")
    p.add_argument("--intervalo", type=float, default=1.0, help="segundos entre leituras (padrão 1)")
    args = p.parse_args()
    if args.intervalo <= 0:
        comum.erro("--intervalo deve ser maior que zero.")

    psutil = comum.exigir_psutil()
    print("Monitor de memória (Ctrl+C para sair)")
    print(f"{'hora':>8} | {'disponível':>10} | {'uso RAM':>7} | {'swap usado':>10} | {'si MB/s':>8} | {'so MB/s':>8}")
    # comum.ler_memoria() traz os contadores certos de cada SO (no macOS, Swapins/Swapouts do vm_stat).
    anterior, t_anterior = comum.ler_memoria(), time.monotonic()
    try:
        while True:
            time.sleep(args.intervalo)
            vm = psutil.virtual_memory()
            mem, agora = comum.ler_memoria(), time.monotonic()
            intervalo = agora - t_anterior
            if mem["swap_in_mb"] is None or anterior["swap_in_mb"] is None:
                si = so = "n/d"
                alerta = ""
            else:
                taxa_in = (mem["swap_in_mb"] - anterior["swap_in_mb"]) / intervalo
                taxa_out = (mem["swap_out_mb"] - anterior["swap_out_mb"]) / intervalo
                si, so = f"{taxa_in:8.1f}", f"{taxa_out:8.1f}"
                alerta = "  <- swap ativo" if (taxa_in > 1 or taxa_out > 1) else ""
            anterior, t_anterior = mem, agora
            print(f"{dt.datetime.now():%H:%M:%S} | {vm.available / comum.MB:7.0f} MB | {vm.percent:6.1f}% | "
                  f"{mem['swap_usado_mb']:7.0f} MB | {si:>8} | {so:>8}{alerta}", flush=True)
    except KeyboardInterrupt:
        print("\nMonitor encerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
