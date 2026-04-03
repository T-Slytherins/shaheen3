#!/usr/bin/env python3
"""
Shaheen 3 — Professional Dark-Theme HTML Report Generator
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from core.logger import get_logger

log = get_logger("HTMLReport")

SEVERITY_COLOR = {
    "critical": "#ff2d55",
    "high":     "#ff9500",
    "medium":   "#ffcc00",
    "low":      "#34c759",
    "info":     "#5ac8fa",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TMPL_TITLE</title>
  <style>
    /* ── Reset & Base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:       #0a0a0f;
      --bg2:      #111118;
      --bg3:      #1a1a24;
      --border:   #2a2a3a;
      --text:     #e2e8f0;
      --text-dim: #8892a0;
      --accent:   #7c3aed;
      --accent2:  #06b6d4;
      --crit:     #ff2d55;
      --high:     #ff9500;
      --med:      #ffcc00;
      --low:      #34c759;
      --info:     #5ac8fa;
      --font:     'Segoe UI', 'Inter', system-ui, sans-serif;
      --mono:     'Fira Code', 'Cascadia Code', monospace;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg); }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

    /* ── Layout ── */
    .wrapper {{ max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; }}

    /* ── Header ── */
    header {{
      background: linear-gradient(135deg, #0d0d1a 0%, #1a0533 50%, #0d0d1a 100%);
      border-bottom: 1px solid var(--accent);
      padding: 2rem 0;
      position: sticky; top: 0; z-index: 100;
    }}
    .header-inner {{
      display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: 1rem;
    }}
    .logo {{
      font-family: var(--mono);
      font-size: 1.4rem;
      font-weight: 700;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .meta-badge {{
      display: flex; gap: 1rem; flex-wrap: wrap;
    }}
    .badge {{
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.25rem 0.75rem;
      font-size: 0.8rem;
      font-family: var(--mono);
    }}

    /* ── Navigation ── */
    nav {{
      background: var(--bg2);
      border-bottom: 1px solid var(--border);
      padding: 0.75rem 0;
      position: sticky; top: 85px; z-index: 90;
    }}
    .nav-inner {{
      display: flex; gap: 0.5rem; flex-wrap: wrap;
    }}
    nav a {{
      color: var(--text-dim);
      text-decoration: none;
      padding: 0.35rem 0.85rem;
      border-radius: 6px;
      font-size: 0.85rem;
      transition: all 0.2s;
      border: 1px solid transparent;
    }}
    nav a:hover {{
      color: var(--text);
      border-color: var(--border);
      background: var(--bg3);
    }}

    /* ── Risk Score Ring ── */
    .dashboard {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      padding: 2rem 0;
    }}
    .stat-card {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    .stat-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
    }}
    .stat-card.critical::before {{ background: var(--crit); }}
    .stat-card.high::before     {{ background: var(--high); }}
    .stat-card.medium::before   {{ background: var(--med); }}
    .stat-card.low::before      {{ background: var(--low); }}
    .stat-card.info::before     {{ background: var(--info); }}
    .stat-card.neutral::before  {{ background: var(--accent); }}
    .stat-number {{
      font-size: 2.5rem;
      font-weight: 700;
      font-family: var(--mono);
      line-height: 1;
      margin-bottom: 0.5rem;
    }}
    .stat-label {{ font-size: 0.85rem; color: var(--text-dim); }}

    /* ── Sections ── */
    section {{
      padding: 2rem 0;
      border-bottom: 1px solid var(--border);
    }}
    .section-title {{
      font-size: 1.3rem;
      font-weight: 700;
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .section-title .icon {{
      width: 32px; height: 32px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1rem;
    }}

    /* ── Tables ── */
    .table-wrap {{ overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
    th {{
      background: var(--bg3);
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.75rem;
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #1a1a24; vertical-align: top; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(255,255,255,0.02); }}

    /* ── Severity badges ── */
    .sev {{
      display: inline-block;
      padding: 0.15rem 0.6rem;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-family: var(--mono);
    }}
    .sev-critical {{ background: #ff2d5522; color: var(--crit); border: 1px solid var(--crit); }}
    .sev-high     {{ background: #ff950022; color: var(--high); border: 1px solid var(--high); }}
    .sev-medium   {{ background: #ffcc0022; color: var(--med);  border: 1px solid var(--med);  }}
    .sev-low      {{ background: #34c75922; color: var(--low);  border: 1px solid var(--low);  }}
    .sev-info     {{ background: #5ac8fa22; color: var(--info); border: 1px solid var(--info); }}

    /* ── Code blocks ── */
    pre, code {{
      font-family: var(--mono);
      font-size: 0.8rem;
      background: #0d0d14;
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    pre {{ padding: 1rem; overflow-x: auto; }}
    code {{ padding: 0.1rem 0.4rem; }}

    /* ── Collapsible details ── */
    details {{ margin-bottom: 0.5rem; }}
    summary {{
      cursor: pointer;
      padding: 0.75rem 1rem;
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.875rem;
      list-style: none;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: background 0.2s;
    }}
    summary:hover {{ background: #1e1e2e; }}
    details[open] summary {{ border-radius: 8px 8px 0 0; }}
    .details-body {{
      border: 1px solid var(--border);
      border-top: none;
      border-radius: 0 0 8px 8px;
      padding: 1rem;
      background: var(--bg2);
    }}

    /* ── Screenshot gallery ── */
    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }}
    .gallery-card {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, border-color 0.2s;
    }}
    .gallery-card:hover {{
      transform: translateY(-2px);
      border-color: var(--accent);
    }}
    .gallery-card img {{
      width: 100%; height: 160px;
      object-fit: cover;
      display: block;
    }}
    .gallery-card .card-label {{
      padding: 0.5rem 0.75rem;
      font-size: 0.75rem;
      color: var(--text-dim);
      font-family: var(--mono);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    /* ── Modal ── */
    .modal-overlay {{
      display: none;
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.85);
      z-index: 1000;
      align-items: center;
      justify-content: center;
    }}
    .modal-overlay.active {{ display: flex; }}
    .modal-img {{ max-width: 90vw; max-height: 85vh; border-radius: 10px; }}
    .modal-close {{
      position: fixed; top: 1rem; right: 1rem;
      background: var(--bg3); border: 1px solid var(--border);
      color: var(--text); border-radius: 50%;
      width: 40px; height: 40px;
      font-size: 1.2rem; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }}

    /* ── Chain cards ── */
    .chain-card {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      margin-bottom: 1rem;
      border-left: 4px solid var(--crit);
    }}
    .chain-card.high {{ border-left-color: var(--high); }}
    .chain-card.medium {{ border-left-color: var(--med); }}
    .chain-title {{ font-weight: 700; margin-bottom: 0.5rem; }}
    .chain-steps {{ list-style: none; }}
    .chain-steps li {{
      padding: 0.3rem 0 0.3rem 1.5rem;
      position: relative;
      font-size: 0.875rem;
      color: var(--text-dim);
    }}
    .chain-steps li::before {{
      content: "→";
      position: absolute; left: 0;
      color: var(--accent);
    }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 3rem 0;
      color: var(--text-dim);
      font-size: 0.8rem;
      font-family: var(--mono);
    }}

    /* ── Responsive ── */
    @media (max-width: 768px) {{
      .header-inner {{ flex-direction: column; align-items: flex-start; }}
      nav a {{ font-size: 0.75rem; padding: 0.25rem 0.6rem; }}
      .stat-number {{ font-size: 1.8rem; }}
    }}

    /* ── Progress bar ── */
    .risk-bar {{ height: 8px; border-radius: 4px; background: var(--bg3); overflow: hidden; }}
    .risk-fill {{
      height: 100%;
      border-radius: 4px;
      transition: width 1s ease;
    }}
  </style>
</head>
<body>

<!-- Modal overlay -->
<div class="modal-overlay" id="imgModal" onclick="closeModal()">
  <button class="modal-close" onclick="closeModal()">×</button>
  <img class="modal-img" id="modalImg" src="" alt="">
</div>

<!-- Header -->
<header>
  <div class="wrapper header-inner">
    <div>
      <div class="logo">⚡ SHAHEEN 3</div>
      <div style="font-size:0.8rem;color:var(--text-dim);margin-top:0.25rem;">
        Crafted by Professor Snape
      </div>
    </div>
    <div class="meta-badge">
      <span class="badge">🎯 TMPL_DOMAIN</span>
      <span class="badge">📅 TMPL_TIMESTAMP</span>
      <span class="badge">⏱ TMPL_ELAPSED</span>
    </div>
  </div>
</header>

<!-- Navigation -->
<nav>
  <div class="wrapper nav-inner">
    <a href="#dashboard">Dashboard</a>
    <a href="#whois">Whois</a>
    <a href="#subdomains">Subdomains</a>
    <a href="#dns">DNS</a>
    <a href="#certs">Certificates</a>
    <a href="#emails">Emails</a>
    <a href="#ports">Port Scan</a>
    <a href="#http">HTTP Probe</a>
    <a href="#vulnerabilities">Vulnerabilities</a>
    <a href="#web">Web Crawl</a>
    <a href="#waf">WAF</a>
    <a href="#exploits">Exploit Chains</a>
    <a href="#screenshots">Screenshots</a>
  </div>
</nav>

<div class="wrapper">
  <h1 style="font-size:1.6rem;padding:2rem 0 0.5rem;font-weight:800;">TMPL_TITLE</h1>
  <p style="color:var(--text-dim);font-size:0.875rem;padding-bottom:1rem;">
    Full security assessment report for <code>TMPL_DOMAIN</code>
  </p>

  <!-- Dashboard -->
  <section id="dashboard">
    <div class="section-title"><span class="icon">📊</span> Risk Dashboard</div>

    <!-- Risk score bar -->
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
        <span style="font-weight:700;">Overall Risk Score</span>
        <span style="font-family:var(--mono);font-size:1.5rem;font-weight:800;color:TMPL_RISK_COLOR;">
          TMPL_RISK_SCORE/100
        </span>
      </div>
      <div class="risk-bar">
        <div class="risk-fill" style="width:TMPL_RISK_SCORE%;background:TMPL_RISK_COLOR;"></div>
      </div>
      <div style="margin-top:0.75rem;font-size:0.85rem;color:var(--text-dim);">TMPL_RISK_LABEL</div>
    </div>

    <div class="dashboard">
      TMPL_STAT_CARDS
    </div>
  </section>

  <!-- Whois -->
  <section id="whois">
    <div class="section-title"><span class="icon">🌐</span> Whois & Registration</div>
    TMPL_WHOIS
  </section>

  <!-- Subdomains -->
  <section id="subdomains">
    <div class="section-title"><span class="icon">🔍</span> Subdomain Enumeration</div>
    TMPL_SUBDOMAINS
  </section>

  <!-- DNS -->
  <section id="dns">
    <div class="section-title"><span class="icon">📡</span> DNS Records</div>
    TMPL_DNS
  </section>

  <!-- Certificates -->
  <section id="certs">
    <div class="section-title"><span class="icon">🔒</span> Certificate Intelligence</div>
    TMPL_CERTS
  </section>

  <!-- Emails -->
  <section id="emails">
    <div class="section-title"><span class="icon">📧</span> Email Harvest & Breach Data</div>
    TMPL_EMAILS
  </section>

  <!-- Port Scan -->
  <section id="ports">
    <div class="section-title"><span class="icon">🔌</span> Port Scan Results</div>
    TMPL_NMAP
  </section>

  <!-- HTTP Probe -->
  <section id="http">
    <div class="section-title"><span class="icon">🌍</span> HTTP Probe & Fingerprinting</div>
    TMPL_HTTP
  </section>

  <!-- Vulnerabilities -->
  <section id="vulnerabilities">
    <div class="section-title"><span class="icon">🚨</span> Vulnerability Findings</div>
    TMPL_VULN
  </section>

  <!-- Web Crawl -->
  <section id="web">
    <div class="section-title"><span class="icon">🕷️</span> Web Crawl Results</div>
    TMPL_WEB
  </section>

  <!-- WAF -->
  <section id="waf">
    <div class="section-title"><span class="icon">🛡️</span> WAF Detection & Bypass</div>
    TMPL_WAF
  </section>

  <!-- Exploit Chains -->
  <section id="exploits">
    <div class="section-title"><span class="icon">⛓️</span> Exploit Chains & Lateral Movement</div>
    TMPL_EXPLOIT
  </section>

  <!-- Screenshots -->
  <section id="screenshots">
    <div class="section-title"><span class="icon">📸</span> Screenshots</div>
    TMPL_SCREENSHOTS
  </section>

</div>

<footer>
  <p>Generated by <strong>Shaheen 3 v1.0</strong> — Crafted by Professor Snape</p>
  <p style="margin-top:0.5rem;">⚠️ This report is confidential. For authorized penetration testing use only.</p>
</footer>

<script>
  // Image modal
  function openModal(src) {
    document.getElementById('modalImg').src = src;
    document.getElementById('imgModal').classList.add('active');
  }
  function closeModal() {
    document.getElementById('imgModal').classList.remove('active');
  }
  document.addEventListener('keydown', e => { if(e.key === 'Escape') closeModal(); });

  // Animate risk bar on load
  window.addEventListener('load', () => {
    document.querySelectorAll('.risk-fill').forEach(el => {
      const w = el.style.width;
      el.style.width = '0%';
      setTimeout(() => el.style.width = w, 300);
    });
  });

  // Active nav highlight
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('nav a');
  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(s => {
      if (window.scrollY >= s.offsetTop - 200) current = s.id;
    });
    navLinks.forEach(a => {
      a.style.color = a.getAttribute('href') === '#' + current
        ? 'var(--accent2)' : '';
    });
  });
</script>
</body>
</html>
"""


