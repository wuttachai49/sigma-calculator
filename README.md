# Sigma Metric Calculator — Clinical Laboratory Quality Management

A full-stack web application for calculating and reporting **Six Sigma metrics** in clinical laboratories across **Hematology**, **Clinical Chemistry**, and **Clinical Immunology** departments.

---

## Features

| Feature | Description |
|---|---|
| **Sigma Calculator** | Compute σ = (TEa − \|Bias%\|) / CV% per analyte with grade classification |
| **QGI Analysis** | Quality Goal Index = \|Bias%\| / (1.5 × CV%) — identifies whether to fix bias or imprecision |
| **QC Rule Recommender** | Westgard multirule suggestions based on Sigma band (1:3s, 2:2s, R:4s, 4:1s, etc.) |
| **OPSpecs Chart** | Interactive normalized Operating Specifications chart (Plotly) |
| **Batch Import** | Upload CSV or Excel (including native IQC format with `IQC_data` sheet) |
| **PDF Report** | 2-page report: results table + embedded Normalized OPSpecs chart |
| **Excel Report** | 4-sheet workbook: Results, QGI Guide, Summary, OPSpecs Chart |
| **TEa Reference Index** | 8 source references (CLIA, BV, NCEP, NGSP, RCPA, ESFEQA, KDIGO, Westgard) with links |
| **Built-in TEa Database** | 75+ analytes pre-loaded with TEa values from CLIA, Biological Variation, and other standards |

---

## Formula

```
Sigma (σ) = (TEa% − |Bias%|) / CV%

QGI = |Bias%| / (1.5 × CV%)
```

### Sigma Performance Bands

| Sigma | Grade | QC Strategy |
|---|---|---|
| ≥ 6 | World Class | 1:3s, N=2 |
| 5 – 6 | Excellent | 1:3s / 2:2s / R:4s, N=2 |
| 4 – 5 | Good | 1:2.5s / 2:2s / R:4s / 4:1s / 10x, N=4 |
| 3 – 4 | Marginal | 1:2s / 2:2s / R:4s / 4:1s / 8x / 10x, N=6 |
| < 3 | Unacceptable | Method improvement required |

### QGI Interpretation

| QGI | Label | Action |
|---|---|---|
| < 0.8 | Precision-limited | Reduce CV — check reagent lots, instrument precision |
| 0.8 – 1.2 | Mixed | Review both calibration and precision |
| > 1.2 | Accuracy-limited | Reduce Bias — check calibration, matrix effects |

---

## Project Structure

```
sigma/
├── backend/
│   ├── main.py           # FastAPI application & API routes
│   ├── calculator.py     # Sigma & QGI calculation engine
│   ├── chart.py          # Matplotlib OPSpecs chart generator
│   ├── report.py         # PDF (fpdf2) and Excel (openpyxl) report generator
│   ├── tea_database.py   # Built-in TEa database (75+ analytes)
│   ├── references.py     # TEa source reference index
│   └── requirements.txt
├── frontend/
│   ├── index.html        # Single-page application
│   ├── style.css
│   └── app.js
└── README.md
```

---

## Getting Started

### Requirements

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/sigma-calculator.git
cd sigma-calculator

# Install dependencies
pip install -r backend/requirements.txt
```

### Run

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8500 --reload
```

Open **http://localhost:8500** in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytes` | List TEa database (filter by `?department=`) |
| `POST` | `/api/calculate` | Calculate Sigma + QGI for one analyte |
| `POST` | `/api/batch` | Batch calculate from CSV/Excel upload |
| `POST` | `/api/opspecs` | Generate OPSpecs chart data |
| `POST` | `/api/report` | Generate PDF or Excel report |
| `GET` | `/api/references` | TEa source reference index |
| `GET` | `/api/health` | Health check |

### Calculate Request Body

```json
{
  "analyte": "Glucose",
  "department": "Clinical Chemistry",
  "tea": 10.0,
  "bias_pct": 1.5,
  "cv_pct": 2.0,
  "tea_source": "CLIA"
}
```

### Batch CSV Format

```csv
analyte,department,tea,bias_pct,cv_pct,tea_source
Glucose,Clinical Chemistry,10,1.5,2.0,CLIA
Hemoglobin,Hematology,7,0.8,1.5,CLIA
TSH,Clinical Immunology,20,3.0,5.0,BV
```

The batch endpoint also auto-detects the **native IQC Excel format** (files containing an `IQC_data` sheet with Parameter / Control Level / SD / CV% / Bias% columns).

---

## TEa Sources

| Key | Source | Category |
|---|---|---|
| CLIA | Clinical Laboratory Improvement Amendments | Regulatory |
| CLIA 2024 | CLIA PT Criteria 2024 revision | Regulatory |
| BV | EFLM Biological Variation Database | Biological Variation |
| NCEP | National Cholesterol Education Program | Clinical Guidelines |
| KDIGO | Kidney Disease: Improving Global Outcomes | Clinical Guidelines |
| NGSP | National Glycohemoglobin Standardization Program | Standardization |
| RCPA | Royal College of Pathologists of Australasia | EQA |
| ESFEQA | Spanish Society of Laboratory Medicine EQA | EQA |
| Westgard | Westgard QC (westgard.com) | QC Resources |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Calculations | Pure Python (no external math libs) |
| Charts (server) | Matplotlib |
| Charts (browser) | Plotly.js |
| PDF export | fpdf2 |
| Excel export | openpyxl |
| Batch import | pandas |
| Frontend | Vanilla HTML / CSS / JavaScript |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
