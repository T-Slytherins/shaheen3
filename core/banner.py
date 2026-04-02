#!/usr/bin/env python3
"""Shaheen 3 ASCII Banner"""

RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

BANNER = r"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                      ║
║                     ███████╗██╗  ██╗ █████╗ ██╗  ██╗███████╗███████╗███╗   ██╗    ██████╗                            ║
║                     ██╔════╝██║  ██║██╔══██╗██║  ██║██╔════╝██╔════╝████╗  ██║         ██                            ║
║                     ███████╗███████║███████║███████║█████╗  █████╗  ██╔██╗ ██║     █████╝                            ║
║                     ╚════██║██╔══██║██╔══██║██╔══██║██╔══╝  ██╔══╝  ██║╚██╗██║         ██                            ║
║                     ███████║██║  ██║██║  ██║██║  ██║███████╗███████╗██║ ╚████║    ██████╝                            ║
║                    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝                                        ║
║                                                                                                                      ║
║                                                                                                                      ║
║                                                                                                                      ║
║             Advanced Red Teaming • OSINT Automation • Reconnaissance • Intelligence Correlation Engine               ║
║                                                                                                                      ║
║                                 Engineered by Pr0fessor SnApe  |  Version 1.0.0                                      ║
║                                                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝


         S H A H E E N   3  —  Elite Pentest & OSINT Suite
                   Crafted by Professor Snape
"""

INFO = """
  +==============================================================+
  |  Version : 1.0                    License : MIT             |
  |  Author  : Professor Snape        Platform: Linux/macOS     |
  |  Modules : Recon | Scan | Vuln | Web | Evasion | Exploit   |
  +==============================================================+
  [!] For AUTHORIZED penetration testing ONLY.
  [!] Unauthorized use is illegal. You are responsible.
"""


def print_banner():
    print(f"{RED}{BOLD}{BANNER}{RESET}")
    print(f"{YELLOW}{INFO}{RESET}")
