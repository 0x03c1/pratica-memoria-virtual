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
import platform
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
    windows = platform.system() == "Windows"
    print("Monitor de memória (Ctrl+C para sair)")
    print(f"{'hora':>8} | {'disponível':>10} | {'uso RAM':>7} | {'swap usado':>10} | {'si MB/s':>8} | {'so MB/s':>8}")
    anterior = psutil.swap_memory()
    try:
        while True:
            time.sleep(args.intervalo)
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            if windows:
                si = so = "n/d"
            else:
                si = f"{(sw.sin - anterior.sin) / comum.MB / args.intervalo:8.1f}"
                so = f"{(sw.sout - anterior.sout) / comum.MB / args.intervalo:8.1f}"
            anterior = sw
            alerta = "  <- swap ativo" if (not windows and (float(si) > 1 or float(so) > 1)) else ""
            print(f"{dt.datetime.now():%H:%M:%S} | {vm.available / comum.MB:7.0f} MB | {vm.percent:6.1f}% | "
                  f"{sw.used / comum.MB:7.0f} MB | {si:>8} | {so:>8}{alerta}", flush=True)
    except KeyboardInterrupt:
        print("\nMonitor encerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
