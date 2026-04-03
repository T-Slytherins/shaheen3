<!-- Shaheen 3 README — Professor Snape -->

<div align="center">

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                      ║
║                     ███████╗██╗  ██╗ █████╗ ██╗  ██╗███████╗███████╗███╗   ██╗    ██████╗                            ║
║                     ██╔════╝██║  ██║██╔══██╗██║  ██║██╔════╝██╔════╝████╗  ██║         ██                            ║
║                     ███████╗███████║███████║███████║█████╗  █████╗  ██╔██╗ ██║     █████╝                            ║
║                     ╚════██║██╔══██║██╔══██║██╔══██║██╔══╝  ██╔══╝  ██║╚██╗██║         ██                            ║
║                     ███████║██║  ██║██║  ██║██║  ██║███████╗███████╗██║ ╚████║    ██████╝                            ║
║                    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝                                        ║
║                                                                                                                      ║
║                                     Shaheen 3 – Elite Penetration Testing & OSINT Suite                              ║
║                                                                                                                      ║
║             Advanced Red Teaming • OSINT Automation • Reconnaissance • Intelligence Correlation Engine               ║
║                                                                                                                      ║
║                                 Engineered by Pr0fessor SnApe  |  Version 1.0.0                                      ║
║                                                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

# ⚡ SHAHEEN 3

