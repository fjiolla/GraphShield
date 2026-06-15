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

    system_prompt = """You are GraphShield AI Assistant — a smart, friendly AI assistant embedded in a bias detection platform.

You behave like ChatGPT. You can answer ANY question the user asks — whether it's about their audit results, general AI/ML concepts, fairness, coding, life advice, or literally anything else. You are not limited to bias topics only.

However, you have special context: you can see the user's current audit results (if any are active). Use this to give specific, data-driven answers when they ask about their audits.

IMPORTANT RULES:
- If the user asks about a specific audit type (e.g., "explain the graph audit") but that audit was NOT run (not in context), clearly say: "I don't see any [graph/model/dataset] audit results right now. It looks like you ran a [document] audit — would you like me to explain those results instead?"
- Be conversational and natural. Short greetings get short replies.
- You can answer general questions about AI, bias, fairness, coding, math, or anything else — you're not restricted.
- When audit context IS available, reference specific numbers, groups, and findings from it.
- Never make up audit results that aren't in the context provided."""

    prompt = f"""CURRENT AUDIT CONTEXT (what the user is looking at right now):
{audit_context}

USER MESSAGE: {request.message}

Respond naturally. Be helpful, specific, and conversational."""

    try:
        reply, _ = llm_generate(prompt, system_prompt=system_prompt, max_tokens=1024)
        return ChatResponse(reply=reply.strip(), provider="gemini")
    except Exception as e:
        logger.error("Chat failed: %s", e)
        raise HTTPException(status_code=502, detail=f"AI assistant unavailable: {str(e)}")
