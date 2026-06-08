"""FastAPI application for Sigma Metric Calculator."""

from __future__ import annotations
import io
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from fastapi.responses import Response

from calculator import calculate_sigma, calculate_qgi, opspecs_chart_data, SigmaResult
from references import REFERENCES, CATEGORY_ORDER
from report import generate_pdf, generate_excel
from tea_database import TEA_DATABASE

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Sigma Metric Calculator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# ── Pydantic Models ────────────────────────────────────────────────────────────

class CalculateRequest(BaseModel):
    analyte: str = Field(..., min_length=1)
    department: str = Field(..., min_length=1)
    tea: float = Field(..., gt=0, description="Total Allowable Error (%)")
    bias_pct: float = Field(..., description="Bias (%)")
    cv_pct: float = Field(..., gt=0, description="CV (%)")
    tea_source: str = Field(default="")

    @field_validator("department")
    @classmethod
    def validate_dept(cls, v: str) -> str:
        valid = {"Hematology", "Clinical Chemistry", "Clinical Immunology"}
        if v not in valid:
            raise ValueError(f"department must be one of {valid}")
        return v


class OPSpecsRequest(BaseModel):
    tea: float = Field(..., gt=0)
    cv_min: float = Field(default=0.5, gt=0)
    cv_max: float = Field(default=15.0, gt=0)


class ReportRequest(BaseModel):
    results: list[dict]
    format: str = Field(default="excel", pattern="^(pdf|excel)$")
    lab: str = Field(default="")
    analyzer: str = Field(default="")
    department: str = Field(default="")
    period: str = Field(default="")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _result_to_dict(r: SigmaResult) -> dict:
    return {
        "analyte":      r.analyte,
        "department":   r.department,
        "tea":          r.tea,
        "bias_pct":     r.bias_pct,
        "cv_pct":       r.cv_pct,
        "sigma":        r.sigma,
        "grade":        r.grade,
        "grade_color":  r.grade_color,
        "qc_rules":     r.qc_rules,
        "interpretation": r.interpretation,
        "tea_source":   r.tea_source,
        "qgi":          r.qgi,
        "qgi_label":    r.qgi_label,
        "qgi_color":    r.qgi_color,
        "qgi_action":   r.qgi_action,
    }


def _parse_iqc_excel(content: bytes) -> list[dict]:
    """
    Parse the lab's native IQC Excel format.
    Detects 'IQC_data' sheet with columns: Parameter, Control Level, SD, CV(%), Bias(%).
    Returns rows suitable for batch calculation. TEa is looked up from the built-in database.
    """
    xl = pd.ExcelFile(io.BytesIO(content))
    if "IQC_data" not in xl.sheet_names:
        return []

    df = xl.parse("IQC_data", header=None)

    # Find header row
    header_row = None
    for i, row in df.iterrows():
        vals = [str(v).strip().lower() for v in row.values if pd.notna(v)]
        if "parameter" in vals and "cv (%)" in vals:
            header_row = i
            break
    if header_row is None:
        return []

    df.columns = [str(c).strip().lower() if pd.notna(c) else f"col_{i}"
                  for i, c in enumerate(df.iloc[header_row])]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    # Normalise column names
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "parameter" in cl:     col_map[c] = "analyte"
        elif "control" in cl:     col_map[c] = "level"
        elif "cv" in cl:          col_map[c] = "cv_pct"
        elif "bias" in cl:        col_map[c] = "bias_pct"
    df = df.rename(columns=col_map)

    # Forward-fill analyte name
    if "analyte" in df.columns:
        df["analyte"] = df["analyte"].replace("", pd.NA).ffill()

    rows = []
    tea_lookup = {k.lower(): v for k, v in TEA_DATABASE.items()}
    alias = {"hb": "hemoglobin", "hgb": "hemoglobin", "hct": "hematocrit",
             "plt": "platelets", "wbc": "wbc", "rbc": "rbc", "mcv": "mcv"}

    for _, row in df.iterrows():
        analyte = str(row.get("analyte", "")).strip()
        level   = str(row.get("level", "")).strip()
        if not analyte or analyte.lower() in ("nan", "parameter", ""):
            continue
        if level.lower() not in ("low", "normal", "high", "average"):
            continue
        try:
            cv   = float(row["cv_pct"])
            bias = float(row["bias_pct"])
        except (KeyError, ValueError, TypeError):
            continue
        if cv <= 0:
            continue

        # TEa lookup
        key = analyte.lower()
        key = alias.get(key, key)
        tea_info = next(
            (v for k, v in tea_lookup.items() if k == key or key in k or k in k),
            None
        )
        tea     = tea_info["tea"]     if tea_info else None
        dept    = tea_info["department"] if tea_info else "Hematology"
        src     = tea_info["source"]  if tea_info else ""

        rows.append({
            "analyte":    f"{analyte} ({level})",
            "department": dept,
            "tea":        tea,
            "bias_pct":   bias,
            "cv_pct":     cv,
            "tea_source": src,
        })
    return rows


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/analytes")
def list_analytes(department: Optional[str] = None):
    """Return analytes from the TEa database, optionally filtered by department."""
    data = []
    for name, info in TEA_DATABASE.items():
        if department and info["department"] != department:
            continue
        data.append({
            "name":       name,
            "department": info["department"],
            "tea":        info["tea"],
            "unit":       info["unit"],
            "source":     info["source"],
        })
    return {"analytes": sorted(data, key=lambda x: x["name"])}


