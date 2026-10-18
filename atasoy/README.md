# atasoy/

"An Illustrated Guide to AI Agents" okuma çalışmasında Ozan'ın alıştırma
kodu. Kitabın kendi notebook'larına ve `src/` klasörüne dokunulmaz; her bölüm
kendi klasöründe.

| Klasör | Bölüm | İçerik |
|---|---|---|
| [bolum00/](bolum00/) | Preface | Ortam kontrolü, repoyu okuma, LLM latency ölçümü |

## Çalıştırma

Her şey repo kökünden, kitabın ortamıyla:

```bash
uv sync --extra jupyter
uv run python atasoy/bolum00/ortam_kontrol.py
```

Modeller WSL2 içindeki Ollama'da çalışır (`http://localhost:11434/v1`).

## Kurallar

- Kitabın stili: stdlib + `illustrated_agents` modülleri, framework yok.
- Yalnızca halka açık, read-only piyasa verisi.
- Emir gönderen tool veya trading API anahtarı kullanan kod yok.
