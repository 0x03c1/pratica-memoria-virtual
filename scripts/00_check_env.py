"""Etapa 0: verifica se a máquina está pronta para a prática.

Uso:
    python scripts/00_check_env.py --id dupla07

Imprime OK / AVISO / FALHA por item. AVISO não impede a prática; FALHA impede.
O --id é salvo em resultados/identificacao.txt e reaproveitado pelos outros scripts.
"""

from __future__ import annotations

import argparse
import importlib
import platform
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum  # noqa: E402

DEPENDENCIAS = ["psutil", "numpy", "matplotlib"]
resultados_itens: list[tuple[str, str, str]] = []


def registrar(item: str, estado: str, detalhe: str = "") -> None:
    resultados_itens.append((item, estado, detalhe))
    print(f"[{estado:5}] {item}" + (f": {detalhe}" if detalhe else ""))


def versoes_requeridas() -> dict[str, str]:
    """Lê requirements.txt e devolve {pacote: versão} válidos para este Python."""
    req = comum.RAIZ / "requirements.txt"
    versoes: dict[str, str] = {}
    if not req.exists():
        return versoes
    menor_312 = sys.version_info < (3, 12)
    for linha in req.read_text(encoding="utf-8").splitlines():
        linha = linha.split("#", 1)[0].strip()
        if "==" not in linha:
            continue
        espec, _, marcador = linha.partition(";")
        nome, versao = (p.strip() for p in espec.split("=="))
        if marcador:
            if '< "3.12"' in marcador and not menor_312:
                continue
            if '>= "3.12"' in marcador and menor_312:
                continue
        versoes[nome.lower()] = versao
    return versoes


def main() -> int:
    comum.preparar_console()
    parser = argparse.ArgumentParser(description="Verifica o ambiente da prática de memória virtual.")
    parser.add_argument("--id", help="identificador da dupla, ex.: dupla07 (vira parte do nome dos CSVs)")
    args = parser.parse_args()

    print("Verificação do ambiente: prática de Memória Virtual\n")

    # 1. Python
    v = sys.version_info
    if v >= (3, 10):
        registrar("Python", "OK", f"{platform.python_version()} ({sys.executable})")
    else:
        registrar("Python", "FALHA", f"{platform.python_version()}; é preciso 3.10 ou mais novo")

    # 2. Ambiente virtual
    em_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    registrar("Ambiente virtual", "OK" if em_venv else "AVISO",
              "ativo" if em_venv else "não ativado; veja o README (passo 'Criar o ambiente')")

    # 3. Dependências
    requeridas = versoes_requeridas()
    for nome in DEPENDENCIAS:
        try:
            modulo = importlib.import_module(nome)
            instalada = getattr(modulo, "__version__", "?")
            esperada = requeridas.get(nome)
            if esperada and instalada != esperada:
                registrar(f"Pacote {nome}", "AVISO", f"{instalada} instalada; requirements.txt pede {esperada}")
            else:
                registrar(f"Pacote {nome}", "OK", instalada)
        except ImportError:
            registrar(f"Pacote {nome}", "FALHA",
                      "não instalado; rode: python -m pip install -r requirements.txt")

    if any(estado == "FALHA" for _, estado, _ in resultados_itens):
        return resumo()

    # 4. Sistema operacional, CPU e página
    registrar("Sistema operacional", "OK", f"{comum.nome_so()}: {comum.versao_so()} [{platform.machine()}]")
    registrar("CPU", "OK", f"{comum.nome_cpu()} ({comum.os.cpu_count()} núcleos lógicos)")
    registrar("Tamanho da página", "OK", f"{comum.TAMANHO_PAGINA} bytes ({comum.TAMANHO_PAGINA // 1024} KB)")

    # 5. Memória e swap
    mem = comum.ler_memoria()
    psutil = comum.exigir_psutil()
    total_mb = psutil.virtual_memory().total / comum.MB
    disp = mem["disponivel_mb"]
    estado = "OK" if disp >= 1024 else "AVISO"
    registrar("RAM", estado, f"total {total_mb / 1024:.1f} GB, disponível agora {disp / 1024:.1f} GB"
              + ("" if estado == "OK" else "; feche programas antes de medir"))
    if mem["swap_total_mb"] < 256 and platform.system() == "Linux":
        registrar("Swap", "AVISO", "sem swap: o kernel encerra o processo ao passar da RAM (veja o ROTEIRO)")
    else:
        detalhe = f"total {mem['swap_total_mb'] / 1024:.1f} GB, em uso {mem['swap_usado_mb'] / 1024:.1f} GB"
        if platform.system() in ("Darwin", "Windows"):
            detalhe += " (cresce sob demanda neste SO)"
        elif platform.system() == "Linux":
            em_disco, tem_zram = comum.swap_linux_em_disco_mb()
            if tem_zram:
                detalhe += f"; inclui zram (comprimido na RAM). Em disco, livre: {(em_disco or 0) / 1024:.1f} GB"
        registrar("Swap", "OK", detalhe)

    # 6. Disco livre (o swap usa o disco)
    livre_gb = shutil.disk_usage(comum.RAIZ).free / comum.GB
    registrar("Disco livre", "OK" if livre_gb >= 10 else "AVISO",
              f"{livre_gb:.1f} GB" + ("" if livre_gb >= 10 else "; menos de 10 GB pode limitar o swap"))

    # 7. Permissão de escrita em resultados/
    try:
        comum.RESULTADOS.mkdir(exist_ok=True)
        teste = comum.RESULTADOS / ".teste_escrita"
        teste.write_text("ok", encoding="utf-8")
        teste.unlink()
        registrar("Escrita em resultados/", "OK", str(comum.RESULTADOS))
    except OSError as exc:
        registrar("Escrita em resultados/", "FALHA", f"{exc}")

    # 8. Teste rápido: alocar e tocar 64 MB
    try:
        t0 = time.perf_counter_ns()
        bloco = comum.alocar(64 * comum.MB)
        mv = memoryview(bloco)
        comum.Tocador("cheio").tocar(mv, 0, 64 * comum.MB)
        ms = (time.perf_counter_ns() - t0) / 1e6
        mv.release()
        bloco.close()
        registrar("Alocar e tocar 64 MB", "OK", f"{ms:.0f} ms")
    except comum.ErroAlocacao as exc:
        registrar("Alocar e tocar 64 MB", "FALHA", str(exc))

    # 9. Identificador
    if args.id:
        ident = comum.limpar_id(args.id)
        comum.ARQUIVO_ID.write_text(ident + "\n", encoding="utf-8")
        registrar("Identificador", "OK", f"'{ident}' salvo em resultados/identificacao.txt")
    elif comum.ARQUIVO_ID.exists():
        registrar("Identificador", "OK", f"'{comum.ARQUIVO_ID.read_text(encoding='utf-8').strip()}' (já salvo)")
    else:
        registrar("Identificador", "FALHA", "rode de novo com --id, ex.: --id dupla07")

    return resumo()


def resumo() -> int:
    falhas = [r for r in resultados_itens if r[1] == "FALHA"]
    avisos = [r for r in resultados_itens if r[1] == "AVISO"]
    print("\n" + "-" * 60)
    if falhas:
        print(f"FALHA em {len(falhas)} item(ns). Corrija antes de seguir:")
        for item, _, detalhe in falhas:
            print(f"  - {item}: {detalhe}")
        return 1
    print("Ambiente OK" + (f" (com {len(avisos)} aviso(s))." if avisos else ".")
          + " Próximo passo: python scripts/01_inspecionar_memoria.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
