"""Bölüm 0 (Preface) - Ortam kontrolü.

Preface'teki "Hardware and Software Requirements" kısmının yerel karşılığı.
Sırayla şunları kontrol eder: Python sürümü, `illustrated_agents` paketi,
GPU, Ollama'nın OpenAI uyumlu endpoint'i, kitabın modelleri, her modelle tek
bir `LLM.generate` çağrısı ve modelin tamamen GPU'da olup olmadığı.

Çalıştırma (repo kökünden):
    uv run python atasoy/bolum00/ortam_kontrol.py
    uv run python atasoy/bolum00/ortam_kontrol.py --models gemma3:12b gemma4:e4b
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from importlib import metadata

BASE_URL = "http://localhost:11434/v1"

# Şimdilik Part 1'in iki ana modeli. Diğerleri (gemma4:e2b, embeddinggemma,
# gemma4:e4b-it-qat) ilgili bölüm gelince --models ile eklenir.
DEFAULT_MODELS = ["gemma3:12b", "gemma4:e4b"]

GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[0m"


class Report:
    """Kontrol sonuçlarını toplar ve yazdırır."""

    def __init__(self):
        self.failures = 0

    def ok(self, label: str, detail: str = "") -> None:
        print(f"[{GREEN} OK {RESET}] {label}  {detail}")

    def warn(self, label: str, detail: str = "") -> None:
        print(f"[{YELLOW}WARN{RESET}] {label}  {detail}")

    def fail(self, label: str, detail: str = "") -> None:
        self.failures += 1
        print(f"[{RED}FAIL{RESET}] {label}  {detail}")


def get_json(url: str, timeout: float = 5.0) -> dict:
    """Bir URL'ye GET atıp JSON döner (kitaptaki gibi yalnızca urllib)."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())


def check_python(report: Report) -> None:
    # pyproject.toml `requires-python = ">=3.12"` diyor. uv yerine sistemdeki
    # python3 ile çalıştırılırsa bu kontrol anlam kazanır.
    version = ".".join(map(str, sys.version_info[:3]))
    if sys.version_info >= (3, 12):  # noqa: UP036
        report.ok("Python", version)
    else:
        report.fail("Python", f"{version} (paket >= 3.12 istiyor)")


def check_package(report: Report) -> bool:
    try:
        import illustrated_agents
    except ImportError:
        report.fail(
            "illustrated_agents", "import edilemedi; `uv sync --extra jupyter`"
        )
        return False

    version = metadata.version("illustrated-agents")
    # Reponun src/ klasöründen mi, PyPI'dan mı geliyor? Fork'ta çalışırken src/ olmalı
    location = illustrated_agents.__file__.rsplit("/", 2)[0]
    report.ok("illustrated_agents", f"v{version} ({location})")
    return True


def check_gpu(report: Report) -> None:
    # WSL2'de nvidia-smi Windows sürücüsüyle gelir (/usr/lib/wsl/lib)
    nvidia_smi = shutil.which("nvidia-smi") or "/usr/lib/wsl/lib/nvidia-smi"
    try:
        output = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
        report.ok("GPU", output)
    except (OSError, subprocess.SubprocessError):
        report.warn("GPU", "nvidia-smi çalışmadı; Ollama CPU'ya düşebilir")


def check_endpoint(report: Report, base_url: str) -> list[str] | None:
    # OpenAI uyumlu model listesi: GET /v1/models
    try:
        data = get_json(f"{base_url}/models")
    except (urllib.error.URLError, OSError) as error:
        report.fail(
            "Ollama endpoint", f"{base_url} erişilemedi ({error}); `ollama serve`"
        )
        return None

    available = sorted(model["id"] for model in data.get("data", []))
    report.ok("Ollama endpoint", f"{base_url} ({len(available)} model)")
    return available


def check_models(
    report: Report, wanted: list[str], available: list[str]
) -> list[str]:
    present = []
    for model in wanted:
        if model in available:
            report.ok(f"Model {model}", "indirilmiş")
            present.append(model)
        else:
            report.fail(f"Model {model}", f"yok; `ollama pull {model}`")
    return present


def check_generate(report: Report, model: str, base_url: str) -> None:
    from illustrated_agents import LLM

    llm = LLM(model=model, base_url=base_url)
    messages = [{"role": "user", "content": "Reply with exactly one word: ready"}]

    # İlk çağrı modeli VRAM'e yükler, bu yüzden yavaş olabilir (cold start)
    start = time.perf_counter()
    try:
        response = llm.generate(messages)
    except (urllib.error.URLError, OSError, KeyError) as error:
        report.fail(f"generate {model}", str(error))
        return
    elapsed = time.perf_counter() - start

    content = (response.content or "").strip().replace("\n", " ")[:40]
    tokens = response.metadata or {}
    report.ok(
        f"generate {model}",
        f"{elapsed:.2f}s, prompt={tokens.get('prompt_tokens')} "
        f"completion={tokens.get('completion_tokens')} -> {content!r}",
    )


def check_gpu_offload(report: Report, base_url: str) -> None:
    # Ollama'ya özgü native API: GET /api/ps yüklü modelleri ve VRAM payını verir
    root = base_url.removesuffix("/").removesuffix("/v1")
    try:
        data = get_json(f"{root}/api/ps")
    except (urllib.error.URLError, OSError) as error:
        report.warn("GPU yerleşimi", f"/api/ps okunamadı ({error})")
        return

    for model in data.get("models", []):
        size, size_vram = model.get("size", 0), model.get("size_vram", 0)
        share = 100 * size_vram / size if size else 0
        context = model.get("context_length")
        detail = f"{size / 1e9:.1f} GB, %{share:.0f} GPU"
        if context:
            detail += f", context={context}"
        if share >= 99.5:
            report.ok(f"Yerleşim {model.get('name')}", detail)
        else:
            report.warn(
                f"Yerleşim {model.get('name')}",
                detail + " (kısmen CPU'da, yavaş)",
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument(
        "--skip-generate", action="store_true", help="Modelleri çağırma"
    )
    args = parser.parse_args()

    report = Report()
    check_python(report)
    has_package = check_package(report)
    check_gpu(report)

    available = check_endpoint(report, args.base_url)
    if available is not None:
        present = check_models(report, args.models, available)
        if has_package and not args.skip_generate:
            for model in present:
                check_generate(report, model, args.base_url)
        check_gpu_offload(report, args.base_url)

    print()
    if report.failures:
        print(f"{RED}{report.failures} kontrol başarısız.{RESET}")
        return 1
    print(f"{GREEN}Ortam hazır.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
