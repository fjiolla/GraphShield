"""
AI Chat Assistant — Gemini-powered Q&A about bias audit results.
Users can ask questions about their audit results in natural language.
"""

import json
import sqlite3
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.struct_local_config import SQLITE_DB_PATH
from app.services.llm_gateway import llm_generate

logger = logging.getLogger("chat_api")

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    audit_context: Optional[str] = None  # Optional JSON string of current audit results


class ChatResponse(BaseModel):
    reply: str
    provider: str


def _get_recent_audits_context(limit: int = 5) -> str:
    """Fetch recent audit summaries for context."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        context_parts = []

        # Recent dataset audits
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_sessions'")
        if cursor.fetchone():
            cursor = conn.execute(
                "SELECT table_name, report_json, created_at FROM audit_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            for row in cursor.fetchall():
                try:
                    report = json.loads(row["report_json"]) if row["report_json"] else {}
                    context_parts.append(
                        f"Dataset Audit '{row['table_name']}' ({row['created_at']}): "
                        f"risk={report.get('risk_level', 'N/A')}, "
                        f"bias_detected={report.get('bias_detected', 'N/A')}, "
                        f"summary={report.get('summary', 'N/A')[:200]}"
                    )
                except Exception:
                    continue

        # Recent model audits
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_audits'")
        if cursor.fetchone():
            cursor = conn.execute(
                "SELECT session_id, result_json, timestamp FROM model_audits ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            for row in cursor.fetchall():
                try:
                    result = json.loads(row["result_json"]) if row["result_json"] else {}
                    verdict = result.get("verdict", {})
                    context_parts.append(
                        f"Model Audit '{row['session_id']}' ({row['timestamp']}): "
                        f"verdict={verdict.get('bias_verdict', 'N/A')}, "
                        f"score={result.get('governance', {}).get('overall_fairness_score', 'N/A')}"
                    )
                except Exception:
                    continue

        # Recent document audits
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_audits'")
        if cursor.fetchone():
            cursor = conn.execute(
                "SELECT filename, result_json, timestamp FROM document_audits ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            for row in cursor.fetchall():
                try:
                    result = json.loads(row["result_json"]) if row["result_json"] else {}
                    findings = result.get("findings", {}).get("qualitative_analysis", {})
                    profile = findings.get("dynamic_profile", {})
                    summary = profile.get("summary", {})
                    context_parts.append(
                        f"Document Audit '{row['filename']}' ({row['timestamp']}): "
                        f"overall_bias={summary.get('overall_bias', 'N/A')}, "
                        f"dominant_category={summary.get('dominant_bias_category', 'N/A')}"
                    )
                except Exception:
                    continue

        conn.close()
        return "\n".join(context_parts) if context_parts else "No previous audits found in the system."
    except Exception as e:
        logger.warning("Failed to fetch audit context: %s", e)
        return "Unable to fetch audit history."


@router.post("/ask", response_model=ChatResponse)
async def chat_ask(request: ChatRequest):
    """
    AI Chat endpoint. Answers questions about bias, fairness, and audit results.
    Uses Gemini first, falls back to Groq.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Build context
    audit_context = request.audit_context or _get_recent_audits_context()

    system_prompt = """You are GraphShield AI Assistant — a friendly, knowledgeable expert in AI fairness, bias detection, and responsible AI.

You have a warm, conversational tone. When users greet you casually (like "hey", "hi", "hello"), respond naturally and friendly — just like a helpful colleague would. Don't overthink it.

When users ask about technical topics, you can help with:
- Explaining fairness metrics (Disparate Impact, Demographic Parity, Equalized Odds, etc.)
- Interpreting audit results and identifying concerning patterns
- Suggesting remediation strategies for detected bias
- Explaining regulatory requirements (EU AI Act, EEOC guidelines, India's AI regulations)
- Making technical bias reports understandable to non-technical stakeholders

Be concise and natural. Don't be overly formal. If someone says "hey", just say hey back and ask how you can help — don't dump a wall of text about audits."""

    prompt = f"""CONTEXT (recent audit history from this system):
{audit_context}

USER: {request.message}

Respond naturally. If it's a greeting, be friendly and brief. If it's a question, be helpful and reference the audit context only if relevant."""

    try:
        reply = llm_generate(prompt, system_prompt=system_prompt, max_tokens=1024)
        # Determine which provider was used based on the gateway logs
        provider = "gemini"  # Default assumption (gateway tries Gemini first)
        return ChatResponse(reply=reply.strip(), provider=provider)
    except Exception as e:
        logger.error("Chat failed: %s", e)
        raise HTTPException(status_code=502, detail=f"AI assistant unavailable: {str(e)}")
