"""Etapa 1: quanta RAM livre você tem de verdade? (equivale ao 'free -h' do slide)

Uso:
    python scripts/01_inspecionar_memoria.py
    python scripts/01_inspecionar_memoria.py --mts 3200 --cl 16     # calculadora DDR do slide

Mostra RAM total, disponível, swap e tamanho da página; tenta ler a especificação
dos pentes (sem privilégio de administrador) e salva tudo em
resultados/01_memoria_<id>.csv.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402


def especificacao_ram() -> str:
    """Tenta descobrir tipo/velocidade da RAM. Melhor esforço, nunca exige admin."""
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            saida = subprocess.run(["system_profiler", "SPMemoryDataType", "-json"],
                                   capture_output=True, text=True, timeout=20)
            dados = json.loads(saida.stdout or "{}").get("SPMemoryDataType", [])
            partes = []
            for item in dados:
                tipo = item.get("dimm_type", "")
                vel = item.get("dimm_speed", "")
                tam = item.get("SPMemoryDataType", "")
                partes.append(" ".join(x for x in (tam, tipo, vel) if x))
                for sub in item.get("_items", []):
                    partes.append(" ".join(x for x in (sub.get("dimm_size", ""), sub.get("dimm_type", ""),
                                                       sub.get("dimm_speed", "")) if x))
            return "; ".join(p for p in partes if p) or "não informado pelo sistema"
        if sistema == "Windows":
            comando = ("Get-CimInstance Win32_PhysicalMemory | "
                       "ForEach-Object { \"$([math]::Round($_.Capacity/1GB))GB $($_.Speed)MT/s "
                       "(configurada $($_.ConfiguredClockSpeed))\" }")
            saida = subprocess.run(["powershell", "-NoProfile", "-Command", comando],
                                   capture_output=True, text=True, timeout=30)
            linhas = [x.strip() for x in saida.stdout.splitlines() if x.strip()]
            return "; ".join(linhas) or "não informado pelo sistema"
        if sistema == "Linux":
            return ("no Linux a velocidade dos pentes só aparece com 'sudo dmidecode -t memory' "
                    "(não é necessário para a prática)")
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return "não foi possível ler sem privilégios"


def calculadora_ddr(mts: float, cl: float) -> dict:
    """Fórmulas do slide 'Lendo a etiqueta'."""
    return {
        "clock_real_mhz": mts / 2,                 # DDR: 2 transferências por ciclo
        "latencia_ns": 2 * cl / mts * 1e3,          # T = 2 x CL / (MT/s) x 10^3
        "vazao_gb_s_por_canal": mts * 8 / 1000,     # MT/s x 8 bytes (barramento de 64 bits)
    }


def main() -> int:
    comum.preparar_console()
    parser = argparse.ArgumentParser(description="Mostra a memória da máquina e calcula latência DDR.")
    parser.add_argument("--id", help="identificador da dupla (padrão: o salvo pelo 00_check_env.py)")
    parser.add_argument("--mts", type=float, help="taxa da memória em MT/s (ex.: 3200)")
    parser.add_argument("--cl", type=float, help="CAS latency em ciclos (ex.: 16)")
    args = parser.parse_args()

    ident = comum.obter_id(args.id)
    psutil = comum.exigir_psutil()
    vm = psutil.virtual_memory()
    mem = comum.ler_memoria()

    print(f"Máquina: {comum.nome_so()} | {comum.nome_cpu()}\n")
    print(f"RAM total ............ {vm.total / comum.GB:6.2f} GB")
    print(f"RAM disponível ....... {vm.available / comum.GB:6.2f} GB   <- anote no relatório (é a 'available')")
    print(f"RAM 'free' ........... {getattr(vm, 'free', 0) / comum.GB:6.2f} GB   (não use esta: ignora o cache)")
    print(f"Swap total / em uso .. {mem['swap_total_mb'] / 1024:6.2f} GB / {mem['swap_usado_mb'] / 1024:.2f} GB")
    print(f"Tamanho da página .... {comum.TAMANHO_PAGINA} bytes")
    espec = especificacao_ram()
    print(f"Especificação da RAM . {espec}")

    linha = comum.metadados(ident, "01_inspecionar_memoria", f"mts={args.mts} cl={args.cl}")
    linha.update({
        "ram_disponivel_mb": round(vm.available / comum.MB),
        "ram_livre_mb": round(getattr(vm, "free", 0) / comum.MB),
        "swap_total_mb": round(mem["swap_total_mb"]),
        "swap_usado_mb": round(mem["swap_usado_mb"]),
        "especificacao_ram": espec,
    })

    if args.mts and args.cl:
        calc = calculadora_ddr(args.mts, args.cl)
        print(f"\nCalculadora DDR para {args.mts:.0f} MT/s CL{args.cl:.0f}:")
        print(f"  clock real ......... {calc['clock_real_mhz']:.0f} MHz")
        print(f"  latência (CAS) ..... {calc['latencia_ns']:.2f} ns")
        print(f"  vazão por canal .... {calc['vazao_gb_s_por_canal']:.1f} GB/s")
        linha.update(calc)
    elif args.mts or args.cl:
        comum.erro("informe --mts e --cl juntos (ex.: --mts 3200 --cl 16).")

    campos = list(linha.keys())
    destino = comum.RESULTADOS / f"01_memoria_{ident}.csv"
    comum.salvar_csv(destino, [linha], campos)
    print(f"\nSalvo em {destino.relative_to(comum.RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
