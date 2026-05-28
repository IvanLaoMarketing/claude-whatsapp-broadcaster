#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
env_check.py - Ivan Lao WhatsApp Broadcaster
============================================
Verifica che l'ambiente Claude Cowork (sandbox cloud) sia pronto per inviare
template WhatsApp tramite Graph API:

  1. Python >= 3.10
  2. Librerie: requests, openpyxl, phonenumbers
  3. Tool Bash disponibile (siamo in sandbox)
  4. Network egress verso graph.facebook.com (HTTPS 443)
  5. Allowlist Cowork: il dominio Meta non e' bloccato dal proxy

Output sia leggibile che JSON (--json). Se manca qualcosa, restituisce
un'istruzione operativa.

Uso:
  python3 env_check.py            # check completo + auto install librerie
  python3 env_check.py --json     # solo JSON
  python3 env_check.py --no-install
  python3 env_check.py --quick

    by Ivan Lao Marketing Automation - laoivan.com
"""
import json
import os
import platform
import shutil
import subprocess
import sys

GRAPH_HOST = "graph.facebook.com"
GRAPH_URL = f"https://{GRAPH_HOST}/v22.0/"
REQUIRED_LIBS = ["requests", "openpyxl", "phonenumbers"]


def banner():
    line = "=" * 68
    print(line)
    print("  Ivan Lao WhatsApp Broadcaster  -  Env Check  -  laoivan.com")
    print(line)


def check_python():
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    return {"name": "python_version", "ok": ok, "value": f"{v.major}.{v.minor}.{v.micro}",
            "required": ">=3.10",
            "fix": None if ok else "Aggiorna Python alla 3.10+. Su Cowork riavvia la sandbox."}


def check_lib(name):
    try:
        __import__(name)
        mod = sys.modules.get(name)
        version = getattr(mod, "__version__", "?")
        return {"name": f"lib_{name}", "ok": True, "value": version, "fix": None}
    except ImportError:
        return {"name": f"lib_{name}", "ok": False, "value": "non installata",
                "fix": f"pip install --break-system-packages {name}"}


def check_pip():
    pip = shutil.which("pip") or shutil.which("pip3")
    return {"name": "pip", "ok": bool(pip), "value": pip or "non trovato",
            "fix": None if pip else "Installa Python con pip incluso"}


def check_curl():
    curl = shutil.which("curl")
    return {"name": "curl", "ok": bool(curl), "value": curl or "non trovato",
            "fix": None if curl else "Installa curl"}


def check_sandbox_marker():
    hostname = platform.node()
    is_sandbox = ("sessions/" in os.getcwd() or os.path.exists("/.dockerenv")
                  or hostname.startswith(("jolly", "claude", "sandbox")))
    return {"name": "ambiente", "ok": True,
            "value": "sandbox Cowork" if is_sandbox else f"locale ({hostname})",
            "detail": "Sandbox Cowork attiva." if is_sandbox else "Esecuzione locale rilevata.",
            "fix": None}


def check_network_egress():
    """Verifica raggiungibilita' di graph.facebook.com.
    Distingue rete OK / 403 allowlist / DNS bloccato / rete disabilitata."""
    try:
        out = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}|%{errormsg}",
             "--max-time", "10", "-L", GRAPH_URL],
            capture_output=True, text=True, timeout=15)
        body = (out.stdout or "") + (out.stderr or "")
        first = (out.stdout or "").split("|")[0].strip()
        low = body.lower()
        if first.isdigit() and 200 <= int(first) < 600 and int(first) != 403:
            return {"name": "network_graph_api", "ok": True,
                    "value": f"HTTP {first}", "fix": None,
                    "detail": "Sandbox raggiunge graph.facebook.com."}
        if "403" in body or "blocked-by-allowlist" in low or first == "403":
            return {"name": "network_graph_api", "ok": False,
                    "value": "403 blocked-by-allowlist",
                    "fix": "Claude Desktop -> Impostazioni -> Funzionalita' -> 'Consenti traffico di rete in uscita' = ON, 'Lista domini consentiti' = 'Tutti i domini' (o aggiungi graph.facebook.com).",
                    "detail": "Il proxy Cowork blocca Meta."}
        if "could not resolve" in low or "name or service not known" in low:
            return {"name": "network_graph_api", "ok": False, "value": "DNS bloccato",
                    "fix": "Attiva il traffico di rete in uscita nelle Impostazioni Claude Desktop."}
        if "connection refused" in low or "no route to host" in low:
            return {"name": "network_graph_api", "ok": False,
                    "value": "rete sandbox disabilitata",
                    "fix": "Attiva 'Consenti traffico di rete in uscita' nelle Impostazioni Claude Desktop."}
        return {"name": "network_graph_api", "ok": False,
                "value": f"output inatteso: {body[:120]}",
                "fix": "Verifica le impostazioni di rete della sandbox in Claude Desktop."}
    except FileNotFoundError:
        return {"name": "network_graph_api", "ok": False, "value": "curl assente",
                "fix": "Installa curl nella sandbox."}
    except subprocess.TimeoutExpired:
        return {"name": "network_graph_api", "ok": False, "value": "timeout",
                "fix": "Probabile blocco del proxy. Attiva 'Tutti i domini' nelle Impostazioni Claude."}


def install_missing(libs):
    if not libs:
        return {"installed": [], "errors": []}
    cmd = ["pip", "install", "--break-system-packages"] + libs
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if out.returncode == 0:
            return {"installed": libs, "errors": []}
        return {"installed": [], "errors": [out.stderr.strip()[-400:]]}
    except Exception as e:
        return {"installed": [], "errors": [str(e)]}


def run_all(auto_install=True, quick=False):
    checks = []
    checks.append(check_sandbox_marker())
    checks.append(check_python())
    checks.append(check_pip())
    checks.append(check_curl())
    for lib in REQUIRED_LIBS:
        checks.append(check_lib(lib))

    missing = [c["name"].replace("lib_", "") for c in checks
               if c["name"].startswith("lib_") and not c["ok"]]
    if missing and auto_install and not quick:
        print(f"[env-check] Installo librerie mancanti: {', '.join(missing)}")
        res = install_missing(missing)
        for lib in missing:
            for i, c in enumerate(checks):
                if c["name"] == f"lib_{lib}":
                    checks[i] = check_lib(lib)
        checks.append({"name": "auto_install",
                       "ok": not res["errors"],
                       "value": ", ".join(res["installed"]) or "errore",
                       "fix": res["errors"][0] if res["errors"] else None})

    checks.append(check_network_egress())

    summary = {"all_ok": all(c["ok"] for c in checks),
               "checks": checks, "next_action": None}
    blockers = [c for c in checks if not c["ok"]]
    if blockers:
        summary["next_action"] = blockers[0].get("fix") or "Risolvi il problema mostrato sopra."
    else:
        summary["next_action"] = "Ambiente OK. La skill puo' inviare via Bash + Graph API."
    return summary


def print_human(summary):
    for c in summary["checks"]:
        icon = "OK " if c["ok"] else "KO "
        detail = f"  -> {c.get('detail')}" if c.get("detail") else ""
        print(f"[{icon}] {c['name']:22s} : {c['value']}{detail}")
        if not c["ok"] and c.get("fix"):
            print(f"        FIX: {c['fix']}")
    print("-" * 68)
    if summary["all_ok"]:
        print("[Ivan Lao WhatsApp Broadcaster] Ambiente pronto. Procedi con l'invio.")
    else:
        print("[Ivan Lao WhatsApp Broadcaster] Ambiente NON pronto.")
        print(f"[Ivan Lao WhatsApp Broadcaster] Prossima azione: {summary['next_action']}")
        print("[Ivan Lao WhatsApp Broadcaster] Se non puoi sbloccare la sandbox, vedi")
        print("  references/fallback-alternative.md (Make, n8n, Google Apps Script,")
        print("  terminale locale, Postman).")


def main():
    args = sys.argv[1:]
    json_mode = "--json" in args
    quick = "--quick" in args
    no_install = "--no-install" in args
    if not json_mode:
        banner()
    summary = run_all(auto_install=not no_install, quick=quick)
    if json_mode:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_human(summary)
    sys.exit(0 if summary["all_ok"] else 1)


if __name__ == "__main__":
    main()
