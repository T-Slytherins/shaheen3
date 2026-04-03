#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Shaheen 3 — Setup Script (Kali Linux / Debian / Ubuntu)
#  Crafted by Professor Snape
#  Usage: bash setup.sh
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

step() { echo -e "${GREEN}[+]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }
err()  { echo -e "${RED}[✗]${RESET} $1"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }

echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   SHAHEEN 3 — Setup & Installation    ║"
echo "  ║   Crafted by Professor Snape          ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${RESET}"

# ── Detect OS ─────────────────────────────────────────────────
IS_KALI=false
IS_UBUNTU=false
if grep -qi "kali" /etc/os-release 2>/dev/null; then
    IS_KALI=true
elif grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null; then
    IS_UBUNTU=true
fi

# ── 1. System packages ────────────────────────────────────────
step "Updating package lists..."
sudo apt-get update -qq

step "Installing system dependencies..."
# Base packages (always)
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    nmap whois dnsutils curl wget git unzip \
    2>/dev/null || true

# Browser for screenshots — Kali uses 'chromium', Ubuntu uses 'chromium-browser'
if $IS_KALI; then
    sudo apt-get install -y -qq chromium 2>/dev/null && ok "chromium installed" \
        || warn "chromium install failed — screenshots will use gowitness fallback"
else
    sudo apt-get install -y -qq chromium-browser 2>/dev/null \
        || sudo apt-get install -y -qq chromium 2>/dev/null \
        || warn "chromium not available — screenshots will use gowitness fallback"
fi

ok "System packages done"

# ── 2. Go environment ─────────────────────────────────────────
export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin

if ! command -v go &>/dev/null; then
    step "Installing Go 1.21..."
    GO_VER="1.21.5"
    wget -q "https://go.dev/dl/go${GO_VER}.linux-amd64.tar.gz" -O /tmp/go.tar.gz
    sudo tar -C /usr/local -xzf /tmp/go.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin
    ok "Go ${GO_VER} installed"
else
    ok "Go: $(go version)"
fi

mkdir -p "$HOME/go/bin"
export GOPATH="$HOME/go"
export PATH=$PATH:$GOPATH/bin

# ── 3. Helper: install binary from GitHub releases ────────────
install_binary() {
    local name="$1"
    local release_url="$2"
    local archive_name="$3"
    local binary_in_archive="$4"

    if command -v "$name" &>/dev/null; then
        ok "$name already installed"
        return
    fi

    step "Installing $name from GitHub releases..."
    local tmp_dir
    tmp_dir=$(mktemp -d)

    if wget -q "$release_url" -O "$tmp_dir/$archive_name"; then
        cd "$tmp_dir"
        if [[ "$archive_name" == *.zip ]]; then
            unzip -q "$archive_name"
        else
            tar -xzf "$archive_name"
        fi

        local bin_path
        bin_path=$(find "$tmp_dir" -name "$binary_in_archive" -type f | head -1)
        if [[ -n "$bin_path" ]]; then
            chmod +x "$bin_path"
            sudo mv "$bin_path" /usr/local/bin/"$name"
            ok "$name installed → /usr/local/bin/$name"
        else
            warn "$name binary not found in archive — skip"
        fi
        cd - > /dev/null
    else
        warn "$name download failed — install manually"
    fi
    rm -rf "$tmp_dir"
}

# ── 4. Go-based security tools (binary releases) ──────────────
step "Installing security tools via pre-built binaries..."

ARCH="linux_amd64"

# ── nuclei ──
if ! command -v nuclei &>/dev/null; then
    NUCLEI_VER=$(curl -s https://api.github.com/repos/projectdiscovery/nuclei/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4 | tr -d 'v' 2>/dev/null || echo "3.2.4")
    install_binary "nuclei" \
        "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_${NUCLEI_VER}_${ARCH}.zip" \
        "nuclei_${NUCLEI_VER}_${ARCH}.zip" \
        "nuclei"
else
    ok "nuclei already installed"
fi

# ── subfinder ──
if ! command -v subfinder &>/dev/null; then
    SF_VER=$(curl -s https://api.github.com/repos/projectdiscovery/subfinder/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4 | tr -d 'v' 2>/dev/null || echo "2.6.6")
    install_binary "subfinder" \
        "https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_${SF_VER}_${ARCH}.zip" \
        "subfinder_${SF_VER}_${ARCH}.zip" \
        "subfinder"
else
    ok "subfinder already installed"
fi

# ── httpx ──
if ! command -v httpx &>/dev/null; then
    HTTPX_VER=$(curl -s https://api.github.com/repos/projectdiscovery/httpx/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4 | tr -d 'v' 2>/dev/null || echo "1.6.8")
    install_binary "httpx" \
        "https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_${HTTPX_VER}_${ARCH}.zip" \
        "httpx_${HTTPX_VER}_${ARCH}.zip" \
        "httpx"
else
    ok "httpx already installed"
fi

# ── katana ──
if ! command -v katana &>/dev/null; then
    KAT_VER=$(curl -s https://api.github.com/repos/projectdiscovery/katana/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4 | tr -d 'v' 2>/dev/null || echo "1.1.0")
    install_binary "katana" \
        "https://github.com/projectdiscovery/katana/releases/latest/download/katana_${KAT_VER}_${ARCH}.zip" \
        "katana_${KAT_VER}_${ARCH}.zip" \
        "katana"
else
    ok "katana already installed"
fi

# ── dnsx ──
if ! command -v dnsx &>/dev/null; then
    DNSX_VER=$(curl -s https://api.github.com/repos/projectdiscovery/dnsx/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4 | tr -d 'v' 2>/dev/null || echo "1.2.1")
    install_binary "dnsx" \
        "https://github.com/projectdiscovery/dnsx/releases/latest/download/dnsx_${DNSX_VER}_${ARCH}.zip" \
        "dnsx_${DNSX_VER}_${ARCH}.zip" \
        "dnsx"
else
    ok "dnsx already installed"
fi

# ── assetfinder ──
if ! command -v assetfinder &>/dev/null; then
    install_binary "assetfinder" \
        "https://github.com/tomnomnom/assetfinder/releases/download/v0.1.1/assetfinder-linux-amd64-0.1.1.tgz" \
        "assetfinder-linux-amd64-0.1.1.tgz" \
        "assetfinder"
else
    ok "assetfinder already installed"
fi

# ── gowitness ──
if ! command -v gowitness &>/dev/null; then
    GW_VER=$(curl -s https://api.github.com/repos/sensepost/gowitness/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4 | tr -d 'v' 2>/dev/null || echo "3.0.5")
    install_binary "gowitness" \
        "https://github.com/sensepost/gowitness/releases/latest/download/gowitness-${GW_VER}-linux-amd64" \
        "gowitness-${GW_VER}-linux-amd64" \
        "gowitness-${GW_VER}-linux-amd64"
    # gowitness is a single binary, not an archive — handle separately
    if ! command -v gowitness &>/dev/null; then
        GW_BIN="gowitness-${GW_VER}-linux-amd64"
        wget -q "https://github.com/sensepost/gowitness/releases/latest/download/${GW_BIN}" \
            -O /tmp/gowitness 2>/dev/null && \
            chmod +x /tmp/gowitness && \
            sudo mv /tmp/gowitness /usr/local/bin/gowitness && \
            ok "gowitness installed" || warn "gowitness install failed"
    fi
else
    ok "gowitness already installed"
fi

# ── amass (Kali has it in repos) ──
if ! command -v amass &>/dev/null; then
    step "Installing amass..."
    sudo apt-get install -y -qq amass 2>/dev/null && ok "amass installed" \
        || warn "amass not in repos — skipping (subfinder covers passive recon)"
else
    ok "amass already installed"
fi

# ── 5. Python virtual environment ─────────────────────────────
step "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
ok "venv at: $(pwd)/venv"

step "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Python packages installed"

# ── 6. theHarvester (Kali has it pre-installed) ───────────────
if command -v theHarvester &>/dev/null; then
    ok "theHarvester already installed"
else
    step "Installing theHarvester..."
    if $IS_KALI; then
        sudo apt-get install -y -qq theharvester 2>/dev/null && ok "theHarvester installed" \
            || warn "theHarvester not found — install: sudo apt install theharvester"
    else
        git clone -q https://github.com/laramies/theHarvester /opt/theHarvester 2>/dev/null || true
        if [ -d /opt/theHarvester ]; then
            pip install -q -r /opt/theHarvester/requirements/base.txt
            sudo ln -sf /opt/theHarvester/theHarvester.py /usr/local/bin/theHarvester
            ok "theHarvester installed"
        fi
    fi
fi

# ── 7. Nuclei templates ───────────────────────────────────────
if command -v nuclei &>/dev/null; then
    step "Updating Nuclei templates..."
    nuclei -update-templates -silent 2>/dev/null && ok "Nuclei templates updated" \
        || warn "Nuclei template update skipped (no internet or already fresh)"
fi

# ── 8. Output directories ─────────────────────────────────────
step "Creating output directories..."
mkdir -p output/{reports,screenshots,crawl,nmap,vuln} logs
ok "Output directories created"

# ── 9. Verification ───────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}── Verification ─────────────────────────────${RESET}"

tools=(
    "python3:required"
    "nmap:required"
    "whois:required"
    "subfinder:recommended"
    "nuclei:recommended"
    "katana:optional"
    "assetfinder:optional"
    "gowitness:optional"
    "amass:optional"
    "theHarvester:optional"
)

all_required=true
for entry in "${tools[@]}"; do
    tool="${entry%%:*}"
    level="${entry##*:}"
    if command -v "$tool" &>/dev/null; then
        ok "$tool"
    else
        if [[ "$level" == "required" ]]; then
            err "$tool NOT found — REQUIRED, install manually"
            all_required=false
        elif [[ "$level" == "recommended" ]]; then
            warn "$tool NOT found — recommended (core vuln scan will be limited)"
        else
            warn "$tool NOT found — optional (graceful degradation enabled)"
        fi
    fi
done

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
if $all_required; then
    echo -e "${GREEN}${BOLD}  Shaheen 3 setup complete!${RESET}"
else
    echo -e "${YELLOW}${BOLD}  Shaheen 3 setup done (some required tools missing — see above)${RESET}"
fi
echo ""
echo "  Activate venv   :  source venv/bin/activate"
echo "  Quick scan      :  python3 shaheen3.py -d example.com"
echo "  Full scan       :  python3 shaheen3.py -d example.com --full"
echo "  Fast mode       :  python3 shaheen3.py -d example.com --fast"
echo "  REST API        :  python3 shaheen3.py --api"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
