"""
PDF Export — Generate downloadable audit reports.
Uses simple HTML-to-PDF approach with minimal dependencies.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.core.struct_local_config import SQLITE_DB_PATH

logger = logging.getLogger("export_api")

router = APIRouter()


def _generate_html_report(audit_data: dict, audit_type: str) -> str:
    """Generate a professional HTML report from audit data."""
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    
    # Build findings section
    findings_html = ""
    if audit_type == "Dataset Audit":
        report = audit_data
        findings_list = report.get("findings", [])
        recommendations_list = report.get("recommendations", [])
        
        findings_html = f"""
        <div class="section">
            <h2>Risk Assessment</h2>
            <div class="metric-box {'danger' if report.get('risk_level') == 'High' else 'warning' if report.get('risk_level') == 'Medium' else 'success'}">
                <span class="label">Risk Level</span>
                <span class="value">{report.get('risk_level', 'N/A')}</span>
            </div>
            <p class="summary">{report.get('summary', 'No summary available.')}</p>
        </div>
        <div class="section">
            <h2>Key Findings</h2>
            <ul>{''.join(f'<li>{f}</li>' for f in findings_list)}</ul>
        </div>
        <div class="section">
            <h2>Recommendations</h2>
            <ul>{''.join(f'<li>{r}</li>' for r in recommendations_list)}</ul>
        </div>
        """
    elif audit_type == "Model Audit":
        result = audit_data
        verdict = result.get("verdict", {})
        narratives = result.get("ai_narrative", [])
        
        findings_html = f"""
        <div class="section">
            <h2>Model Verdict</h2>
            <div class="metric-box {'danger' if verdict.get('bias_verdict') == 'BIASED' else 'warning' if verdict.get('bias_verdict') == 'MARGINAL' else 'success'}">
                <span class="label">Bias Verdict</span>
                <span class="value">{verdict.get('bias_verdict', 'N/A')}</span>
            </div>
            <p class="summary">{verdict.get('verdict_reason', '')}</p>
            <div class="metrics-grid">
                <div class="metric"><span class="label">Confidence</span><span class="value">{verdict.get('bias_confidence', 'N/A')}</span></div>
                <div class="metric"><span class="label">Worst DIR</span><span class="value">{verdict.get('worst_disparate_impact_ratio', 'N/A')}</span></div>
                <div class="metric"><span class="label">Worst Group</span><span class="value">{verdict.get('worst_group', 'N/A')}</span></div>
                <div class="metric"><span class="label">Fairness Score</span><span class="value">{result.get('governance', {}).get('overall_fairness_score', 'N/A')}/100</span></div>
            </div>
        </div>
        {''.join(f'<div class="section"><h2>{n["title"]}</h2><p>{n["content"]}</p></div>' for n in narratives)}
        """
    elif audit_type == "Document Audit":
        findings = audit_data.get("findings", {})
        qual = findings.get("qualitative_analysis", {})
        profile = qual.get("dynamic_profile", {})
        groups = profile.get("groups", [])
        
        groups_html = ""
        for g in groups:
            groups_html += f"""
            <div class="group-card">
                <h3>{g.get('group_name', 'Unknown')}</h3>
                <p><strong>Category:</strong> {g.get('bias_category', 'N/A')} | <strong>Type:</strong> {g.get('bias_type', 'N/A')} | <strong>Intensity:</strong> {g.get('bias_intensity', 0)}</p>
                <p><strong>Evidence:</strong> {'; '.join(g.get('evidence', []))}</p>
            </div>
            """
        
        findings_html = f"""
        <div class="section">
            <h2>Bias Groups Detected</h2>
            {groups_html}
        </div>
        """
    else:
        findings_html = f"<div class='section'><h2>Raw Data</h2><pre>{json.dumps(audit_data, indent=2, default=str)[:3000]}</pre></div>"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>GraphShield AI — Audit Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #1C1C1A; }}
.header {{ text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid #4D6B44; }}
.header h1 {{ color: #4D6B44; font-size: 24px; margin: 0; }}
.header p {{ color: #6B6B68; font-size: 13px; margin-top: 8px; }}
.section {{ margin-bottom: 30px; }}
.section h2 {{ color: #2F412A; font-size: 18px; border-bottom: 1px solid #E8E6E0; padding-bottom: 8px; }}
.metric-box {{ display: inline-block; padding: 12px 20px; border-radius: 12px; margin: 10px 0; }}
.metric-box.danger {{ background: #FEF2F1; border: 1px solid #FCCFCC; }}
.metric-box.warning {{ background: #FFF8F1; border: 1px solid #FCE8D3; }}
.metric-box.success {{ background: #F0FDF4; border: 1px solid #D5E1D1; }}
.metric-box .label {{ font-size: 11px; text-transform: uppercase; color: #6B6B68; display: block; }}
.metric-box .value {{ font-size: 20px; font-weight: 700; }}
.metric-box.danger .value {{ color: #C0392B; }}
.metric-box.warning .value {{ color: #B87D52; }}
.metric-box.success .value {{ color: #4D6B44; }}
.summary {{ font-size: 14px; color: #4A4A48; line-height: 1.6; margin-top: 12px; }}
.metrics-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 16px; }}
.metric {{ background: #F5F4F0; padding: 12px; border-radius: 8px; }}
.metric .label {{ font-size: 11px; color: #6B6B68; text-transform: uppercase; }}
.metric .value {{ font-size: 16px; font-weight: 600; color: #1C1C1A; }}
ul {{ padding-left: 20px; }}
li {{ margin-bottom: 8px; font-size: 14px; line-height: 1.5; color: #4A4A48; }}
.group-card {{ background: #F5F4F0; border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
.group-card h3 {{ margin: 0 0 8px; font-size: 15px; color: #1C1C1A; }}
.group-card p {{ margin: 4px 0; font-size: 13px; color: #4A4A48; }}
.footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E8E6E0; font-size: 11px; color: #A8A6A0; }}
pre {{ background: #F5F4F0; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 12px; }}
</style>
</head>
<body>
<div class="header">
    <h1>🛡️ GraphShield AI — Audit Report</h1>
    <p>Generated on {timestamp} • Audit Type: {audit_type}</p>
</div>
{findings_html}
<div class="footer">
    <p>Generated by GraphShield AI — Enterprise Bias Detection & Fairness Platform</p>
    <p>Compliant with EU AI Act, EEOC Guidelines, and India AI Regulations</p>
</div>
</body>
</html>"""
    return html


