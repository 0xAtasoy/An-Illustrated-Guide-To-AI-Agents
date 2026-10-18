# Bölüm 0 — Preface alıştırmaları

Preface'te kitabın kendi alıştırması yok. Bu yüzden buradaki üç alıştırma,
Preface'in verdiği sözleri (TinyAgent, "kod repoda yaşar", "her şey ücretsiz
donanımda çalışır") kendi makinende ve repoda sınamak için.

Hepsi repo kökünden çalışır. Kurallar: stdlib + `illustrated_agents`,
framework yok.

## 0.1 Ortamı ayağa kaldır (hazır script)

```bash
uv sync --extra jupyter
ollama pull gemma3:12b
ollama pull gemma4:e4b
uv run python atasoy/bolum00/ortam_kontrol.py
```

Script Python sürümünü, paketi, GPU'yu, Ollama endpoint'ini, iki modeli,
her modelle tek bir `LLM.generate` çağrısını ve modelin yüzde kaçının GPU'da
durduğunu kontrol eder. Hepsi `OK` olmalı. `Yerleşim` satırında %100 GPU
görmüyorsan model kısmen CPU'da çalışıyor demektir; bunu bildir.

Sonra `uv run jupyter lab` ile `chapter01/chapter01.ipynb`'i baştan sona
çalıştır. LLM gerektirmiyor, sadece paketin notebook'tan import edildiğini
görmek için.

Diğer modeller (`gemma4:e2b`, `embeddinggemma`, `gemma4:e4b-it-qat`)
ilgili bölüm gelince indirilecek.

## 0.2 Repoyu bir agent anatomisi gibi oku

Kod çalıştırmadan, yalnızca `src/illustrated_agents/` ve repo dokümanlarını
okuyarak cevapla. Cevapları thread'e yaz; birlikte üzerinden geçelim.

1. Preface, TinyAgent'ın kitabın sonunda beş şey yapacağını söylüyor:
   reason, remember, use tools, plan, reflect. Her yetenek için hangi dosya
   ve sınıf karşılık geliyor? Bir tablo çıkar. Sonra şunu sor: beşinin de
   `TinyAgent`'ın döngüsüne gerçekten bağlı olduğu bir yer var mı?
   *İpucu: `__init__.py`'den başla; `agent.py` ve `chapters/ch6.py`'deki
   `TinyAgent`'ları karşılaştır.*
2. `llm.py`'deki `LLM.generate` modelle nasıl konuşuyor? Hangi URL'ye,
   hangi kütüphaneyle, body'de hangi alanlarla? `think=False` ne gönderiyor?
3. `LLM.generate`'e bir HFT mühendisi gözüyle code review yap. Production'da
   seni rahatsız edecek en az üç şey bul.
   *İpucu: sunucu hiç cevap vermezse ne olur? Model aynı cevapta iki tool
   çağırırsa? Cevap ne kadar uzun olabilir?*
4. Preface "kitaptaki kod öğretmek, repodaki kod çalıştırmak için" diyor.
   `src/illustrated_agents/README.md`'deki örnek kodu kaynak koduyla
   karşılaştır: olduğu gibi çalışır mı? `.setup/README.md`'deki Python
   sürümü ve kurulum komutları `pyproject.toml` ile tutarlı mı?
5. Preface "her bölüm bağımsız okunabilir" diyor, ama TinyAgent bölüm bölüm
   büyüyor. Kod tarafında bağımsız okumayı mümkün kılan ne?
   *İpucu: `src/illustrated_agents/chapters/`.*

## 0.3 Ekstra (alan): LLM'i bir latency bütçesi gibi ölç

Preface'e göre agent, çok adımda iş yapan bir LLM. Her adım bir
`LLM.generate` çağrısı. Senin dünyanda tick-to-trade mikro saniyelerle
ölçülüyor; bu alıştırma bir agent adımının maliyetini aynı disiplinle ölçüp
agent'ların senin mimarinde nereye oturabileceğini sayıyla görmek için.

`latency_olcum.py` bir iskelet: altyapı (`unload_model`, raporlama, `main`)
hazır, ölçüm mantığı senin.

| TODO | Fonksiyon | Ne yapacak |
|---|---|---|
| 1 | `measure_call` | Tek çağrının süresi, token sayıları, tokens/s |
| 2 | `percentile` | p50/p95, kendi implementasyonun |
| 3 | `cold_vs_warm` | Model boşaltıldıktan sonraki ilk çağrı ve warm çağrılar |
| 4 | `growing_context` | Geçmiş büyüdükçe adım süresi (agent döngüsü taklidi) |
| 5 | `measure_native` | Bonus: prefill ve decode hızını ayrı ölç |

```bash
uv run python atasoy/bolum00/latency_olcum.py
uv run python atasoy/bolum00/latency_olcum.py --native   # TODO 5 bittiyse
```

Çıktıyı thread'e yapıştır ve şu soruları cevapla:

1. Cold start warm çağrıdan kaç kat yavaş? Bir agent sistemi tasarlarken bu
   neyi değiştirir?
2. `gemma3:12b` ile `gemma4:e4b` arasındaki tokens/s farkı ne? Parametre
   sayısıyla orantılı mı?
3. TODO 4'te `prompt_tokens` adım başına nasıl büyüyor ve adım süresini ne
   kadar etkiliyor? 8 adımlık bir döngünün toplam süresi ne?
4. Bu toplam süre senin tick-to-trade bütçenin kabaca kaç katı (10'un
   kuvveti olarak)? Buna göre bir LLM agent'ı senin altyapında nereye
   koyardın, nereye asla koymazdın?
