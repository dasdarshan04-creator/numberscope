# 🔎 NumberScope — Mobile Number OSINT Lab

> A local-first, **privacy-respecting** tool for inspecting the *public numbering-plan metadata* behind a phone number — with a clean Streamlit UI, a headless CLI, batch analysis, exportable reports, and a synthetic trilateration teaching demo.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white">
  <img alt="Tests" src="https://img.shields.io/badge/tests-13%20passing-brightgreen">
  <img alt="Lint" src="https://img.shields.io/badge/lint-ruff-informational">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
  <img alt="Processing" src="https://img.shields.io/badge/processing-100%25%20local-success">
</p>

<!-- After you push to GitHub, this badge goes live automatically (replace OWNER/REPO):
  [![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
-->

NumberScope answers a focused question — *"What can public, offline metadata tell me about how this number is structured?"* — and is deliberate about what it **refuses** to do. There is **no** subscriber lookup, no live GPS, no carrier/SS7 queries, and no network calls. It is an ethics-forward OSINT learning project.

**One core engine, three interfaces:** a reusable `numberscope` package drives the **Streamlit UI**, a **headless CLI**, and a **FastAPI REST service**.

---

## ✨ Features

| | Feature | What it does |
|---|---|---|
| 🔬 | **Single-number analysis** | Parse to International / National / E.164 / RFC 3966, classify line type, and show possible-vs-valid status with a plain-language reason. |
| 📑 | **Batch analysis + dashboard** | Paste or upload a CSV/TXT of **test** numbers; get summary metrics, charts (by type / region) on a colorblind-safe palette, a results table, and a CSV download. |
| 🌐 | **REST API** | FastAPI service (`/analyse`, `/batch`, `/health`) with auto-generated Swagger docs at `/docs`. |
| 🧾 | **Exportable reports** | Download any result as JSON or CSV, stamped with a UTC timestamp and the libphonenumber metadata version for reproducibility. |
| 🎓 | **"Learn" module** | Explains possible vs. valid, why carrier ≠ current operator (number portability), and **defensive OSINT** tips to reduce your own exposure. |
| 📐 | **Synthetic trilateration demo** | Interactive geometry with range circles, a noise slider, and an RMS-error readout that shows *why* positioning is uncertain — on invented data only. |
| 💻 | **Headless CLI** | Same core engine for scripts/automation: text, `--json`, or `--csv` output. |
| ✅ | **Tested core** | 13 unit tests covering parsing, invalid input, region fallback, and trilateration math. |

---

## 🖥️ Quickstart

```bash
git clone <your-fork-url> numberscope && cd numberscope
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py          # open the UI at http://localhost:8501
```

### Command line

```bash
python cli.py +919876543210                 # pretty text report
python cli.py 9876543210 --region IN         # region used when no leading +
python cli.py +919876543210 +14155552671 --csv > report.csv
python cli.py +14155552671 --json
```

Example output:

```text
International:   +91 98765 43210
Number type:    Mobile
Valid range:    True
Carrier (range):India
Time zones:     Asia/Calcutta
Metadata version: 9.0.43
```

### REST API

```bash
uvicorn api:app --reload        # http://127.0.0.1:8000/docs  (interactive Swagger UI)

curl -X POST http://127.0.0.1:8000/analyse \
  -H 'Content-Type: application/json' \
  -d '{"number": "+919876543210"}'
```

### Tests & lint

```bash
python -m unittest discover -s tests -v
ruff check .
```

### Docker

```bash
docker compose up --build        # UI → :8501  ·  API → :8000
# or just the UI:
docker build -t numberscope . && docker run -p 8501:8501 numberscope
```

---

## 🧱 Architecture

A small, importable core keeps the logic testable and lets every interface share one engine — no duplicated parsing logic, no network anywhere.

```text
mobile-number-osint-lab/
├── numberscope/            # reusable core package (no UI, no network)
│   ├── analysis.py         #   parse → NumberReport dataclass + field caveats
│   └── trilateration.py    #   synthetic geometry + fit-quality (RMS) reporting
├── app.py                  # Streamlit UI (Analyse · Batch · Learn · Demo · Ethics)
├── cli.py                  # headless CLI (text / JSON / CSV)
├── api.py                  # FastAPI REST service (/analyse, /batch, /health, /docs)
├── tests/                  # unit tests for analysis + trilateration
├── Dockerfile · docker-compose.yml
├── .github/workflows/ci.yml  # tests + ruff on Python 3.10–3.12
├── pyproject.toml · requirements.txt · LICENSE · README.md
```

```text
                 ┌───────────────────────┐
  Streamlit UI ──┤                       │
  CLI ───────────┤  numberscope (core)   ├── offline libphonenumber metadata
  FastAPI ───────┤                       │
                 └───────────────────────┘
```

**Data source:** the open-source [`phonenumbers`](https://github.com/daviddrysdale/python-phonenumbers) port of Google's **libphonenumber**. All metadata ships with the package and is read offline.

---

## ⚖️ Ethics & scope — what this lab does *not* do

This project is intentionally bounded. It will **not**:

- ❌ identify a subscriber, or confirm a SIM is active/reachable;
- ❌ reveal a phone's live or GPS location;
- ❌ query cell sites, carriers, SS7/Diameter, or any data broker;
- ❌ send network requests or persist any number you enter.

**Interpretation limits you should always apply:**

- *Carrier* names the operator a number **range** was originally assigned to — **portability** means the current operator can differ.
- A *geographic range* describes the numbering block, **not** where the handset is.
- A *valid range* does **not** prove a number is allocated, active, or owned by anyone.

> Real-time location from a phone number requires privileged carrier signalling or on-device GPS **with consent**, and in most jurisdictions is released only to law enforcement under lawful process. Services claiming to "track any number live" are typically scams or unlawful. Use NumberScope only with numbers you own or are authorised to assess.

---

## 🚀 Deploy

**Streamlit Community Cloud (free, recommended for the UI):**

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → pick your repo.
3. Set **Main file path** to `app.py` and click **Deploy**. Streamlit installs `requirements.txt` automatically — no other config needed.

You'll get a public `https://<your-app>.streamlit.app` URL to drop straight into your LinkedIn post.

**API / full stack:** deploy `Dockerfile` (or `docker-compose.yml`) to any container host — Render, Railway, Fly.io, or a VPS.

---

## 🧪 Tech stack

`Python` · `Streamlit` · `FastAPI` · `phonenumbers (libphonenumber)` · `pandas` · `Vega-Lite` · `Docker` · `GitHub Actions` · `ruff` · `unittest`

## 📄 License

MIT — see [LICENSE](LICENSE).
