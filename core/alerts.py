#!/usr/bin/env python3
"""Real-time alert system — Slack, Telegram, Email notifications"""

import requests
import smtplib
from email.mime.text   import MIMEText
from email.mime.multipart import MIMEMultipart
from core.logger import get_logger

log = get_logger("Alerts")


class AlertModule:
    def __init__(self, cfg):
        self.cfg   = cfg
        self.creds = cfg.get("credentials") or {}

    def alert_finding(self, finding: dict, domain: str):
        """Send real-time alert for high/critical findings."""
        sev = finding.get("severity", "info").lower()
        if sev not in ("critical", "high"):
            return

        msg = (f"[SHAHEEN 3] {sev.upper()} finding on {domain}\n"
               f"Finding: {finding.get('name', '')}\n"
               f"URL: {finding.get('matched', '')}\n"
               f"Template: {finding.get('template', '')}")

        # Slack
        slack_wh = self.creds.get("slack_webhook")
        if slack_wh:
            self._slack(msg, slack_wh, sev)

        # Telegram
        tg = self.creds.get("telegram", {})
        if tg.get("token") and tg.get("chat_id"):
            self._telegram(msg, tg["token"], tg["chat_id"])

        # Email
        smtp = self.creds.get("smtp", {})
        if smtp.get("host") and smtp.get("to"):
            self._email(finding, domain, smtp)

    def _slack(self, message: str, webhook: str, severity: str):
        colours = {"critical": "#ff2d55", "high": "#ff9500",
                   "medium": "#ffcc00", "low": "#34c759"}
        try:
            requests.post(webhook, json={
                "attachments": [{
                    "color": colours.get(severity, "#888"),
                    "text":  message,
                    "footer": "Shaheen 3 by Professor Snape",
                }]
            }, timeout=10)
            log.debug("[Alert] Slack notification sent")
        except Exception as e:
            log.debug(f"[Alert] Slack error: {e}")

    def _telegram(self, message: str, token: str, chat_id: str):
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10,
            )
            log.debug("[Alert] Telegram notification sent")
        except Exception as e:
            log.debug(f"[Alert] Telegram error: {e}")

    def _email(self, finding: dict, domain: str, smtp_cfg: dict):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Shaheen3] {finding.get('severity','').upper()} — {domain}"
            msg["From"]    = smtp_cfg.get("from", "shaheen3@scanner.local")
            msg["To"]      = smtp_cfg.get("to")
            body = MIMEText(
                f"Finding: {finding.get('name','')}\n"
                f"Severity: {finding.get('severity','')}\n"
                f"URL: {finding.get('matched','')}\n"
                f"Domain: {domain}\n\n"
                f"-- Shaheen 3 by Professor Snape", "plain"
            )
            msg.attach(body)
            with smtplib.SMTP(smtp_cfg["host"], smtp_cfg.get("port", 587)) as s:
                s.starttls()
                if smtp_cfg.get("user"):
                    s.login(smtp_cfg["user"], smtp_cfg.get("password", ""))
                s.send_message(msg)
            log.debug("[Alert] Email notification sent")
        except Exception as e:
            log.debug(f"[Alert] Email error: {e}")
