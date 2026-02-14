from xhtml2pdf import pisa
from typing import Dict
import datetime
import io


def generate_pdf_report(data: Dict) -> bytes:
    """
    Generate a professional PDF report from analytics data.
    Returns PDF as bytes using xhtml2pdf.
    """
    html_content = build_report_html(data)
    pdf_buffer   = io.BytesIO()
    pisa.CreatePDF(html_content, dest=pdf_buffer)
    return pdf_buffer.getvalue()


def build_report_html(data: Dict) -> str:
    """
    Build clean HTML content for PDF conversion.
    """
    now = datetime.datetime.now().strftime("%B %d, %Y")

    # ── KPI Rows ──
    kpi_rows = ""
    if data["analytics"].get("category_analysis"):
        for category, cat_data in data["analytics"]["category_analysis"].items():
            for metric, stats in cat_data["summary"].items():
                comp      = cat_data["period_comparison"].get(metric, {})
                pct       = comp.get("pct_change", 0)
                direction = comp.get("direction", "")
                arrow     = "UP" if direction == "up" else "DOWN" if direction == "down" else "STABLE"
                color     = "#16a34a" if direction == "up" else "#dc2626" if direction == "down" else "#f59e0b"
                sign      = "+" if pct > 0 else ""
                kpi_rows += f"""
                <tr>
                    <td>{category}</td>
                    <td>{metric.replace('_', ' ').title()}</td>
                    <td><b>{stats['latest']}</b></td>
                    <td>{stats['average']}</td>
                    <td>{stats['max']}</td>
                    <td>{stats['min']}</td>
                    <td style="color:{color}"><b>{arrow} {sign}{pct}%</b></td>
                </tr>"""
    else:
        for kpi in data["charts"]["kpi_cards"]:
            pct       = kpi["pct_change_from_previous"]
            direction = kpi["trend"]
            arrow     = "UP" if direction == "up" else "DOWN" if direction == "down" else "STABLE"
            color     = "#16a34a" if direction == "up" else "#dc2626" if direction == "down" else "#f59e0b"
            sign      = "+" if pct > 0 else ""
            kpi_rows += f"""
            <tr>
                <td>--</td>
                <td>{kpi['label']}</td>
                <td><b>{kpi['latest']}</b></td>
                <td>{kpi['average']}</td>
                <td>{kpi['max']}</td>
                <td>{kpi['min']}</td>
                <td style="color:{color}"><b>{arrow} {sign}{pct}%</b></td>
            </tr>"""

    # ── Insight Rows ──
    insight_rows = ""
    if data["analytics"].get("category_analysis"):
        for category, cat_data in data["analytics"]["category_analysis"].items():
            for metric, trend in cat_data["trends"].items():
                direction = trend["direction"]
                color     = "#16a34a" if direction == "improving" else "#dc2626" if direction == "declining" else "#f59e0b"
                insight_rows += f"""
                <tr>
                    <td>{category}</td>
                    <td>{metric.replace('_', ' ').title()}</td>
                    <td style="color:{color}"><b>{direction.upper()}</b></td>
                    <td>{trend['interpretation']}</td>
                </tr>"""

            for metric, comp in cat_data["period_comparison"].items():
                direction = comp["direction"]
                color     = "#16a34a" if direction == "up" else "#dc2626" if direction == "down" else "#f59e0b"
                insight_rows += f"""
                <tr>
                    <td>{category} (Period)</td>
                    <td>{metric.replace('_', ' ').title()}</td>
                    <td style="color:{color}"><b>{direction.upper()}</b></td>
                    <td>{comp['note']}</td>
                </tr>"""

    # ── Anomaly Section ──
    anomaly_section = ""
    anomalies = data["analytics"].get("anomalies", [])
    if anomalies:
        anomaly_rows = ""
        for a in anomalies:
            anomaly_rows += f"""
            <tr>
                <td>{a['metric'].replace('_', ' ').title()}</td>
                <td>{a['date']}</td>
                <td>{a['value']}</td>
                <td style="color:#dc2626"><b>{a['flag'].upper()}</b></td>
                <td>{a['note']}</td>
            </tr>"""
        anomaly_section = f"""
        <h2>Anomalies Detected</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th><th>Date</th>
                    <th>Value</th><th>Flag</th><th>Note</th>
                </tr>
            </thead>
            <tbody>{anomaly_rows}</tbody>
        </table>"""

    # ── Full HTML ──
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <style>
    @page {{
      size: A4;
      margin: 20mm 18mm 20mm 18mm;
    }}

    body {{
      font-family: Helvetica, Arial, sans-serif;
      font-size: 10pt;
      color: #1e293b;
    }}

    .header {{
      background-color: #1e40af;
      color: white;
      padding: 16px 20px;
      margin-bottom: 20px;
    }}

    .header h1 {{
      font-size: 16pt;
      margin: 0 0 4px 0;
      color: white;
    }}

    .header p {{
      font-size: 9pt;
      margin: 0;
      color: #bfdbfe;
    }}

    .meta {{
      background-color: #eff6ff;
      border: 1px solid #bfdbfe;
      padding: 8px 14px;
      font-size: 9pt;
      color: #1e40af;
      margin-bottom: 20px;
    }}

    h2 {{
      color: #1e40af;
      font-size: 12pt;
      margin-top: 24px;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 2px solid #e2e8f0;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 16px;
      font-size: 9pt;
    }}

    th {{
      background-color: #1e40af;
      color: white;
      padding: 7px 9px;
      text-align: left;
    }}

    td {{
      padding: 6px 9px;
      border-bottom: 1px solid #e2e8f0;
    }}

    .footer {{
      margin-top: 32px;
      font-size: 8pt;
      color: #94a3b8;
      text-align: center;
      border-top: 1px solid #e2e8f0;
      padding-top: 10px;
    }}
  </style>
</head>
<body>

  <div class="header">
    <h1>Performance Insight Report</h1>
    <p>Automated Performance Insight Platform &middot; Chicago Education Advocacy Cooperative (ChiEAC)</p>
  </div>

  <div class="meta">
    <b>File:</b> {data['filename']} &nbsp;&nbsp;
    <b>Rows:</b> {data['rows']} &nbsp;&nbsp;
    <b>Generated:</b> {now}
  </div>

  <h2>Key Performance Indicators</h2>
  <table>
    <thead>
      <tr>
        <th>Category</th>
        <th>Metric</th>
        <th>Latest</th>
        <th>Average</th>
        <th>Max</th>
        <th>Min</th>
        <th>vs Previous</th>
      </tr>
    </thead>
    <tbody>{kpi_rows}</tbody>
  </table>

  <h2>Automated Insights</h2>
  <table>
    <thead>
      <tr>
        <th>Category</th>
        <th>Metric</th>
        <th>Trend</th>
        <th>Interpretation</th>
      </tr>
    </thead>
    <tbody>{insight_rows}</tbody>
  </table>

  {anomaly_section}

  <div class="footer">
    Generated by Automated Performance Insight Platform &middot;
    Chicago Education Advocacy Cooperative (ChiEAC) &middot; {now}
  </div>

</body>
</html>"""