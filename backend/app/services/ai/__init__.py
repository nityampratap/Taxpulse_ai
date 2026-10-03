"""AI copilot: provider chain with grounding check and fallback."""
import json
import logging
import os
import re
import time
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import AIInteraction, Case, Invoice, ReconciliationResult, Vendor, Payment

logger = logging.getLogger(__name__)


class CaseContext:
    """Typed, redacted context for AI — no DB access for the model."""

    @staticmethod
    def build(db: Session, case: Case) -> Dict[str, Any]:
        result = db.query(ReconciliationResult).filter_by(id=case.reconciliation_result_id).first()
        invoice = db.query(Invoice).filter_by(id=result.invoice_id).first() if result and result.invoice_id else None
        vendor = db.query(Vendor).filter_by(id=invoice.vendor_id).first() if invoice else None
        payment = db.query(Payment).filter_by(id=result.payment_id).first() if result and result.payment_id else None

        ctx = {
            "case_number": case.case_number,
            "status": case.status,
            "risk_score": str(case.risk_score),
            "risk_level": case.priority,
            "financial_exposure": str(case.financial_exposure),
            "tax_impact": str(case.tax_impact),
            "risk_factors": case.factor_breakdown,
        }
        if result:
            ctx["reconciliation"] = {
                "match_type": result.match_type,
                "status": result.status,
                "confidence": str(result.confidence_score),
                "variance_amount": str(result.variance_amount),
                "reason_codes": result.reason_codes,
                "evidence": result.evidence,
            }
        if invoice:
            ctx["invoice"] = {
                "number": invoice.invoice_number,
                "date": str(invoice.invoice_date),
                "subtotal": str(invoice.subtotal),
                "tax_amount": str(invoice.tax_amount),
                "total_amount": str(invoice.total_amount),
                "currency": invoice.currency,
            }
        if vendor:
            ctx["vendor"] = {
                "name": vendor.name,
                "tax_id": vendor.tax_identifier,
                "risk_tier": vendor.risk_tier,
                "disputes": vendor.dispute_count,
            }
        if payment:
            ctx["payment"] = {
                "reference": payment.payment_reference,
                "date": str(payment.payment_date),
                "amount": str(payment.amount_paid),
                "method": payment.payment_method,
            }
        return ctx


def _extract_numbers(text: str) -> set:
    """Extract numeric values from text for grounding check."""
    nums = set()
    for m in re.findall(r'[\d,]+\.?\d*', text):
        try:
            nums.add(str(Decimal(m.replace(",", ""))))
        except Exception:
            pass
    return nums


