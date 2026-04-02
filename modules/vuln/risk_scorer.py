#!/usr/bin/env python3
"""Risk scoring engine — CVSS-based with contextual weighting"""

from core.logger import get_logger

log = get_logger("RiskScorer")

# Severity weights (0–10 scale)
WEIGHTS = {
    "critical": 10.0,
    "high":      7.5,
    "medium":    5.0,
    "low":       2.5,
    "info":      0.5,
}

# Context multipliers
CONTEXT = {
    "internet_exposed":    1.5,
    "authenticated_bypass": 2.0,
    "data_exposure":        1.8,
    "rce":                  2.5,
    "privilege_escalation": 2.0,
    "default":              1.0,
}


class RiskScorer:
    def __init__(self, cfg):
        self.cfg = cfg

    def score(self, findings: list, context: dict = None) -> dict:
        if not findings:
            return {"score": 0, "rating": "Clean", "breakdown": {}}

        breakdown = {sev: 0 for sev in WEIGHTS}
        raw_score = 0.0

        for f in findings:
            sev     = f.get("severity", "info").lower()
            weight  = WEIGHTS.get(sev, 0.5)
            ctx_key = self._detect_context(f)
            mult    = CONTEXT.get(ctx_key, 1.0)
            raw_score += weight * mult
            breakdown[sev] = breakdown.get(sev, 0) + 1

        # Normalize to 0–100
        max_possible = len(findings) * WEIGHTS["critical"] * max(CONTEXT.values())
        score = min(int((raw_score / max(max_possible, 1)) * 100), 100)

        rating = self._rating(score)
        log.info(f"  [RiskScorer] Score: {score}/100 — {rating}")

        return {
            "score":     score,
            "rating":    rating,
            "breakdown": breakdown,
            "raw":       round(raw_score, 2),
        }

    def _detect_context(self, finding: dict) -> str:
        name = (finding.get("name", "") + " " + finding.get("template", "")).lower()
        if any(k in name for k in ("rce", "remote code", "command injection")):
            return "rce"
        if any(k in name for k in ("privilege", "escalation", "sudo")):
            return "privilege_escalation"
        if any(k in name for k in ("bypass", "authentication")):
            return "authenticated_bypass"
        if any(k in name for k in ("exposure", "disclosure", "sensitive")):
            return "data_exposure"
        return "default"

    def _rating(self, score: int) -> str:
        if score >= 80: return "CRITICAL"
        if score >= 60: return "HIGH"
        if score >= 40: return "MEDIUM"
        if score >= 20: return "LOW"
        return "INFORMATIONAL"
