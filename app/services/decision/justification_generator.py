"""Generates a plain-language explanation of an already-made decision.
This is explanation only - DecisionEngine makes the actual decision
(deterministic, rule-based). The LLM never decides anything here; it only
phrases facts that already exist into readable prose."""

from app.adapters.openrouter import openrouter
from app.prompts import render_prompt
from app.schemas.application import FinalDecision, RiskAssessment, VerificationReport

async def generate_justification(decision: FinalDecision, risk_assessment: RiskAssessment, verification: VerificationReport) -> str:
    reasons_text = "\n".join(f"- {reason}" for reason in decision.reasons)
    risk_factors_text = "\n".join(f"- {factor.name}: {factor.points:+d} points - {factor.detail}" for factor in risk_assessment.factors)
    verification_text = "\n".join(f"- {check.field_name}: {check.status}" for check in verification.checks)

    prompt = render_prompt(
        "generate_justification.jinja2",
        decision=decision.decision,
        reasons=reasons_text,
        risk_factors=risk_factors_text,
        verification_checks=verification_text
    )
    return await openrouter.chat(prompt=prompt, json_mode=False)