def _grounding_check(response: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Every number in the AI output must exist somewhere in the context."""
    response_text = json.dumps(response, default=str)
    context_text = json.dumps(context, default=str)
    response_nums = _extract_numbers(response_text)
    context_nums = _extract_numbers(context_text)
    if not response_nums:
        return True
    ungrounded = response_nums - context_nums
    if ungrounded:
        logger.warning("Grounding check failed: ungrounded numbers %s", ungrounded)
        return False
    return True


class BaseAIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class GroqProvider(BaseAIProvider):
    name = "GROQ"

    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        api_key = os.environ.get("GROQ_API_KEY", "")
        base_url = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        model = os.environ.get("GROQ_MODEL", "")
        if not api_key or not model or api_key == "UPDATE_ME":
            raise ValueError("GROQ_API_KEY or GROQ_MODEL not configured")

        system_prompt = (
            "You are a tax compliance analyst. Analyze the case data and respond ONLY with valid JSON. "
            "Schema: {summary, reason, evidence[], financial_impact, tax_impact, confidence, recommended_action}. "
            "Use only numbers from the provided context. Never fabricate data."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{prompt}\n\nCase data:\n{json.dumps(context, default=str)}"},
        ]
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "response_format": {"type": "json_object"},
                  "temperature": 0.1, "max_tokens": 1024},
            timeout=30.0,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)


class GeminiProvider(BaseAIProvider):
    name = "GEMINI"

    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        api_key = os.environ.get("GEMINI_API_KEY", "")
        model = os.environ.get("GEMINI_MODEL", "")
        if not api_key or not model or api_key == "UPDATE_ME":
            raise ValueError("GEMINI_API_KEY or GEMINI_MODEL not configured")

        full_prompt = (
            "You are a tax compliance analyst. Analyze this case and respond ONLY with valid JSON.\n"
            f"Schema: {{summary, reason, evidence[], financial_impact, tax_impact, confidence, recommended_action}}\n"
            f"Use only numbers from the provided data. Never fabricate.\n\n"
            f"{prompt}\n\nCase data:\n{json.dumps(context, default=str)}"
        )
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": full_prompt}]}],
                  "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024,
                                       "responseMimeType": "application/json"}},
            timeout=30.0,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)


class MockAIProvider(BaseAIProvider):
    """Template-based provider using real case data. No LLM calls."""
    name = "MOCK"

    def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        inv = context.get("invoice", {})
        recon = context.get("reconciliation", {})
        vendor = context.get("vendor", {})
        evidence_items = recon.get("reason_codes", []) or []

        variance = context.get("tax_impact", "0")
        subtotal = inv.get("subtotal", "0")
        tax_amount = inv.get("tax_amount", "0")
        total = inv.get("total_amount", "0")

        return {
            "summary": (
                f"Tax variance detected for {vendor.get('name', 'vendor')} "
                f"on invoice {inv.get('number', 'N/A')}. "
                f"Taxable base: {subtotal}, recorded tax: {tax_amount}, "
                f"total: {total}. Variance: {variance}."
            ),
            "reason": f"Recorded tax differs from expected statutory calculation by {variance}.",
            "evidence": evidence_items if evidence_items else [recon.get("status", "UNKNOWN")],
            "financial_impact": str(context.get("financial_exposure", "0")),
            "tax_impact": str(variance),
            "confidence": "0.85",
            "recommended_action": "Review tax calculation and request correction from vendor if warranted.",
            "provider": "MOCK",
        }


class AIService:
    """Manages AI provider chain with fallback and grounding."""

    def __init__(self):
        order = os.environ.get("AI_PROVIDER_ORDER", "groq,gemini,mock")
        self.provider_order = [p.strip().lower() for p in order.split(",")]
        self._providers = {
            "groq": GroqProvider,
            "gemini": GeminiProvider,
            "mock": MockAIProvider,
        }

    def explain_case(
        self,
        db: Session,
        case: Case,
        prompt: str = "Explain this tax discrepancy case.",
        actor_id: str = "SYSTEM",
    ) -> Dict[str, Any]:
        context = CaseContext.build(db, case)
        provider_used = None
        provider_fallback = []
        result = None
        start = time.time()

        for provider_name in self.provider_order:
            provider_cls = self._providers.get(provider_name)
            if not provider_cls:
                continue
            try:
                provider = provider_cls()
                response = provider.generate(prompt, context)
                if not _grounding_check(response, context):
                    provider_fallback.append(f"{provider_name}:grounding_failed")
                    continue
                provider_used = provider_name.upper()
                response["provider"] = provider_used
                result = response
                break
            except Exception as e:
                logger.warning("AI provider %s failed: %s", provider_name, e)
                provider_fallback.append(f"{provider_name}:{str(e)[:50]}")
                continue

        latency_ms = int((time.time() - start) * 1000)

        if not result:
            result = MockAIProvider().generate(prompt, context)
            provider_used = "MOCK"
            result["provider"] = "MOCK"

        # Log interaction
        interaction = AIInteraction(
            id=str(uuid.uuid4()),
            organization_id=case.organization_id,
            case_id=case.id,
            provider=provider_used or "MOCK",
            prompt_context=context,
            response_text=json.dumps(result, default=str),
            tokens_used=0,
            latency_ms=latency_ms,
        )
        db.add(interaction)

        # Audit event
        from app.services.audit import AuditService
        AuditService.log(
            db,
            organization_id=case.organization_id,
            event_type="AI_ANALYSIS_COMPLETED",
            actor_id=actor_id,
            entity_type="case",
            entity_id=case.id,
            after_state={"provider": provider_used, "fallback": provider_fallback},
        )

        result["_meta"] = {
            "provider_used": provider_used,
            "provider_fallback": provider_fallback,
            "latency_ms": latency_ms,
        }
        return result