class HTMLReportGenerator:
    def __init__(self, cfg, out_dir: Path):
        self.cfg     = cfg
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, domain: str, results: dict, title: str = "") -> Path:
        meta = results.get("meta", {})
        ts   = meta.get("timestamp", datetime.now(timezone.utc).isoformat())
        el   = meta.get("elapsed", "—")

        # risk score
        risk_score = results.get("vuln", {}).get("risk_score", 0)
        risk_color, risk_label = self._risk_label(risk_score)

        replacements = {
            "TMPL_TITLE":       title or f"Shaheen 3 — {domain}",
            "TMPL_DOMAIN":      domain,
            "TMPL_TIMESTAMP":   ts[:19].replace("T", " ") + " UTC",
            "TMPL_ELAPSED":     el,
            "TMPL_RISK_SCORE":  str(risk_score),
            "TMPL_RISK_COLOR":  risk_color,
            "TMPL_RISK_LABEL":  risk_label,
            "TMPL_STAT_CARDS":  self._stat_cards(results),
            "TMPL_WHOIS":       self._render_whois(results),
            "TMPL_SUBDOMAINS":  self._render_subdomains(results),
            "TMPL_DNS":         self._render_dns(results),
            "TMPL_CERTS":       self._render_certs(results),
            "TMPL_EMAILS":      self._render_emails(results),
            "TMPL_NMAP":        self._render_nmap(results),
            "TMPL_HTTP":        self._render_http(results),
            "TMPL_VULN":        self._render_vuln(results),
            "TMPL_WEB":         self._render_web(results),
            "TMPL_WAF":         self._render_waf(results),
            "TMPL_EXPLOIT":     self._render_exploits(results),
            "TMPL_SCREENSHOTS": self._render_screenshots(results),
        }
        html = HTML_TEMPLATE
        for token, value in replacements.items():
            html = html.replace(token, str(value))

        safe   = domain.replace(".", "_")
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path   = self.out_dir / f"shaheen3_{safe}_{ts_str}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        log.info(f"[Report] Written: {path}")
        return path

    # ── helpers ───────────────────────────────────────────────────
    def _risk_label(self, score: int):
        if score >= 70: return "#ff2d55", "🔴 CRITICAL RISK — Immediate action required"
        if score >= 40: return "#ff9500", "🟠 HIGH RISK — Urgent remediation needed"
        if score >= 20: return "#ffcc00", "🟡 MEDIUM RISK — Schedule remediation"
        if score > 0:   return "#34c759", "🟢 LOW RISK — Minor issues found"
        return "#5ac8fa", "🔵 INFORMATIONAL — Clean or not fully scanned"

    def _stat_cards(self, results: dict) -> str:
        recon   = results.get("recon", {})
        subs    = recon.get("subdomains", {})
        vuln    = results.get("vuln", {})
        summary = vuln.get("summary", {})
        emails  = recon.get("emails", {}).get("count", 0)

        cards = [
            ("critical", "🔴", summary.get("critical", 0), "Critical Vulns"),
            ("high",     "🟠", summary.get("high", 0),     "High Vulns"),
            ("medium",   "🟡", summary.get("medium", 0),   "Medium Vulns"),
            ("neutral",  "🔍", len(subs.get("all", [])),   "Subdomains"),
            ("neutral",  "📧", emails,                      "Emails Found"),
            ("neutral",  "🌐", len(results.get("scan", {}).get("live_hosts", [])), "Live Hosts"),
        ]

        html = ""
        for cls, icon, num, label in cards:
            html += f"""
            <div class="stat-card {cls}">
              <div style="font-size:1.5rem;margin-bottom:0.25rem;">{icon}</div>
              <div class="stat-number" style="color:var(--{cls if cls != 'neutral' else 'accent2'});">{num}</div>
              <div class="stat-label">{label}</div>
            </div>"""
        return html

    def _table(self, headers: list, rows: list) -> str:
        if not rows:
            return '<p style="color:var(--text-dim);font-size:0.875rem;">No data found.</p>'
        ths = "".join(f"<th>{h}</th>" for h in headers)
        trs = ""
        for row in rows:
            tds = "".join(f"<td>{c}</td>" for c in row)
            trs += f"<tr>{tds}</tr>"
        return f'<div class="table-wrap"><table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'

    def _sev_badge(self, sev: str) -> str:
        s = sev.lower()
        return f'<span class="sev sev-{s}">{s}</span>'

    def _render_whois(self, results: dict) -> str:
        w = results.get("recon", {}).get("whois", {})
        if not w:
            return "<p style='color:var(--text-dim)'>No Whois data.</p>"
        parsed = w.get("parsed", {})
        rows = []
        for field, values in parsed.items():
            v = ", ".join(values) if isinstance(values, list) else str(values)
            rows.append([field.replace("_"," ").title(), v or "—"])
        return self._table(["Field","Value"], rows)

    def _render_subdomains(self, results: dict) -> str:
        subs  = results.get("recon", {}).get("subdomains", {})
        alive = subs.get("alive", [])
        all_s = subs.get("all", [])
        srcs  = subs.get("sources", {})

        html  = f"<p style='margin-bottom:1rem;color:var(--text-dim);'>"
        html += f"Total: <strong>{len(all_s)}</strong> unique subdomains found. "
        html += f"<strong>{len(alive)}</strong> resolved.</p>"

        # Source breakdown
        if srcs:
            html += "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;'>"
            for src, found in srcs.items():
                html += f'<span class="badge">{src}: {len(found)}</span>'
            html += "</div>"

        if alive:
            rows = [[h.get("subdomain",""), h.get("ip","—")] for h in alive]
            html += self._table(["Subdomain","IP Address"], rows)
        return html

    def _render_dns(self, results: dict) -> str:
        dns = results.get("recon", {}).get("dns", {})
        records = dns.get("records", {})
        if not records:
            return "<p style='color:var(--text-dim)'>No DNS data.</p>"
        html = ""
        for rtype, values in records.items():
            if values:
                html += f"<details><summary>📌 {rtype} Records ({len(values)})</summary>"
                html += f'<div class="details-body"><pre>{chr(10).join(str(v) for v in values)}</pre></div></details>'
        zt = dns.get("zone_transfers", [])
        if zt:
            html += '<div style="background:#ff2d5511;border:1px solid var(--crit);border-radius:8px;padding:1rem;margin-top:1rem;">'
            html += '🚨 <strong>Zone Transfer Vulnerability Detected!</strong><br>'
            for z in zt:
                html += f'<code>{z["ns"]}</code> leaked {len(z["records"])} records<br>'
            html += '</div>'
        return html or "<p style='color:var(--text-dim)'>No DNS records found.</p>"

    def _render_certs(self, results: dict) -> str:
        certs = results.get("recon", {}).get("certs", {})
        crtsh = certs.get("crtsh", [])
        live  = certs.get("live_cert", {})
        html  = ""
        if live:
            html += '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1rem;">'
            html += f'<strong>Live Certificate:</strong><br>'
            html += f'Subject: <code>{live.get("subject",{})}</code><br>'
            html += f'Issuer: <code>{live.get("issuer",{})}</code><br>'
            html += f'Valid: <code>{live.get("not_before","")} — {live.get("not_after","")}</code><br>'
            html += f'Protocol: <code>{live.get("protocol","")}</code><br>'
            san = live.get("san", [])
            if san:
                html += f'SAN ({len(san)}): <code>{", ".join(san[:10])}</code>'
            html += '</div>'
        if crtsh:
            rows = [[c.get("common_name",""), c.get("not_before","")[:10],
                     c.get("not_after","")[:10], c.get("issuer","")[:50]]
                    for c in crtsh[:50]]
            html += self._table(["Common Name","Valid From","Valid To","Issuer"], rows)
        return html or "<p style='color:var(--text-dim)'>No certificate data.</p>"

    def _render_emails(self, results: dict) -> str:
        recon    = results.get("recon", {})
        emails   = recon.get("emails", {}).get("emails", [])
        breaches = recon.get("breaches", {}).get("domain_check", [])
        html = ""
        if emails:
            rows = [[f"<code>{e}</code>"] for e in emails]
            html += self._table(["Email Address"], rows)
        if breaches:
            html += '<div style="margin-top:1rem;">'
            html += f'<h3 style="margin-bottom:0.75rem;color:var(--crit);">⚠️ {len(breaches)} Breach(es) Found</h3>'
            rows = [[b.get("name",""), b.get("breach_date",""), f'{b.get("pwn_count",0):,}',
                     ", ".join(b.get("data_classes",[])[:4])] for b in breaches]
            html += self._table(["Breach","Date","Records","Data Types"], rows)
            html += "</div>"
        return html or "<p style='color:var(--text-dim)'>No emails found.</p>"

    def _render_nmap(self, results: dict) -> str:
        nmap_data = results.get("scan", {}).get("nmap", {})
        if not nmap_data:
            return "<p style='color:var(--text-dim)'>No Nmap data.</p>"
        html = ""
        for target, data in nmap_data.items():
            for host in data.get("hosts", []):
                ports = host.get("ports", [])
                html += f"<details><summary>🖥️ {host.get('ip',target)} — {host.get('os','Unknown OS')} — {len(ports)} open ports</summary>"
                html += '<div class="details-body">'
                if ports:
                    rows = [[p.get("port",""), p.get("protocol",""), p.get("service",""),
                             f'{p.get("product","")} {p.get("version","")}'.strip()]
                            for p in ports]
                    html += self._table(["Port","Protocol","Service","Version"], rows)
                html += "</div></details>"
        return html or "<p style='color:var(--text-dim)'>No open ports found.</p>"

    def _render_http(self, results: dict) -> str:
        info = results.get("scan", {}).get("http_info", {})
        if not info:
            return "<p style='color:var(--text-dim)'>No HTTP probe data.</p>"
        html = ""
        for url, d in list(info.items())[:30]:
            techs = ", ".join(d.get("technologies", [])) or "—"
            html += f"<details><summary>🌐 {url} — {d.get('status','')} — {d.get('title','')[:60]}</summary>"
            html += '<div class="details-body">'
            html += f"<p><strong>Server:</strong> {d.get('server','—')}</p>"
            html += f"<p><strong>Technologies:</strong> {techs}</p>"
            sec = d.get("security_headers", {})
            if sec:
                sec_rows = [[h, '<code style="color:var(--crit)">MISSING</code>'
                             if v == "MISSING" else f"<code>{v[:60]}</code>"]
                            for h, v in sec.items()]
                html += self._table(["Security Header","Value"], sec_rows)
            html += "</div></details>"
        return html or "<p style='color:var(--text-dim)'>No live HTTP hosts.</p>"

    def _render_vuln(self, results: dict) -> str:
        vuln    = results.get("vuln", {})
        all_v   = vuln.get("all", [])
        summary = vuln.get("summary", {})
        if not all_v:
            return "<p style='color:var(--text-dim)'>No vulnerabilities found.</p>"

        # Summary cards
        html = "<div style='display:flex;flex-wrap:wrap;gap:0.75rem;margin-bottom:1.5rem;'>"
        for sev, count in summary.items():
            if count:
                col = SEVERITY_COLOR.get(sev, "#888")
                html += f'<div style="background:{col}22;border:1px solid {col};border-radius:8px;padding:0.75rem 1.25rem;text-align:center;">'
                html += f'<div style="font-size:1.5rem;font-weight:800;color:{col};">{count}</div>'
                html += f'<div style="font-size:0.75rem;text-transform:uppercase;">{sev}</div></div>'
        html += "</div>"

        # Sorted by severity
        order = {"critical":0,"high":1,"medium":2,"low":3,"info":4}
        sorted_v = sorted(all_v, key=lambda x: order.get(x.get("severity","info").lower(), 5))

        rows = [
            [self._sev_badge(v.get("severity","info")),
             v.get("name",""),
             f'<code>{v.get("matched","")[:60]}</code>',
             ", ".join(v.get("cve",[]))[:40] or "—"]
            for v in sorted_v
        ]
        html += self._table(["Severity","Finding","Matched URL","CVE"], rows)
        return html

    def _render_web(self, results: dict) -> str:
        web = results.get("web", {})
        crawl = web.get("crawl", {})
        js    = web.get("js_urls", [])
        if not crawl and not js:
            return "<p style='color:var(--text-dim)'>No crawl data.</p>"
        html = ""
        for url, data in list(crawl.items())[:10]:
            total = data.get("total", 0)
            apis  = data.get("apis", [])
            html += f"<details><summary>🕷️ {url} — {total} URLs found, {len(apis)} API endpoints</summary>"
            html += '<div class="details-body">'
            if apis:
                html += "<strong>API Endpoints:</strong>"
                html += "<ul style='margin:0.5rem 0 1rem 1rem;font-family:var(--mono);font-size:0.8rem;'>"
                for a in apis[:20]:
                    html += f"<li>{a}</li>"
                html += "</ul>"
            forms = data.get("forms", [])
            if forms:
                rows = [[f.get("action",""), f.get("method",""), ", ".join(f.get("inputs",[]))] for f in forms]
                html += self._table(["Form Action","Method","Input Fields"], rows)
            html += "</div></details>"
        if js:
            html += f"<details><summary>📜 JavaScript Files ({len(js)})</summary>"
            html += '<div class="details-body"><ul style="font-family:var(--mono);font-size:0.8rem;line-height:2;">'
            for j in js[:50]:
                html += f'<li><a href="{j}" target="_blank" style="color:var(--accent2);">{j}</a></li>'
            html += "</ul></div></details>"
        return html

    def _render_waf(self, results: dict) -> str:
        evasion = results.get("evasion", {})
        if not evasion:
            return "<p style='color:var(--text-dim)'>WAF evasion module not run.</p>"
        detected = evasion.get("waf_detected", {})
        html = ""
        if detected:
            html += '<div style="background:#ff950011;border:1px solid var(--high);border-radius:8px;padding:1rem;margin-bottom:1rem;">'
            html += f'🛡️ <strong>WAF Detected:</strong> {", ".join(detected.keys())}'
            html += '</div>'
        else:
            html += '<div style="background:#34c75911;border:1px solid var(--low);border-radius:8px;padding:1rem;margin-bottom:1rem;">✅ No WAF detected</div>'

        bypass = evasion.get("bypass_results", {})
        for cat, tests in bypass.items():
            bypassed = [t for t in tests if t.get("bypassed")]
            html += f"<details><summary>🔓 {cat.upper()} bypass — {len(bypassed)}/{len(tests)} bypassed</summary>"
            html += '<div class="details-body">'
            if bypassed:
                rows = [[t.get("payload","")[:50], t.get("method",""), t.get("status","")] for t in bypassed]
                html += self._table(["Payload","Encoding","Status"], rows)
            html += "</div></details>"
        return html

    def _render_exploits(self, results: dict) -> str:
        exploit = results.get("exploit", {})
        chains  = exploit.get("chains", [])
        lateral = exploit.get("lateral_movement", {})
        escalation = exploit.get("risk_escalation", "")
        if not chains and not lateral:
            return "<p style='color:var(--text-dim)'>Exploit chaining module not run.</p>"
        html = ""
        if escalation:
            html += f'<div style="background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1rem;font-weight:700;">{escalation}</div>'
        for chain in chains:
            sev = chain.get("severity","medium")
            html += f'<div class="chain-card {sev}">'
            html += f'<div class="chain-title">{chain.get("name","")}</div>'
            html += f'{self._sev_badge(sev)}<br><br>'
            html += '<ol class="chain-steps">'
            for step in chain.get("steps",[]):
                html += f"<li>{step}</li>"
            html += "</ol></div>"
        if lateral:
            html += f"<details><summary>🗺️ Lateral Movement Map</summary>"
            html += '<div class="details-body">'
            svc = lateral.get("internal_services", [])
            if svc:
                rows = [[s.get("host",""), s.get("port",""), s.get("service","")] for s in svc]
                html += self._table(["Host","Port","Service"], rows)
            for pivot in lateral.get("pivot_paths", []):
                html += f'<p style="margin:0.5rem 0;"><strong>{pivot["from"]}</strong> → <strong>{pivot["to"]}</strong> via <code>{pivot["via"]}</code> <span class="sev sev-{pivot["risk"]}">{pivot["risk"]}</span></p>'
            html += "</div></details>"
        return html

    def _render_screenshots(self, results: dict) -> str:
        shots = results.get("web", {}).get("screenshots", {})
        if not shots:
            return "<p style='color:var(--text-dim)'>No screenshots captured. Run with --screenshots flag.</p>"
        html = '<div class="gallery">'
        for url, path in shots.items():
            html += f"""
            <div class="gallery-card" onclick="openModal('{path}')">
              <img src="{path}" alt="{url}" onerror="this.parentElement.style.display='none'">
              <div class="card-label">{url}</div>
            </div>"""
        html += "</div>"
        return html