**Elite Penetration Testing & OSINT Suite**  
*Crafted by Professor Snape*

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)](https://github.com)
[![Version](https://img.shields.io/badge/Version-1.0-purple)](https://github.com)

> ⚠️ **For authorized penetration testing and security research ONLY.**  
> Unauthorized use is illegal. You are responsible for how you use this tool.

</div>

---

## 🚀 Features

| Module | Capabilities |
|--------|-------------|
| 🔍 **Recon** | Whois, passive DNS, certificate transparency, breach data |
| 🌐 **Subdomains** | Amass, Subfinder, Assetfinder, crt.sh, DNS brute-force |
| 📡 **DNS** | Full record enumeration, zone transfer detection, DNSSEC |
| 🔌 **Port Scan** | Nmap full-port scan, service detection, OS fingerprinting |
| 🌍 **HTTP Probe** | Live host detection, tech fingerprinting, security headers |
| 📧 **Email** | theHarvester, Hunter.io, breach correlation |
| 🚨 **Vuln Scan** | Nuclei with 11 elite custom templates + severity scoring |
| 🕷️ **Web Crawl** | Katana + Python crawler, JS URL extraction, form mapping |
| 📸 **Screenshots** | Gowitness / Aquatone / Chromium headless |
| 🛡️ **WAF Bypass** | Detection + encoding evasion techniques |
| ⛓️ **Exploit Chain** | Automated chain analysis + lateral movement mapping |
| 📊 **Reports** | Professional dark-theme HTML reports, JSON snapshots |
| 🔌 **REST API** | Flask-based API for integration with other tools |
| ⏰ **Scheduler** | Daily/weekly automated scanning |

---

## 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/T-Slytherins/shaheen3.git
cd shaheen3

# 2. Run the automated setup (installs all tools + Python env)
bash setup.sh

# 3. Activate virtual environment
source venv/bin/activate
```

### Manual install (Python only)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚡ Quick Start

```bash
# Basic recon scan
python3 shaheen3.py -d example.com

# Full assessment (all modules)
python3 shaheen3.py -d example.com --full

# Specific modules only
python3 shaheen3.py -d example.com --modules recon,scan,vuln

# With proxy (Burp Suite)
python3 shaheen3.py -d example.com --proxy http://127.0.0.1:8080

# Enable WAF bypass + screenshots
python3 shaheen3.py -d example.com --waf-bypass --screenshots

# Scan multiple domains from file
python3 shaheen3.py -l domains.txt --full

# Start REST API server
python3 shaheen3.py --api --api-port 5000

# Schedule daily scans at 09:00
python3 shaheen3.py -d example.com --schedule daily 09:00
```

---

## 🗂️ Project Structure

```
shaheen3/
├── shaheen3.py              # Main entry point & orchestrator
├── setup.sh                 # One-shot setup script
├── requirements.txt         # Python dependencies
│
├── core/
│   ├── banner.py            # ASCII banner
│   ├── config.py            # Central configuration manager
│   ├── logger.py            # Unified logging (console + file)
│   ├── scheduler.py         # Task scheduling (daily/weekly)
│   └── api.py               # Flask REST API server
│
├── modules/
│   ├── recon/
│   │   ├── whois_lookup.py  # Whois & registration data
│   │   ├── subdomain_enum.py# Multi-source subdomain enumeration
│   │   ├── dns_enum.py      # Full DNS + zone transfer
│   │   ├── certificate_scan.py # CT log scanning
│   │   ├── email_harvest.py # Email harvesting
│   │   └── breach_data.py   # Breach data lookup
│   ├── scanning/
│   │   ├── nmap_scan.py     # Nmap port scanning
│   │   └── http_probe.py    # HTTP probing & fingerprinting
│   ├── vuln/
│   │   └── nuclei_scan.py   # Nuclei vulnerability scanning
│   ├── web/
│   │   ├── crawler.py       # Web + JS crawler
│   │   └── screenshot.py    # Full-page screenshots
│   ├── evasion/
│   │   └── waf_bypass.py    # WAF detection & bypass
│   └── exploit/
│       └── chain.py         # Exploit chaining & lateral movement
│
├── reports/
│   └── html_report.py       # Dark-theme HTML report generator
│
├── nuclei_templates/        # 11 elite custom Nuclei templates
│   ├── xss-reflected.yaml
│   ├── sqli-error-based.yaml
│   ├── ssrf-detection.yaml
│   ├── open-redirect.yaml
│   ├── cors-misconfiguration.yaml
│   ├── jwt-vulnerabilities.yaml
│   ├── lfi-detection.yaml
│   ├── sensitive-files.yaml
│   ├── api-key-exposure.yaml
│   ├── admin-panel.yaml
│   └── security-headers.yaml
│
├── output/                  # Scan outputs (gitignored)
│   ├── reports/             # HTML reports
│   ├── screenshots/         # Captured screenshots
│   ├── crawl/               # Crawled URLs
│   ├── nmap/                # Nmap XML results
│   └── vuln/                # Nuclei findings
│
└── logs/                    # Log files (gitignored)
```

---

## 🔌 REST API

```bash
# Start API server
python3 shaheen3.py --api --api-port 5000

# Trigger a scan
curl -X POST http://localhost:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "modules": "recon,scan,vuln"}'

# Get results
curl http://localhost:5000/results?domain=example.com

# Status
curl http://localhost:5000/status
```

---

## 🎛️ All Options

```
  -d, --domain          Target domain
  -l, --list            File with list of domains
  -o, --output          Output directory (default: output)

  --full                Run ALL modules
  --modules             Comma-separated: recon,scan,vuln,web,exploit,evasion

  --ports               Port range (default: 1-65535)
  --fast                Fast scan (top 1000 ports)
  --nuclei-severity     critical,high,medium,low,info
  --exploit-chain       Enable automated exploit chaining
  --waf-bypass          Enable WAF evasion techniques
  --screenshots         Capture full-page screenshots

  --proxy               HTTP proxy (e.g. http://127.0.0.1:8080)
  --rate                Requests per second (default: 150)
  --threads             Parallel threads (default: 10)
  --timeout             Timeout in seconds (default: 10)

  --api                 Launch REST API server
  --api-port            API port (default: 5000)
  --schedule FREQ TIME  Schedule: daily|weekly + HH:MM

  --config              Custom config JSON file
  --creds               Credentials JSON file
  --silent              Suppress banner
  --version             Show version
```

---

## 🧩 Custom Nuclei Templates

Shaheen 3 ships with **11 elite templates** covering OWASP Top 10:

| Template | Severity | Coverage |
|----------|----------|----------|
| `xss-reflected` | High | Reflected XSS via URL params |
| `sqli-error-based` | Critical | SQL error-based injection |
| `ssrf-detection` | Critical | SSRF + cloud metadata |
| `open-redirect` | Medium | Open redirect detection |
| `cors-misconfiguration` | High | CORS policy bypass |
| `jwt-vulnerabilities` | Critical | None algorithm + weak secrets |
| `lfi-detection` | High | Local file inclusion |
| `sensitive-files` | High | .env, .git, backups exposed |
| `api-key-exposure` | Critical | AWS/GitHub/Stripe keys in JS |
| `admin-panel` | Medium | Admin panel discovery |
| `security-headers` | Low | Missing security headers |

---

## 📊 Report Sample

Reports are generated as **dark-theme HTML** files with:
- 📈 Risk score dashboard with severity breakdown
- 🗺️ Interactive exploit chain visualization
- 📸 Screenshot gallery (lightbox)
- 🔍 Collapsible scan sections
- 📱 Mobile-responsive design

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/new-module`
3. Commit your changes: `git commit -m "feat: add new module"`
4. Push and open a PR

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ⚡ by <strong>Professor Snape</strong> | Shaheen 3 v1.0
</div>
