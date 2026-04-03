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
grep -qi "kali" /etc/os-release 2>/dev/null && IS_KALI=true

# ── 1. System packages ────────────────────────────────────────
step "Updating package lists..."
sudo apt-get update -qq

step "Installing system dependencies..."
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    nmap whois dnsutils curl wget git unzip tar \
    2>/dev/null || true

# Browser — Kali uses 'chromium', Ubuntu uses 'chromium-browser'
sudo apt-get install -y -qq chromium 2>/dev/null \
    || sudo apt-get install -y -qq chromium-browser 2>/dev/null \
    || warn "No chromium found — screenshots fall back to gowitness"

ok "System packages done"

# ── 2. Go path ────────────────────────────────────────────────
export GOPATH="$HOME/go"
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin
mkdir -p "$GOPATH/bin"

if command -v go &>/dev/null; then
    ok "Go: $(go version)"
else
    warn "Go not found — install from https://go.dev/dl/"
fi

# ── 3. ProjectDiscovery tools — apt repo (most reliable) ──────
step "Adding ProjectDiscovery apt repository..."
if ! grep -q "packages.projectdiscovery.io" /etc/apt/sources.list.d/*.list 2>/dev/null; then
    curl -fsSL https://packages.projectdiscovery.io/linux/main/dists/Release.gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/projectdiscovery-archive-keyring.gpg 2>/dev/null \
        && echo "deb [signed-by=/usr/share/keyrings/projectdiscovery-archive-keyring.gpg] \
https://packages.projectdiscovery.io/linux/main stable main" \
        | sudo tee /etc/apt/sources.list.d/projectdiscovery.list > /dev/null \
        && sudo apt-get update -qq 2>/dev/null \
        && ok "ProjectDiscovery repo added" \
        || warn "PD repo setup failed — will use direct binary download"
fi

# Try apt install for PD tools first
for tool in nuclei subfinder httpx katana dnsx; do
    if command -v "$tool" &>/dev/null; then
        ok "$tool already installed"
    else
        sudo apt-get install -y -qq "$tool" 2>/dev/null \
            && ok "$tool installed via apt" \
            || true   # fallback handled below
    fi
done

# ── 4. Direct binary download fallback ────────────────────────
# Hardcoded stable versions — updated April 2025
NUCLEI_VER="3.3.2"
SUBFINDER_VER="2.6.6"
HTTPX_VER="1.6.9"
KATANA_VER="1.1.2"
DNSX_VER="1.2.1"
GW_VER="3.0.5"
ARCH="linux_amd64"
PD_BASE="https://github.com/projectdiscovery"

download_pd_tool() {
    local name="$1"
    local ver="$2"
    local repo="$3"
    local zipname="${name}_${ver}_${ARCH}.zip"
    local url="${PD_BASE}/${repo}/releases/download/v${ver}/${zipname}"

    if command -v "$name" &>/dev/null; then
        ok "$name already installed"
        return 0
    fi

    step "Downloading $name v${ver}..."
    local tmp
    tmp=$(mktemp -d)
    if wget -q --timeout=60 "$url" -O "$tmp/$zipname" 2>/dev/null; then
        unzip -q "$tmp/$zipname" -d "$tmp" 2>/dev/null || true
        local bin
        bin=$(find "$tmp" -maxdepth 2 -name "$name" -type f | head -1)
        if [[ -n "$bin" ]]; then
            chmod +x "$bin"
            sudo mv "$bin" /usr/local/bin/"$name"
            ok "$name v${ver} installed"
        else
            warn "$name: binary not found in archive"
        fi
    else
        warn "$name: download failed (check internet / firewall)"
    fi
    rm -rf "$tmp"
}

download_pd_tool "nuclei"    "$NUCLEI_VER"    "nuclei"
download_pd_tool "subfinder" "$SUBFINDER_VER" "subfinder"
download_pd_tool "httpx"     "$HTTPX_VER"     "httpx"
download_pd_tool "katana"    "$KATANA_VER"    "katana"
download_pd_tool "dnsx"      "$DNSX_VER"      "dnsx"

# ── 5. assetfinder ────────────────────────────────────────────
if command -v assetfinder &>/dev/null; then
    ok "assetfinder already installed"
else
    step "Installing assetfinder..."
    ASSETFINDER_URL="https://github.com/tomnomnom/assetfinder/releases/download/v0.1.1/assetfinder-linux-amd64-0.1.1.tgz"
    tmp=$(mktemp -d)
    if wget -q --timeout=30 "$ASSETFINDER_URL" -O "$tmp/assetfinder.tgz" 2>/dev/null; then
        tar -xzf "$tmp/assetfinder.tgz" -C "$tmp" 2>/dev/null || true
        bin=$(find "$tmp" -name "assetfinder" -type f | head -1)
        if [[ -n "$bin" ]]; then
            chmod +x "$bin"
            sudo mv "$bin" /usr/local/bin/assetfinder
            ok "assetfinder installed"
        else
            warn "assetfinder binary not found in archive"
        fi
    else
        warn "assetfinder download failed"
    fi
    rm -rf "$tmp"
fi

# ── 6. gowitness ──────────────────────────────────────────────
if command -v gowitness &>/dev/null; then
    ok "gowitness already installed"
else
    step "Installing gowitness..."
    GW_INSTALLED=false

    # gowitness v3.x uses zip archives with a versioned binary name
    # Try several known URL patterns across v2 and v3 releases
    GW_URLS=(
        "https://github.com/sensepost/gowitness/releases/download/3.0.5/gowitness-3.0.5-linux-amd64.zip"
        "https://github.com/sensepost/gowitness/releases/download/3.0.5/gowitness-linux-amd64"
        "https://github.com/sensepost/gowitness/releases/download/2.5.1/gowitness-2.5.1-linux-amd64"
        "https://github.com/sensepost/gowitness/releases/download/2.4.2/gowitness-2.4.2-linux-amd64"
    )

    tmp=$(mktemp -d)
    for url in "${GW_URLS[@]}"; do
        fname=$(basename "$url")
        if wget -q --timeout=60 "$url" -O "$tmp/$fname" 2>/dev/null; then
            if [[ "$fname" == *.zip ]]; then
                unzip -q "$tmp/$fname" -d "$tmp" 2>/dev/null || true
                bin=$(find "$tmp" -name "gowitness*" ! -name "*.zip" -type f | head -1)
            else
                bin="$tmp/$fname"
            fi
            if [[ -n "$bin" ]] && [[ -f "$bin" ]]; then
                chmod +x "$bin"
                sudo mv "$bin" /usr/local/bin/gowitness
                ok "gowitness installed from $(basename $url)"
                GW_INSTALLED=true
                break
            fi
        fi
    done
    rm -rf "$tmp"

    # Last resort: apt or go install
    if ! $GW_INSTALLED; then
        sudo apt-get install -y -qq gowitness 2>/dev/null \
            && ok "gowitness installed via apt" \
            && GW_INSTALLED=true
    fi
    if ! $GW_INSTALLED; then
        if command -v go &>/dev/null; then
            GOFLAGS=-mod=mod go install github.com/sensepost/gowitness@latest 2>/dev/null \
                && ok "gowitness installed via go install" \
                || warn "gowitness install failed — screenshots will use chromium headless"
        else
            warn "gowitness not installed — screenshots will use chromium headless (that's fine)"
        fi
    fi
fi

# ── 7. amass ──────────────────────────────────────────────────
if command -v amass &>/dev/null; then
    ok "amass already installed"
else
    step "Installing amass..."
    sudo apt-get install -y -qq amass 2>/dev/null \
        && ok "amass installed" \
        || warn "amass not available — subfinder covers passive recon"
fi

# ── 8. theHarvester ───────────────────────────────────────────
if command -v theHarvester &>/dev/null; then
    ok "theHarvester already installed"
else
    step "Installing theHarvester..."
    sudo apt-get install -y -qq theharvester 2>/dev/null \
        && ok "theHarvester installed" \
        || {
            git clone -q https://github.com/laramies/theHarvester /opt/theHarvester 2>/dev/null || true
            if [[ -d /opt/theHarvester ]]; then
                pip install -q -r /opt/theHarvester/requirements/base.txt 2>/dev/null || true
                sudo ln -sf /opt/theHarvester/theHarvester.py /usr/local/bin/theHarvester
                ok "theHarvester installed from source"
            else
                warn "theHarvester install failed — email harvesting will use passive methods"
            fi
        }
fi

# ── 9. Python virtual environment ─────────────────────────────
step "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
ok "venv: $(pwd)/venv"

step "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Python packages installed"

# ── 10. Nuclei templates ──────────────────────────────────────
if command -v nuclei &>/dev/null; then
    step "Updating Nuclei templates..."
    nuclei -update-templates -silent 2>/dev/null \
        && ok "Nuclei templates updated" \
        || warn "Template update skipped (run: nuclei -update-templates)"
fi

# ── 11. Output directories ────────────────────────────────────
step "Creating output directories..."
mkdir -p output/{reports,screenshots,crawl,nmap,vuln} logs
ok "Output directories ready"

# ── 12. Final verification ────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}── Tool Verification ────────────────────────${RESET}"

declare -A TOOL_LEVEL=(
    [python3]="required"
    [nmap]="required"
    [whois]="required"
    [subfinder]="recommended"
    [nuclei]="recommended"
    [katana]="optional"
    [dnsx]="optional"
    [assetfinder]="optional"
    [gowitness]="optional"
    [amass]="optional"
    [theHarvester]="optional"
)

all_ok=true
for tool in python3 nmap whois subfinder nuclei katana dnsx assetfinder gowitness amass theHarvester; do
    level="${TOOL_LEVEL[$tool]}"
    if command -v "$tool" &>/dev/null; then
        ok "$tool"
    else
        case "$level" in
            required)
                err "$tool NOT found — REQUIRED"
                all_ok=false ;;
            recommended)
                warn "$tool NOT found — recommended (some features limited)" ;;
            *)
                warn "$tool NOT found — optional (graceful degradation active)" ;;
        esac
    fi
done

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
$all_ok && echo -e "${GREEN}${BOLD}  Shaheen 3 setup complete!${RESET}" \
         || echo -e "${YELLOW}${BOLD}  Setup done — some tools missing (see above)${RESET}"
echo ""
echo "  Activate venv  :  source venv/bin/activate"
echo "  Quick scan     :  python3 shaheen3.py -d example.com"
echo "  Full scan      :  python3 shaheen3.py -d example.com --full"
echo "  Fast scan      :  python3 shaheen3.py -d example.com --fast"
echo "  REST API       :  python3 shaheen3.py --api"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
