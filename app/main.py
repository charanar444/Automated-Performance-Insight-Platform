from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from app.ingestion.loader import load_file
from app.ingestion.schema_detector import detect_schema, validate_schema
from app.analytics.engine import run_analytics
from app.visuals.charts import generate_charts
from app.reports.exporter import generate_pdf_report

app = FastAPI(
    title="Automated Performance Insight Platform",
    description="Upload CSV or Excel files to receive automated performance insights.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return FileResponse("app/static/dashboard.html")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts CSV or Excel. Returns schema, analytics, and chart data.
    """
    try:
        df = load_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    schema     = detect_schema(df)
    validation = validate_schema(schema)

    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["errors"])

    analytics = run_analytics(df.copy(), schema)
    charts    = generate_charts(df.copy(), schema)

    return {
        "filename":   file.filename,
        "rows":       len(df),
        "columns":    list(df.columns),
        "schema":     schema,
        "validation": validation,
        "preview":    df.head(5).to_dict(orient="records"),
        "analytics":  analytics,
        "charts":     charts
    }


@app.post("/report")
async def download_report(file: UploadFile = File(...)):
    """
    Accepts CSV or Excel. Returns a downloadable PDF report.
    """
    try:
        df = load_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    schema     = detect_schema(df)
    validation = validate_schema(schema)

    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["errors"])

    analytics = run_analytics(df.copy(), schema)
    charts    = generate_charts(df.copy(), schema)

    report_data = {
        "filename":  file.filename,
        "rows":      len(df),
        "analytics": analytics,
        "charts":    charts
    }

    pdf_bytes = generate_pdf_report(report_data)
    filename  = file.filename.replace(".csv", "").replace(".xlsx", "")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{filename}.pdf"
        }
    )