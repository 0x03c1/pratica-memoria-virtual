"""Funções compartilhadas pelos scripts da prática.

Este módulo não é executado diretamente. Ele reúne:
- caminhos do repositório (sempre com pathlib);
- identificação da dupla e metadados da máquina (SO, CPU, Python, data/hora);
- estatísticas (média, mediana, desvio-padrão, mínimo, máximo, IC 95%);
- leitura de contadores do sistema (page faults, swap, RAM disponível);
- alocação de memória virtual e a rotina que "toca" as páginas.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import mmap
import os
import platform
import statistics
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"
ARQUIVO_ID = RESULTADOS / "identificacao.txt"

MB = 1024 * 1024
GB = 1024 * MB
TAMANHO_PAGINA = mmap.PAGESIZE  # 4096 na maioria dos PCs; 16384 no Apple Silicon


def preparar_console() -> None:
    """Garante saída UTF-8 (acentos) também no console do Windows."""
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def erro(mensagem: str, codigo: int = 1) -> None:
    """Mostra uma mensagem de erro em português e encerra o script."""
    print(f"\nERRO: {mensagem}", file=sys.stderr)
    sys.exit(codigo)


def exigir_psutil():
    """Importa o psutil com uma mensagem amigável se ele não estiver instalado."""
    try:
        import psutil  # noqa: PLC0415
    except ImportError:
        erro(
            "a biblioteca 'psutil' não foi encontrada.\n"
            "  1. Ative o ambiente virtual (veja o README).\n"
            "  2. Rode: python -m pip install -r requirements.txt"
        )
    return psutil


# ---------------------------------------------------------------------------
# Identificação e metadados
# ---------------------------------------------------------------------------
def nome_so() -> str:
    return {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(
        platform.system(), platform.system() or "desconhecido"
    )


def versao_so() -> str:
    sistema = platform.system()
    if sistema == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    if sistema == "Windows":
        rel, ver, _, _ = platform.win32_ver()
        return f"Windows {rel} ({ver})"
    if sistema == "Linux":
        try:
            nome = platform.freedesktop_os_release().get("PRETTY_NAME", "Linux")
        except OSError:
            nome = "Linux"
        return f"{nome} (kernel {platform.release()})"
    return platform.platform()


def nome_cpu() -> str:
    """Nome comercial da CPU, sem exigir privilégios de administrador."""
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            saida = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5,
            )
            if saida.stdout.strip():
                return saida.stdout.strip()
        elif sistema == "Windows":
            import winreg  # noqa: PLC0415

            chave = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            return str(winreg.QueryValueEx(chave, "ProcessorNameString")[0]).strip()
        elif sistema == "Linux":
            texto = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
            for linha in texto.splitlines():
                if linha.lower().startswith(("model name", "hardware", "cpu model")):
                    return linha.split(":", 1)[1].strip()
    except Exception:  # noqa: BLE001 (qualquer falha aqui só reduz a informação)
        pass
    return platform.processor() or platform.machine() or "desconhecida"


def obter_id(id_argumento: str | None) -> str:
    """Retorna o identificador da dupla (argumento --id ou o salvo pelo 00_check_env.py)."""
    if id_argumento:
        return limpar_id(id_argumento)
    if ARQUIVO_ID.exists():
        valor = ARQUIVO_ID.read_text(encoding="utf-8").strip()
        if valor:
            return valor
    erro(
        "identificador da dupla não definido.\n"
        "  Rode primeiro: python scripts/00_check_env.py --id SEU_ID\n"
        "  (ou passe --id SEU_ID para este script)."
    )
    return ""  # nunca chega aqui


def limpar_id(texto: str) -> str:
    """Mantém só letras, números, '-' e '_' para o ID virar nome de arquivo válido em qualquer SO."""
    limpo = "".join(c if (c.isalnum() or c in "-_") else "-" for c in texto.strip())
    limpo = limpo.strip("-_")
    if not limpo:
        erro("o identificador precisa ter ao menos uma letra ou número (ex.: dupla07).")
    return limpo[:40]


def metadados(id_dupla: str, script: str, parametros: str) -> dict:
    """Metadados gravados em todas as linhas de CSV (facilitam a consolidação da turma)."""
    psutil = exigir_psutil()
    vm = psutil.virtual_memory()
    return {
        "id": id_dupla,
        "so": nome_so(),
        "so_versao": versao_so(),
        "arquitetura": platform.machine(),
        "cpu": nome_cpu(),
        "nucleos_logicos": os.cpu_count(),
        "ram_total_mb": round(vm.total / MB),
        "tamanho_pagina_bytes": TAMANHO_PAGINA,
        "python": platform.python_version(),
        "data_hora": dt.datetime.now().isoformat(timespec="seconds"),
        "script": script,
        "parametros": parametros,
    }


# ---------------------------------------------------------------------------
# Estatística
# ---------------------------------------------------------------------------
# Valores críticos t de Student (bicaudal, 95%) para gl = 1..30; acima disso usamos a tabela abaixo.
_T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]
_T95_GRANDE = [(40, 2.021), (60, 2.000), (120, 1.980)]


def t95(gl: int) -> float:
    if gl < 1:
        return float("nan")
    if gl <= 30:
        return _T95[gl - 1]
    for limite, valor in _T95_GRANDE:
        if gl <= limite:
            return valor
    return 1.960


def estatisticas(valores: list[float]) -> dict:
    """Média, mediana, desvio-padrão amostral, mín., máx. e IC 95% da média (t de Student)."""
    v = [float(x) for x in valores if x is not None and not math.isnan(float(x))]
    n = len(v)
    if n == 0:
        return {"n": 0, "media": "", "mediana": "", "desvio": "", "minimo": "",
                "maximo": "", "ic95_inf": "", "ic95_sup": ""}
    media = statistics.fmean(v)
    desvio = statistics.stdev(v) if n >= 2 else 0.0
    margem = t95(n - 1) * desvio / math.sqrt(n) if n >= 2 else 0.0
    return {
        "n": n,
        "media": media,
        "mediana": statistics.median(v),
        "desvio": desvio,
        "minimo": min(v),
        "maximo": max(v),
        "ic95_inf": media - margem,
        "ic95_sup": media + margem,
    }


def fmt(valor, casas: int = 3) -> str:
    if valor == "" or valor is None:
        return "-"
    return f"{valor:.{casas}f}"


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
class EscritorCSV:
    """Escreve linha a linha e faz flush a cada linha.

    Assim, se o script for interrompido (Ctrl+C) ou encerrado pelo SO por falta de
    memória, o que já foi medido continua salvo no arquivo.
    """

    def __init__(self, caminho: Path, campos: list[str]):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho = caminho
        self._arquivo = caminho.open("w", encoding="utf-8", newline="")
        self._escritor = csv.DictWriter(self._arquivo, fieldnames=campos, extrasaction="ignore")
        self._escritor.writeheader()
        self._arquivo.flush()

    def escrever(self, linha: dict) -> None:
        self._escritor.writerow({k: _arredondar(v) for k, v in linha.items()})
        self._arquivo.flush()

    def fechar(self) -> None:
        self._arquivo.close()


def _arredondar(valor):
    if isinstance(valor, float):
        return round(valor, 6)
    return valor


def salvar_csv(caminho: Path, linhas: list[dict], campos: list[str]) -> None:
    escritor = EscritorCSV(caminho, campos)
    for linha in linhas:
        escritor.escrever(linha)
    escritor.fechar()


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open("r", encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


# ---------------------------------------------------------------------------
# Contadores do sistema
# ---------------------------------------------------------------------------
try:
    import resource  # disponível em Linux e macOS; não existe no Windows
except ImportError:
    resource = None


def ler_faltas() -> dict:
    """Page faults acumulados por ESTE processo.

    Linux/macOS: getrusage separa faltas menores (leves) e maiores (pesadas, com E/S).
    Windows: só há o total (leves + pesadas) via psutil; as colunas separadas ficam vazias.
    """
    if resource is not None:
        uso = resource.getrusage(resource.RUSAGE_SELF)
        return {"menores": uso.ru_minflt, "maiores": uso.ru_majflt,
                "total": uso.ru_minflt + uso.ru_majflt}
    psutil = exigir_psutil()
    total = getattr(psutil.Process().memory_info(), "num_page_faults", None)
    return {"menores": None, "maiores": None, "total": total}


def diferenca_faltas(antes: dict, depois: dict) -> dict:
    return {k: (depois[k] - antes[k]) if (antes[k] is not None and depois[k] is not None) else ""
            for k in antes}


def ler_memoria() -> dict:
    """RAM disponível e swap, em MB. swap_in/out acumulados (vazios no Windows)."""
    psutil = exigir_psutil()
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    tem_contadores = platform.system() != "Windows"
    return {
        "disponivel_mb": vm.available / MB,
        "swap_total_mb": sw.total / MB,
        "swap_usado_mb": sw.used / MB,
        "swap_in_mb": sw.sin / MB if tem_contadores else None,
        "swap_out_mb": sw.sout / MB if tem_contadores else None,
    }


def diferenca_swap(antes: dict, depois: dict) -> dict:
    def delta(chave):
        if antes[chave] is None or depois[chave] is None:
            return ""
        return depois[chave] - antes[chave]

    return {"swap_in_delta_mb": delta("swap_in_mb"),
            "swap_out_delta_mb": delta("swap_out_mb"),
            "swap_usado_delta_mb": delta("swap_usado_mb")}


# ---------------------------------------------------------------------------
# Alocação e toque de páginas
# ---------------------------------------------------------------------------
class ErroAlocacao(Exception):
    pass


def alocar(n_bytes: int) -> mmap.mmap:
    """Reserva n_bytes de memória VIRTUAL anônima (equivalente ao malloc grande do slide).

    Nada é colocado na RAM física aqui: as páginas só ganham um frame quando
    forem tocadas pela primeira vez (cada primeiro toque = um page fault).
    """
    opcoes = {}
    if platform.system() != "Windows":
        anonimo = getattr(mmap, "MAP_ANONYMOUS", getattr(mmap, "MAP_ANON", 0))
        opcoes["flags"] = mmap.MAP_PRIVATE | anonimo
    try:
        return mmap.mmap(-1, n_bytes, **opcoes)
    except (OSError, ValueError, OverflowError, MemoryError) as exc:
        dica = ("No Windows isso costuma significar que RAM + arquivo de paginação não comportam o bloco."
                if platform.system() == "Windows"
                else "O sistema recusou reservar esse espaço de endereçamento.")
        raise ErroAlocacao(
            f"não foi possível alocar {n_bytes / MB:.0f} MB ({exc}). {dica} "
            "Use um --limite menor."
        ) from exc


class Tocador:
    """Escreve na memória de duas formas.

    modo 'pagina': 1 byte por página, exatamente como o laço em C do slide
                   (for i += 4096: p[i] = 1), mas usando o tamanho real da página.
    modo 'cheio':  preenche a página inteira com bytes aleatórios. Páginas assim não
                   podem ser comprimidas pelo SO, então o único lugar para elas é a RAM
                   ou o swap. É o modo padrão porque funciona igual nos três SOs.
    """

    BLOCO_FONTE = 16 * MB

    def __init__(self, modo: str, pagina: int = TAMANHO_PAGINA):
        if modo not in ("cheio", "pagina"):
            erro(f"modo desconhecido: {modo!r}. Use 'cheio' ou 'pagina'.")
        self.modo = modo
        self.pagina = pagina
        self._vez = 0
        if modo == "cheio":
            # Fonte de dados aleatórios gerada uma única vez (custo fora da medição).
            self._fonte = memoryview(os.urandom(self.BLOCO_FONTE + pagina))

    def tocar(self, mv: memoryview, inicio: int, fim: int) -> None:
        if self.modo == "pagina":
            quantidade = len(range(inicio, fim, self.pagina))
            mv[inicio:fim:self.pagina] = b"\x01" * quantidade
            return
        pos = inicio
        while pos < fim:
            tamanho = min(self.BLOCO_FONTE, fim - pos)
            # Deslocamento variável: páginas diferentes recebem conteúdos diferentes.
            desloc = (self._vez * 97) % self.pagina
            self._vez += 1
            mv[pos:pos + tamanho] = self._fonte[desloc:desloc + tamanho]
            pos += tamanho


def arredondar_mb(valor_mb: float, multiplo: int = 256) -> int:
    """Arredonda para baixo em múltiplos de 'multiplo' MB (mínimo = multiplo)."""
    return max(multiplo, int(valor_mb // multiplo) * multiplo)


def swap_linux_em_disco_mb() -> tuple[float | None, bool]:
    """Swap livre (MB) em disco no Linux, sem contar zram, e se há zram.

    Lê /proc/swaps (legível sem privilégios). Colunas: nome, tipo, tamanho, usado, prioridade (KB).
    """
    try:
        linhas = Path("/proc/swaps").read_text(encoding="utf-8").splitlines()[1:]
    except OSError:
        return None, False
    livre_kb, tem_zram = 0, False
    for linha in linhas:
        partes = linha.split()
        if len(partes) < 4:
            continue
        if Path(partes[0]).name.startswith("zram"):
            tem_zram = True
            continue
        livre_kb += int(partes[2]) - int(partes[3])
    return livre_kb / 1024, tem_zram


def ram_total_mb() -> float:
    return exigir_psutil().virtual_memory().total / MB


def limite_seguro_mb(fator: float, forcar: bool = False) -> tuple[int, list[str]]:
    """Calcula o maior bloco (MB) a usar e devolve avisos de segurança.

    Regra geral: fator x RAM TOTAL. Usamos a total, e não a disponível, porque no
    macOS e no Windows o SO comprime e despeja outros programas para abrir espaço,
    e o penhasco costuma aparecer bem depois da 'disponível'. Os scripts param
    sozinhos logo depois de detectar o penhasco, então o limite raramente é atingido.

    Linux: o swap tem tamanho fixo; se o bloco passar de RAM + swap livre, o kernel
    mata o processo (OOM killer). Por isso limitamos a RAM disponível + 50% do swap livre.
    Todos: o swap mora no disco, então exigimos folga de disco para o excedente.
    """
    import shutil  # noqa: PLC0415

    mem = ler_memoria()
    disp = mem["disponivel_mb"]
    alvo = ram_total_mb() * fator
    avisos = []
    disco_livre = shutil.disk_usage(RAIZ).free / MB
    teto_disco = disp + 0.5 * disco_livre
    if alvo > teto_disco:
        avisos.append(f"Limite reduzido de {alvo:.0f} MB para {teto_disco:.0f} MB por falta de espaço em disco.")
        alvo = teto_disco
    if platform.system() == "Linux" and not forcar:
        swap_livre, tem_zram = swap_linux_em_disco_mb()
        if swap_livre is None:  # /proc/swaps ilegível: usa o total informado pelo psutil
            swap_livre = mem["swap_total_mb"] - mem["swap_usado_mb"]
        if tem_zram:
            avisos.append(
                "Swap em zram detectado. O zram guarda as páginas comprimidas na própria RAM e, com "
                "os dados aleatórios deste teste, não libera espaço; por isso ele não conta para o limite."
            )
        teto = disp + 0.5 * swap_livre
        if swap_livre < 256:
            avisos.append(
                "Este Linux está sem swap (ou com menos de 256 MB livres). Sem swap não há "
                "penhasco para medir: ao passar da RAM o kernel encerra o processo. "
                "O teste vai parar em 90% da RAM disponível. Use --forcar só se aceitar o risco."
            )
            teto = disp * 0.9
        if alvo > teto:
            avisos.append(f"Limite reduzido de {alvo:.0f} MB para {teto:.0f} MB por causa do tamanho do swap.")
            alvo = teto
    return arredondar_mb(alvo), avisos