@app.post("/api/calculate")
def calculate(req: CalculateRequest):
    """Calculate Sigma metric for a single analyte."""
    try:
        result = calculate_sigma(
            analyte=req.analyte,
            department=req.department,
            tea=req.tea,
            bias_pct=req.bias_pct,
            cv_pct=req.cv_pct,
            tea_source=req.tea_source,
        )
        return _result_to_dict(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/qgi")
def qgi_only(bias_pct: float, cv_pct: float):
    """Calculate QGI standalone."""
    try:
        return calculate_qgi(bias_pct, cv_pct)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/batch")
async def batch_calculate(file: UploadFile = File(...)):
    """
    Batch calculate from CSV or Excel.
    Accepts:
      1. Standard format — columns: analyte, department, tea, bias_pct, cv_pct [, tea_source]
      2. Lab IQC format  — Excel with 'IQC_data' sheet (auto-detected)
    """
    content  = await file.read()
    filename = file.filename or ""

    if not filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=415, detail="Only CSV and Excel files are supported.")

    # Try lab IQC format first (Excel only)
    iqc_rows = []
    if filename.endswith((".xlsx", ".xls")):
        try:
            iqc_rows = _parse_iqc_excel(content)
        except Exception:
            pass

    results, errors = [], []

    if iqc_rows:
        for i, row in enumerate(iqc_rows):
            if row["tea"] is None:
                errors.append({"row": i + 1, "error": f"TEa not found for '{row['analyte']}'"})
                continue
            try:
                r = calculate_sigma(**row)
                results.append(_result_to_dict(r))
            except Exception as e:
                errors.append({"row": i + 1, "error": str(e)})
        return {"results": results, "errors": errors, "total": len(results), "format": "iqc"}

    # Standard flat format
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    required = {"analyte", "department", "tea", "bias_pct", "cv_pct"}
    missing  = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing columns: {', '.join(sorted(missing))}. "
                   f"Required: analyte, department, tea, bias_pct, cv_pct",
        )

    for i, row in df.iterrows():
        try:
            r = calculate_sigma(
                analyte=str(row["analyte"]),
                department=str(row["department"]),
                tea=float(row["tea"]),
                bias_pct=float(row["bias_pct"]),
                cv_pct=float(row["cv_pct"]),
                tea_source=str(row.get("tea_source", "")),
            )
            results.append(_result_to_dict(r))
        except Exception as e:
            errors.append({"row": i + 2, "error": str(e)})

    return {"results": results, "errors": errors, "total": len(results), "format": "standard"}


@app.post("/api/report")
def report(req: ReportRequest):
    """Generate a PDF or Excel report from a list of sigma results."""
    meta = {
        "lab":        req.lab,
        "analyzer":   req.analyzer,
        "department": req.department,
        "period":     req.period,
    }
    try:
        if req.format == "pdf":
            data     = generate_pdf(req.results, meta)
            filename = "sigma_report.pdf"
            media    = "application/pdf"
        else:
            data     = generate_excel(req.results, meta)
            filename = "sigma_report.xlsx"
            media    = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/opspecs")
def opspecs(req: OPSpecsRequest):
    """Generate OPSpecs chart data for a given TEa."""
    return opspecs_chart_data(req.tea, (req.cv_min, req.cv_max))


@app.get("/api/references")
def get_references():
    """Return the full TEa source reference index."""
    items = []
    for key, ref in REFERENCES.items():
        items.append({"key": key, **ref})
    # Sort by category order, then alphabetically within category
    order_map = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    items.sort(key=lambda x: (order_map.get(x["category"], 99), x["key"]))
    return {"references": items, "categories": CATEGORY_ORDER}


@app.get("/api/references/{source_key}")
def get_reference(source_key: str):
    """Return a single TEa source reference."""
    ref = REFERENCES.get(source_key)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Reference '{source_key}' not found.")
    return {"key": source_key, **ref}


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Static frontend ────────────────────────────────────────────────────────────

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
