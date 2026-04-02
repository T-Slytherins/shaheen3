#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Shaheen 3 — One-Shot Setup Script
#  Crafted by Professor Snape
#  Usage: bash setup.sh
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

banner() {
  echo -e "${CYAN}${BOLD}"
  echo "  ╔═══════════════════════════════════════╗"
  echo "  ║   SHAHEEN 3 — Setup & Installation    ║"
  echo "  ║   Crafted by Professor Snape          ║"
  echo "  ╚═══════════════════════════════════════╝"
  echo -e "${RESET}"
}

step() { echo -e "${GREEN}[+]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }
err()  { echo -e "${RED}[✗]${RESET} $1"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }

install_go_tool() {
  local name=$1; local url=$2
  if command -v "$name" &>/dev/null; then
    ok "$name already installed"
  else
    step "Installing $name..."
    go install "$url" 2>/dev/null && ok "$name installed" || warn "$name install failed (install manually)"
  fi
}

banner

# ── 1. System packages ────────────────────────────────────────
step "Updating package lists..."
sudo apt-get update -qq

step "Installing system dependencies..."
sudo apt-get install -y -qq \
  python3 python3-pip python3-venv \
  nmap whois dnsutils curl wget git \
  chromium-browser || \
sudo apt-get install -y -qq \
  python3 python3-pip python3-venv \
  nmap whois dnsutils curl wget git \
  chromium 2>/dev/null || true

ok "System packages installed"

# ── 2. Go language (required for modern tools) ────────────────
if ! command -v go &>/dev/null; then
  step "Installing Go..."
  GO_VERSION="1.21.5"
  wget -q "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -O /tmp/go.tar.gz
  sudo tar -C /usr/local -xzf /tmp/go.tar.gz
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc
  export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin
  ok "Go ${GO_VERSION} installed"
else
  ok "Go already installed: $(go version)"
fi

export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin

# ── 3. Go-based security tools ────────────────────────────────
step "Installing Go-based security tools..."
install_go_tool "subfinder"    "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
install_go_tool "nuclei"       "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
install_go_tool "httpx"        "github.com/projectdiscovery/httpx/cmd/httpx@latest"
install_go_tool "katana"       "github.com/projectdiscovery/katana/cmd/katana@latest"
install_go_tool "dnsx"         "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"
install_go_tool "assetfinder"  "github.com/tomnomnom/assetfinder@latest"
install_go_tool "gowitness"    "github.com/sensepost/gowitness@latest"
install_go_tool "amass"        "github.com/owasp-amass/amass/v4/...@master"

# ── 4. Python virtual environment ─────────────────────────────
step "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
ok "Virtual environment created at: $(pwd)/venv"

step "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Python packages installed"

# ── 5. theHarvester ───────────────────────────────────────────
if ! command -v theHarvester &>/dev/null; then
  step "Installing theHarvester..."
  git clone -q https://github.com/laramies/theHarvester /opt/theHarvester 2>/dev/null || true
  if [ -d /opt/theHarvester ]; then
    cd /opt/theHarvester
    pip install -q -r requirements/base.txt
    sudo ln -sf /opt/theHarvester/theHarvester.py /usr/local/bin/theHarvester
    cd - > /dev/null
    ok "theHarvester installed"
  else
    warn "theHarvester install failed — install manually"
  fi
else
  ok "theHarvester already installed"
fi

# ── 6. Nuclei templates ───────────────────────────────────────
step "Updating Nuclei templates..."
nuclei -update-templates -silent 2>/dev/null && ok "Nuclei templates updated" || warn "Nuclei template update failed"

# ── 7. Output directories ─────────────────────────────────────
step "Creating output directories..."
mkdir -p output/{reports,screenshots,crawl,nmap,vuln} logs
ok "Output directories created"

# ── 8. Verify installation ────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}── Verification ─────────────────────────────${RESET}"
tools=("python3" "nmap" "whois" "subfinder" "nuclei" "katana" "assetfinder" "gowitness")
all_ok=true
for tool in "${tools[@]}"; do
  if command -v "$tool" &>/dev/null; then
    ok "$tool"
  else
    warn "$tool NOT found (optional — graceful degradation enabled)"
    all_ok=false
  fi
done

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  Shaheen 3 setup complete!${RESET}"
echo ""
echo "  Activate environment:  source venv/bin/activate"
echo "  Run a scan:            python3 shaheen3.py -d example.com"
echo "  Full scan:             python3 shaheen3.py -d example.com --full"
echo "  Start REST API:        python3 shaheen3.py --api"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
