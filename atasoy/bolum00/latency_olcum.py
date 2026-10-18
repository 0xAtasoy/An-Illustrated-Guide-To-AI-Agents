"""Bölüm 0 (Preface) - Ekstra alıştırma: LLM'i bir latency bütçesi gibi ölç.

Preface agent'ı "hedef + tools + memory verilmiş, çok adımda iş yapan LLM"
olarak tanımlıyor. Her adım bir `LLM.generate` çağrısı demek. Bu script o
çağrının maliyetini senin alışık olduğun şekilde ölçer: cold start, warm
p50/p95, tokens/s ve agent döngüsünde context büyüdükçe adım süresi.

TODO'ları doldurmadan çalıştırırsan NotImplementedError alırsın; bu normal.
Görevler ve sorular: atasoy/bolum00/README.md

Çalıştırma (repo kökünden):
    uv run python atasoy/bolum00/latency_olcum.py
    uv run python atasoy/bolum00/latency_olcum.py --models gemma3:12b --runs 20
"""

import argparse
import json
import urllib.request

from illustrated_agents import LLM

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODELS = ["gemma3:12b", "gemma4:e4b"]

PROMPT = (
    "In exactly three sentences, explain what the funding rate of a "
    "perpetual futures contract is."
)
FOLLOW_UP = "Add one more sentence with a concrete numeric example."


def unload_model(model: str, base_url: str = BASE_URL) -> None:
    """Modeli Ollama'da VRAM'den boşaltır; sonraki çağrı cold start olur.

    Ollama'ya özgü native API: keep_alive=0 olan boş bir generate isteği.
    Ölçüm altyapısı olduğu için hazır veriliyor.
    """
    root = base_url.removesuffix("/").removesuffix("/v1")
    request = urllib.request.Request(
        f"{root}/api/generate",
        data=json.dumps({"model": model, "keep_alive": 0}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        response.read()


def warm_up(model: str, base_url: str = BASE_URL) -> None:
    """Modeli VRAM'e yükler; böylece sonraki ölçüm cold start içermez."""
    LLM(model=model, base_url=base_url).generate(
        [{"role": "user", "content": "Hi"}]
    )


def measure_call(llm: LLM, messages: list[dict]) -> dict:
    """Tek bir `llm.generate` çağrısını ölçer.

    Dönmesi gereken sözlük:
        {
            "wall_s": float,            # çağrının duvar saati süresi
            "prompt_tokens": int,       # response.metadata'dan
            "completion_tokens": int,   # response.metadata'dan
            "tok_per_s": float,         # completion_tokens / wall_s
            "content": str,             # modelin cevabı
        }

    TODO 1: Süreyi ölçmek için hangi saat fonksiyonunu seçtiğine dikkat et
    (C++'taki steady_clock ile system_clock farkını düşün).
    """
    raise NotImplementedError("TODO 1: measure_call")


def percentile(values: list[float], p: float) -> float:
    """`values` listesinin p. yüzdeliğini döner (0 < p <= 100).

    TODO 2: Kendin yaz (nearest-rank ya da lineer interpolasyon, hangisini
    seçtiğini yorumda belirt). Sonra `statistics.quantiles` ile karşılaştır:
    küçük örneklemde (runs=10) p95 neden yanıltıcı olabilir?
    """
    raise NotImplementedError("TODO 2: percentile")


def cold_vs_warm(model: str, runs: int, base_url: str = BASE_URL) -> dict:
    """Bir model için cold start ve warm çağrıları ölçer.

    Dönmesi gereken sözlük:
        {"cold": <measure_call sonucu>, "warm": [<measure_call sonucu>, ...]}

    TODO 3: Önce `unload_model` ile modeli boşalt, ilk çağrıyı "cold" olarak
    ölç, sonra aynı mesajla `runs` kez "warm" ölç. Her çağrıda aynı
    `messages` listesini mi kullanmalısın, yoksa her seferinde yenisini mi?
    """
    raise NotImplementedError("TODO 3: cold_vs_warm")


def growing_context(
    model: str, steps: int, base_url: str = BASE_URL
) -> list[dict]:
    """Bir agent döngüsünü taklit eder: her adımda geçmiş büyür.

    Her adım için bir `measure_call` sonucu döner (adım sırasıyla).

    TODO 4: PROMPT ile başla. Her adımdan sonra modelin cevabını
    {"role": "assistant", ...} olarak, ardından FOLLOW_UP'ı {"role": "user", ...}
    olarak geçmişe ekle ve bir sonraki çağrıyı tüm geçmişle yap. Bu, kitabın
    TinyAgent'ının her adımda `memory.get_messages()` ile yaptığının özü.
    """
    raise NotImplementedError("TODO 4: growing_context")


def measure_native(model: str, base_url: str = BASE_URL) -> dict:
    """BONUS (TODO 5, isteğe bağlı): Ollama'nın native /api/chat endpoint'i.

    {"model": model, "messages": [...], "stream": False} gönderirsen cevapta
    `prompt_eval_count`, `prompt_eval_duration`, `eval_count`, `eval_duration`
    (nanosaniye) gelir. Buradan prefill ve decode hızını ayrı ayrı hesapla ve
    TODO 1'deki tok_per_s ile karşılaştır. Fark nereden geliyor?
    """
    raise NotImplementedError("TODO 5 (bonus): measure_native")


def print_summary(model: str, result: dict) -> None:
    cold = result["cold"]
    walls = [call["wall_s"] for call in result["warm"]]
    speeds = [call["tok_per_s"] for call in result["warm"]]
    print(
        f"{model:<14} cold={cold['wall_s']:6.2f}s  "
        f"warm p50={percentile(walls, 50):5.2f}s p95={percentile(walls, 95):5.2f}s  "
        f"tok/s p50={percentile(speeds, 50):6.1f}"
    )


def print_growth(model: str, calls: list[dict]) -> None:
    print(f"\n{model}: context büyüdükçe adım süresi")
    print(f"{'adım':>4} {'prompt_tok':>10} {'compl_tok':>9} {'wall_s':>7}")
    for step, call in enumerate(calls, start=1):
        print(
            f"{step:>4} {call['prompt_tokens']:>10} "
            f"{call['completion_tokens']:>9} {call['wall_s']:>7.2f}"
        )
    total = sum(call["wall_s"] for call in calls)
    print(f"toplam: {total:.2f}s ({len(calls)} adım)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument(
        "--native", action="store_true", help="TODO 5'i de çalıştır"
    )
    args = parser.parse_args()

    results = {}
    for model in args.models:
        # Diğer modeller VRAM'de kalırsa ölçülen modeli CPU'ya itebilir
        for other in args.models:
            unload_model(other, args.base_url)
        results[model] = cold_vs_warm(model, args.runs, args.base_url)

    print("\n== Cold start ve warm çağrılar ==")
    for model, result in results.items():
        print_summary(model, result)

    print("\n== Agent döngüsü taklidi ==")
    for model in args.models:
        warm_up(model, args.base_url)
        print_growth(model, growing_context(model, args.steps, args.base_url))

    if args.native:
        print("\n== Native Ollama metrikleri ==")
        for model in args.models:
            print(model, measure_native(model, args.base_url))


if __name__ == "__main__":
    main()