@router.get("/report")
async def export_report(
    audit_id: Optional[str] = Query(None, description="Specific audit ID to export"),
    audit_type: Optional[str] = Query(None, description="Type filter: Dataset Audit, Model Audit, Document Audit"),
    format: str = Query("html", description="Export format: html or json"),
):
    """
    Export an audit report. Returns HTML (print-to-PDF in browser) or JSON.
    If no audit_id provided, exports the most recent audit.
    """
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        audit_data = None
        resolved_type = audit_type or "Unknown"
        
        if audit_id:
            # Try each table to find the audit
            for table, type_name, id_col, json_col in [
                ("audit_sessions", "Dataset Audit", "session_id", "report_json"),
                ("model_audits", "Model Audit", "job_id", "result_json"),
                ("document_audits", "Document Audit", "session_id", "result_json"),
            ]:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor = conn.execute(f"SELECT {json_col} FROM {table} WHERE {id_col} = ?", (audit_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        audit_data = json.loads(row[0])
                        resolved_type = type_name
                        break
        else:
            # Get the most recent audit
            for table, type_name, json_col, date_col in [
                ("model_audits", "Model Audit", "result_json", "timestamp"),
                ("audit_sessions", "Dataset Audit", "report_json", "created_at"),
                ("document_audits", "Document Audit", "result_json", "timestamp"),
            ]:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor = conn.execute(f"SELECT {json_col} FROM {table} ORDER BY {date_col} DESC LIMIT 1")
                    row = cursor.fetchone()
                    if row and row[0]:
                        audit_data = json.loads(row[0])
                        resolved_type = type_name
                        break
        
        conn.close()
        
        if not audit_data:
            raise HTTPException(status_code=404, detail="No audit found to export")
        
        if format == "json":
            return audit_data
        
        # Generate HTML report
        html_content = _generate_html_report(audit_data, resolved_type)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'inline; filename="graphshield_report_{datetime.now().strftime("%Y%m%d")}.html"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Export failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
