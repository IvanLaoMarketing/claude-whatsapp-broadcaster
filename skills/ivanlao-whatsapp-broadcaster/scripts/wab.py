#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wab.py - Ivan Lao WhatsApp Broadcaster
======================================
Motore operativo per la gestione degli account WhatsApp Business (WABA) e
l'invio massivo di messaggi template tramite WhatsApp Business Cloud API
(Meta Graph API).

    by Ivan Lao Marketing Automation - laoivan.com

Sottocomandi:
  validate          Verifica le credenziali di ogni account in waba_config.json
  templates         Elenca i template di un account (con i placeholder)
  template-create   Crea un template da un file JSON di definizione
  template-delete   Elimina un template per nome
  limits            Mostra il limite di messaggi giornaliero e la quality rating
  prepare           Ispeziona un file Excel e aggiunge le colonne di log
  phones            Normalizza i numeri in E.164 e segnala quelli dubbi
  send              Invia un template a una lista Excel (invio unico o a blocchi)

Dipendenze:
  pip install --break-system-packages requests openpyxl phonenumbers
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BRAND = "Ivan Lao WhatsApp Broadcaster"
BRAND_LINE = "Ivan Lao WhatsApp Broadcaster  -  Ivan Lao Marketing Automation  -  laoivan.com"
GRAPH_BASE = "https://graph.facebook.com"
GRAPH_DEFAULT_VERSION = "v22.0"
LOG_COLUMNS = ["stato_invio", "message_id", "timestamp_invio", "errore"]
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

# Tier -> limite giornaliero di conversazioni business-initiated (clienti unici / 24h)
TIER_LIMITS = {
    "TIER_50": 50, "TIER_250": 250, "TIER_1K": 1000, "TIER_2K": 2000,
    "TIER_10K": 10000, "TIER_100K": 100000,
    "TIER_UNLIMITED": 1000000000, "UNLIMITED": 1000000000,
}

# --------------------------------------------------------------- utilities

def banner():
    print("=" * 68)
    print("  " + BRAND_LINE)
    print("=" * 68)

def die(msg, code=1):
    sys.stderr.write("\n[" + BRAND + "] ERRORE: " + str(msg) + "\n\n")
    sys.exit(code)

def info(msg):
    print("[" + BRAND + "] " + str(msg))

def need(name):
    """Importa una dipendenza, con messaggio chiaro se manca."""
    try:
        return __import__(name)
    except ImportError:
        die("libreria Python mancante: '" + name + "'.\n"
            "  Installa le dipendenze con:\n"
            "  pip install --break-system-packages requests openpyxl phonenumbers",
            code=2)

def cell_str(v):
    """Converte un valore di cella Excel in stringa pulita."""
    if v is None:
        return ""
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    if isinstance(v, int):
        return str(v)
    return str(v).strip()

def startcase(value):
    """Start Case rispettando spazi, trattini e apostrofi:
    'mario  ROSSI' -> 'Mario Rossi', "d'angelo" -> "D'Angelo",
    'anna-maria' -> 'Anna-Maria'."""
    s = cell_str(value)
    if not s:
        return ""
    out = []
    cap = True
    for ch in s.lower():
        if cap and ch.isalpha():
            out.append(ch.upper())
            cap = False
        else:
            out.append(ch)
        if ch in " \t-'’.":
            cap = True
    return re.sub(r"\s+", " ", "".join(out)).strip()

def normalize_phone(raw, region="IT"):
    """Ritorna dict {input, e164, digits, valid, ambiguous, note}.
    e164 con il '+';  digits senza '+'."""
    phonenumbers = need("phonenumbers")
    res = {"input": cell_str(raw), "e164": "", "digits": "",
           "valid": False, "ambiguous": False, "note": ""}
    s = res["input"]
    if not s:
        res["note"] = "vuoto"
        return res
    cleaned = re.sub(r"[^\d+]", "", s)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]

    def _try(text, reg):
        try:
            n = phonenumbers.parse(text, reg)
            if phonenumbers.is_valid_number(n):
                return phonenumbers.format_number(
                    n, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            return None
        return None

    candidates = []
    if cleaned.startswith("+"):
        e = _try(cleaned, None)
        if e:
            candidates.append(e)
    else:
        e1 = _try(cleaned, region)
        if e1:
            candidates.append(e1)
        e2 = _try("+" + cleaned, None)
        if e2:
            candidates.append(e2)
    candidates = list(dict.fromkeys(candidates))

    if not candidates:
        res["note"] = "numero non valido per la region '" + region + "'"
        return res
    res["valid"] = True
    res["e164"] = candidates[0]
    res["digits"] = candidates[0].lstrip("+")
    if len(candidates) > 1:
        res["ambiguous"] = True
        res["note"] = "interpretazioni multiple: " + " oppure ".join(candidates)
    elif not cleaned.startswith("+"):
        res["note"] = "prefisso internazionale assunto da region '" + region + "'"
    return res

# ------------------------------------------------------------- Graph API

def graph_version(account):
    return account.get("graph_version") or GRAPH_DEFAULT_VERSION

def graph_request(method, account, path, params=None, payload=None, timeout=30):
    requests = need("requests")
    url = GRAPH_BASE + "/" + graph_version(account) + "/" + str(path).lstrip("/")
    headers = {"Authorization": "Bearer " + str(account.get("access_token", ""))}
    for attempt in (1, 2):
        try:
            if method == "GET":
                r = requests.get(url, params=params, headers=headers, timeout=timeout)
            elif method == "POST":
                r = requests.post(url, params=params, json=payload,
                                  headers=headers, timeout=timeout)
            elif method == "DELETE":
                r = requests.delete(url, params=params, headers=headers, timeout=timeout)
            else:
                raise ValueError("metodo HTTP non supportato: " + str(method))
        except Exception as e:
            if attempt == 1:
                time.sleep(4)
                continue
            return 0, {"error": {"message": "connessione fallita: " + str(e)}}
        try:
            data = r.json()
        except Exception:
            data = {"error": {"message": "risposta non-JSON (HTTP " + str(r.status_code) + ")"}}
        if (r.status_code == 429 or r.status_code >= 500) and attempt == 1:
            time.sleep(6)
            continue
        return r.status_code, data
    return 0, {"error": {"message": "errore sconosciuto"}}

def graph_error(data):
    err = (data or {}).get("error") or {}
    parts = [str(err.get("message", "errore sconosciuto"))]
    if err.get("code") is not None:
        parts.append("(code " + str(err.get("code")) + ")")
    sub = err.get("error_user_msg")
    if not sub and isinstance(err.get("error_data"), dict):
        sub = err["error_data"].get("details")
    if sub:
        parts.append("- " + str(sub))
    return " ".join(parts)

# --------------------------------------------------------------- config

def load_config(path):
    p = Path(path)
    if not p.exists():
        die("file di configurazione non trovato: " + str(p) + "\n"
            "  Crea 'waba_config.json' partendo da assets/waba_config.example.json")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die("waba_config.json non e' un JSON valido: " + str(e))
    if isinstance(data, dict) and data.get("_demo"):
        die("questa e' una configurazione DEMO con dati segnaposto.\n"
            "  Aprila con la skill Ivan Lao WhatsApp Broadcaster: ti guida a\n"
            "  inserire le credenziali reali. Poi rimuovi il campo \"_demo\".")
    accounts = data.get("accounts") if isinstance(data, dict) else data
    if not isinstance(accounts, list) or not accounts:
        die("waba_config.json non contiene nessun account.")
    for i, a in enumerate(accounts, 1):
        for f in ("waba_id", "phone_number_id", "access_token"):
            if not a.get(f):
                die("account #" + str(i) + " ('" + cell_str(a.get("nome_account"))
                    + "'): campo obbligatorio '" + f + "' mancante.")
    return accounts

def pick_account(accounts, name):
    def _lbl(a):
        nm = cell_str(a.get("nome_account")) or "?"
        g = cell_str(a.get("gruppo_account"))
        return nm + (" [" + g + "]" if g else "")
    names = "; ".join(_lbl(a) for a in accounts)
    if name:
        for a in accounts:
            if cell_str(a.get("nome_account")).lower() == name.strip().lower():
                return a
        die("account '" + name + "' non trovato. Disponibili: " + names)
    if len(accounts) == 1:
        return accounts[0]
    die("piu' account presenti: specifica --account <nome>. Disponibili: " + names)

# ------------------------------------------------------------- templates

def fetch_templates(account, name_filter=None):
    params = {"fields": "name,status,category,language,components", "limit": 200}
    if name_filter:
        params["name"] = name_filter
    status, data = graph_request("GET", account,
        str(account["waba_id"]) + "/message_templates", params=params)
    if status != 200:
        die("impossibile leggere i template: " + graph_error(data))
    return data.get("data", [])

def parse_template(tpl):
    out = {"name": tpl.get("name", ""), "language": tpl.get("language", ""),
           "status": tpl.get("status", ""), "category": tpl.get("category", ""),
           "header": None, "body_text": "", "body_placeholders": [],
           "footer_text": "", "buttons": [], "named_params": False}
    for c in tpl.get("components", []):
        ctype = cell_str(c.get("type")).upper()
        if ctype == "HEADER":
            fmt = cell_str(c.get("format")).upper() or "TEXT"
            h = {"format": fmt, "placeholders": []}
            if fmt == "TEXT":
                h["text"] = c.get("text", "") or ""
                h["placeholders"] = PLACEHOLDER_RE.findall(h["text"])
            out["header"] = h
        elif ctype == "BODY":
            out["body_text"] = c.get("text", "") or ""
            out["body_placeholders"] = PLACEHOLDER_RE.findall(out["body_text"])
        elif ctype == "FOOTER":
            out["footer_text"] = c.get("text", "") or ""
        elif ctype == "BUTTONS":
            for b in c.get("buttons", []):
                out["buttons"].append({"type": cell_str(b.get("type")).upper(),
                                       "text": b.get("text", ""),
                                       "url": b.get("url", "")})
    allph = list(out["body_placeholders"])
    if out["header"]:
        allph += out["header"]["placeholders"]
    out["named_params"] = any(not str(p).isdigit() for p in allph)
    return out

# --------------------------------------------------------------- Excel

def find_excel(path_or_dir):
    p = Path(path_or_dir)
    if p.is_file():
        return p
    if p.is_dir():
        xs = sorted(f for f in p.glob("*.xlsx") if not f.name.startswith("~$"))
        if len(xs) == 1:
            return xs[0]
        if not xs:
            die("nessun file .xlsx trovato in " + str(p))
        die("piu' file .xlsx trovati, specifica quale con --file:\n  "
            + "\n  ".join(str(x) for x in xs))
    die("percorso non valido: " + str(p))

def open_sheet(path, sheet):
    openpyxl = need("openpyxl")
    try:
        wb = openpyxl.load_workbook(path)
    except Exception as e:
        die("impossibile aprire l'Excel '" + str(path) + "': " + str(e)
            + "\n  Assicurati che il file NON sia aperto in Excel.")
    ws = wb[sheet] if (sheet and sheet in wb.sheetnames) else wb.active
    return wb, ws

def ensure_log_columns(ws):
    headers = [cell_str(c.value) for c in ws[1]]
    added = []
    for name in LOG_COLUMNS:
        if name not in headers:
            ws.cell(row=1, column=ws.max_column + 1, value=name)
            headers.append(name)
            added.append(name)
    return headers, added

def guess_phone_column(headers):
    keys = ("telefono", "phone", "cell", "numero", "whatsapp", "mobile", "tel")
    for h in headers:
        if any(k in h.lower() for k in keys):
            return h
    return None

def save_wb(wb, path):
    try:
        wb.save(path)
    except Exception as e:
        die("impossibile salvare il log nell'Excel: " + str(e)
            + "\n  CHIUDI il file in Excel e riprendi: i contatti gia' 'OK' "
              "non verranno reinviati.")

# --------------------------------------------------------------- commands

def cmd_validate(args):
    banner()
    accounts = load_config(args.config)
    gruppo = getattr(args, "gruppo", None)
    if gruppo:
        accounts = [x for x in accounts
                    if cell_str(x.get("gruppo_account")).lower() == gruppo.strip().lower()]
        if not accounts:
            die("nessun account nel gruppo '" + gruppo + "'.")
    groups = {}
    for x in accounts:
        g = cell_str(x.get("gruppo_account")) or "(senza gruppo)"
        groups.setdefault(g, []).append(x)
    info("Verifica di " + str(len(accounts)) + " account in "
         + str(len(groups)) + " gruppo/i...\n")
    ok = 0
    for g in sorted(groups):
        print("  == Gruppo: " + g + " ==")
        for x in groups[g]:
            nome = cell_str(x.get("nome_account")) or "(senza nome)"
            status, data = graph_request("GET", x, x["phone_number_id"],
                params={"fields": "display_phone_number,verified_name,quality_rating"})
            if status == 200:
                ok += 1
                print("    [OK]   " + nome + "  |  numero: "
                      + cell_str(data.get("display_phone_number"))
                      + "  |  qualita': " + cell_str(data.get("quality_rating")))
            else:
                print("    [FAIL] " + nome + ": " + graph_error(data))
        print()
    info("Account validi: " + str(ok) + "/" + str(len(accounts)))
    if ok != len(accounts):
        sys.exit(1)

def cmd_templates(args):
    accounts = load_config(args.config)
    account = pick_account(accounts, args.account)
    parsed = [parse_template(t) for t in fetch_templates(account, args.name)]
    if args.json:
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
        return
    banner()
    info("Account: " + cell_str(account.get("nome_account"))
         + "  -  " + str(len(parsed)) + " template\n")
    for t in parsed:
        print("  - " + t["name"] + "  [" + t["status"] + "]  lingua="
              + t["language"] + "  categoria=" + t["category"])
        if t["header"]:
            h = t["header"]
            if h["format"] == "TEXT":
                print("      intestazione (TESTO): " + h.get("text", ""))
            else:
                print("      intestazione (MEDIA " + h["format"]
                      + "): richiede l'URL del file sorgente")
        if t["body_text"]:
            print("      corpo: " + t["body_text"].replace("\n", " / "))
        if t["body_placeholders"]:
            print("      placeholder corpo: "
                  + ", ".join("{{" + p + "}}" for p in t["body_placeholders"]))
        if t["footer_text"]:
            print("      footer: " + t["footer_text"])
        if t["buttons"]:
            print("      bottoni: "
                  + " | ".join(b["type"] + ":" + b["text"] for b in t["buttons"]))
        print()

def cmd_template_create(args):
    accounts = load_config(args.config)
    account = pick_account(accounts, args.account)
    p = Path(args.definition)
    if not p.exists():
        die("file di definizione non trovato: " + str(p))
    try:
        defn = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die("definizione template non valida (JSON): " + str(e))
    banner()
    status, data = graph_request("POST", account,
        str(account["waba_id"]) + "/message_templates", payload=defn)
    if status == 200:
        info("Template '" + cell_str(defn.get("name")) + "' inviato per approvazione.")
        info("ID: " + cell_str(data.get("id")) + "  -  stato: "
             + cell_str(data.get("status")))
    else:
        die("creazione template fallita: " + graph_error(data))

def cmd_template_delete(args):
    accounts = load_config(args.config)
    account = pick_account(accounts, args.account)
    banner()
    status, data = graph_request("DELETE", account,
        str(account["waba_id"]) + "/message_templates",
        params={"name": args.name})
    if status == 200 and data.get("success", True):
        info("Template '" + args.name + "' eliminato.")
    else:
        die("eliminazione template fallita: " + graph_error(data))

def quality_hint(qr):
    return {
        "GREEN": "(buona - ok per inviare campagne)",
        "YELLOW": "(media - riduci il ritmo e cura i contenuti)",
        "RED": "(bassa - rischio sospensione: NON inviare campagne ora)",
        "UNKNOWN": "(non ancora classificata)",
    }.get(cell_str(qr).upper(), "")

def interpret_limit(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        return TIER_LIMITS.get(value.strip().upper())
    if isinstance(value, dict):
        for k in ("limit", "value", "messaging_limit", "tier", "messaging_limit_tier"):
            if k in value:
                return interpret_limit(value[k])
    return None

def cmd_limits(args):
    accounts = load_config(args.config)
    account = pick_account(accounts, args.account)
    banner()
    info("Account: " + cell_str(account.get("nome_account")) + "\n")
    status, data = graph_request("GET", account, account["phone_number_id"],
        params={"fields": "display_phone_number,verified_name,quality_rating,throughput"})
    if status != 200:
        die("impossibile leggere il numero: " + graph_error(data))
    print("  Numero          : " + cell_str(data.get("display_phone_number")))
    print("  Nome WhatsApp   : " + cell_str(data.get("verified_name")))
    qr = cell_str(data.get("quality_rating"))
    print("  Quality rating  : " + qr + "  " + quality_hint(qr))
    thr = data.get("throughput")
    if isinstance(thr, dict):
        print("  Throughput      : " + cell_str(thr.get("level")))

    limit_value, limit_source = None, ""
    for field in ("whatsapp_business_manager_messaging_limit", "messaging_limit_tier"):
        st, d = graph_request("GET", account, account["phone_number_id"],
                              params={"fields": field})
        if st == 200 and field in d:
            limit_value, limit_source = d[field], field
            break
    daily = interpret_limit(limit_value)
    override = account.get("daily_limit_override")
    print()
    if override:
        print("  Limite giornaliero (da config) : " + str(override)
              + " conversazioni / 24h")
    if daily is not None:
        print("  Limite giornaliero (da API)    : ~" + str(daily)
              + " conversazioni / 24h")
        print("     [campo: " + limit_source + ", valore grezzo: "
              + json.dumps(limit_value, ensure_ascii=False) + "]")
    elif not override:
        print("  Limite giornaliero: NON disponibile via API.")
        print("  -> Leggilo da WhatsApp Manager > Impostazioni account >")
        print("     Limiti di messaggistica, poi inseriscilo in waba_config.json")
        print("     come \"daily_limit_override\": <numero>.")
    print()
    info("Il limite conta i CLIENTI UNICI a cui apri una conversazione in una")
    info("finestra mobile di 24h. Un template marketing a un nuovo contatto = 1.")

def cmd_prepare(args):
    banner()
    path = find_excel(args.file)
    wb, ws = open_sheet(path, args.sheet)
    headers, added = ensure_log_columns(ws)
    if added:
        save_wb(wb, path)
    nrows = max(0, ws.max_row - 1)
    info("File       : " + str(path))
    info("Foglio     : " + ws.title)
    info("Righe dati : " + str(nrows))
    print("\n  Colonne presenti:")
    for h in headers:
        print("    - " + h + ("   <- log" if h in LOG_COLUMNS else ""))
    print()
    if added:
        info("Colonne di log aggiunte: " + ", ".join(added))
    else:
        info("Colonne di log gia' presenti.")
    cand = guess_phone_column([h for h in headers if h not in LOG_COLUMNS])
    if cand:
        info("Probabile colonna telefono: '" + cand + "' (da confermare)")
    if args.json:
        print(json.dumps({"file": str(path), "sheet": ws.title, "rows": nrows,
                          "headers": headers, "log_columns_added": added,
                          "phone_column_guess": cand}, ensure_ascii=False))

def cmd_phones(args):
    banner()
    path = find_excel(args.file)
    wb, ws = open_sheet(path, args.sheet)
    headers = [cell_str(c.value) for c in ws[1]]
    if args.phone_col not in headers:
        die("colonna '" + args.phone_col + "' non trovata. Colonne: "
            + ", ".join(headers))
    idx = headers.index(args.phone_col)
    valid, ambiguous, invalid, duplicates = [], [], [], []
    seen = {}
    for r in range(2, ws.max_row + 1):
        raw = ws.cell(row=r, column=idx + 1).value
        if cell_str(raw) == "":
            continue
        res = normalize_phone(raw, args.region)
        if not res["valid"]:
            invalid.append((r, res["input"], res["note"]))
            continue
        if res["ambiguous"]:
            ambiguous.append((r, res["input"], res["e164"], res["note"]))
        else:
            valid.append((r, res["e164"]))
        if res["digits"] in seen:
            duplicates.append((r, res["e164"], seen[res["digits"]]))
        else:
            seen[res["digits"]] = r
    info("Colonna '" + args.phone_col + "' - region di default '"
         + args.region + "'\n")
    info("Numeri unici : " + str(len(seen)))
    info("Validi       : " + str(len(valid) + len(ambiguous)))
    info("Ambigui      : " + str(len(ambiguous)))
    info("Non validi   : " + str(len(invalid)))
    info("Duplicati    : " + str(len(duplicates)))
    if duplicates:
        print("\n  NUMERI DUPLICATI (in invio verra' contattato solo il primo):")
        for r, e, orig in duplicates:
            print("    riga " + str(r) + ": " + e
                  + "  (gia' presente alla riga " + str(orig) + ")")
    if ambiguous:
        print("\n  NUMERI AMBIGUI (da confermare con l'utente):")
        for r, inp, e, note in ambiguous:
            print("    riga " + str(r) + ": '" + inp + "' -> " + e + "  (" + note + ")")
    if invalid:
        print("\n  NUMERI NON VALIDI (da correggere o escludere):")
        for r, inp, note in invalid:
            print("    riga " + str(r) + ": '" + inp + "'  (" + note + ")")
    if not ambiguous and not invalid and not duplicates:
        print("\n  Tutti i numeri sono validi, unici e non ambigui.")


# ------------------------------------------------------------- send

def load_mapping(path):
    p = Path(path)
    if not p.exists():
        die("file di mapping non trovato: " + str(p) + "\n"
            "  Crea 'mapping.json' partendo da assets/mapping.example.json")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die("mapping.json non e' un JSON valido: " + str(e))

def resolve_source(spec, row_values, header_index, name_cols):
    """spec = stringa literal, oppure {"from":"column"|"literal","value":...}."""
    if isinstance(spec, str):
        return spec
    if not isinstance(spec, dict):
        return cell_str(spec)
    src = cell_str(spec.get("from")) or "literal"
    val = spec.get("value")
    if src == "column":
        col = cell_str(val)
        if col not in header_index:
            die("mapping: la colonna '" + col + "' non esiste nell'Excel.")
        text = cell_str(row_values[header_index[col]])
        if col in name_cols:
            text = startcase(text)
        return text
    return cell_str(val)

def build_components(tpl, mapping, row_values, header_index, name_cols):
    """Ritorna (components, errore_o_None)."""
    components = []
    hdr = tpl.get("header")
    if hdr:
        fmt = hdr["format"]
        if fmt in ("IMAGE", "VIDEO", "DOCUMENT"):
            mh = mapping.get("header") or {}
            if mh.get("link") is None:
                return None, "manca l'URL del file per l'intestazione media " + fmt
            link = resolve_source(mh.get("link"), row_values, header_index, name_cols)
            if not link:
                return None, "URL dell'intestazione media vuoto"
            key = fmt.lower()
            media = {"link": link}
            if fmt == "DOCUMENT" and mh.get("filename"):
                media["filename"] = cell_str(mh["filename"])
            components.append({"type": "header",
                               "parameters": [{"type": key, key: media}]})
        elif fmt == "TEXT" and hdr["placeholders"]:
            specs = mapping.get("header_text_params") or []
            if len(specs) < len(hdr["placeholders"]):
                return None, "placeholder dell'intestazione testo non mappati"
            params = []
            for ph, spec in zip(hdr["placeholders"], specs):
                val = resolve_source(spec, row_values, header_index, name_cols)
                if val == "":
                    return None, "placeholder intestazione vuoto ({{" + ph + "}})"
                obj = {"type": "text", "text": val}
                if not ph.isdigit():
                    obj["parameter_name"] = ph
                params.append(obj)
            components.append({"type": "header", "parameters": params})
    if tpl["body_placeholders"]:
        specs = mapping.get("body_params") or []
        if len(specs) < len(tpl["body_placeholders"]):
            return None, ("placeholder del corpo non mappati: il template ne ha "
                          + str(len(tpl["body_placeholders"])) + ", il mapping ne ha "
                          + str(len(specs)))
        params = []
        for ph, spec in zip(tpl["body_placeholders"], specs):
            val = resolve_source(spec, row_values, header_index, name_cols)
            if val == "":
                return None, "valore mancante per il placeholder {{" + ph + "}}"
            obj = {"type": "text", "text": val}
            if not ph.isdigit():
                obj["parameter_name"] = ph
            params.append(obj)
        components.append({"type": "body", "parameters": params})
    for b in mapping.get("button_url_params") or []:
        val = resolve_source(b, row_values, header_index, name_cols)
        components.append({"type": "button", "sub_type": "url",
                           "index": str(b.get("index", 0)),
                           "parameters": [{"type": "text", "text": val}]})
    return components, None

def write_log(ws, row, col, stato, mid, errore):
    ws.cell(row=row, column=col["stato_invio"] + 1, value=stato)
    ws.cell(row=row, column=col["message_id"] + 1, value=mid)
    ws.cell(row=row, column=col["timestamp_invio"] + 1,
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ws.cell(row=row, column=col["errore"] + 1, value=errore)

def cmd_send(args):
    banner()
    accounts = load_config(args.config)
    account = pick_account(accounts, args.account)
    mapping = load_mapping(args.mapping)
    path = find_excel(args.file)

    matches = [parse_template(t) for t in fetch_templates(account, args.template)
               if t.get("name") == args.template]
    if not matches:
        die("template '" + args.template + "' non trovato sull'account '"
            + cell_str(account.get("nome_account")) + "'.")
    tpl = matches[0]
    lang = args.lang or tpl["language"]
    if tpl["status"] != "APPROVED":
        die("il template '" + tpl["name"] + "' non e' APPROVED (stato: "
            + tpl["status"] + "). WhatsApp consente l'invio solo di template approvati.")

    wb, ws = open_sheet(path, args.sheet)
    headers, added = ensure_log_columns(ws)
    if added:
        save_wb(wb, path)
    header_index = {h: i for i, h in enumerate(headers)}
    col = {name: header_index[name] for name in LOG_COLUMNS}

    phone_col = mapping.get("phone_column")
    if not phone_col or phone_col not in header_index:
        die("mapping: 'phone_column' assente o non presente nell'Excel.\n"
            "  Colonne disponibili: " + ", ".join(headers))
    region = mapping.get("default_region", "IT")
    name_cols = set(mapping.get("name_columns") or [])
    interval = max(1.0, min(float(args.interval), 5.0))
    dedup = not getattr(args, "allow_duplicates", False)

    pending = []
    done_ok = done_err = done_dup = 0
    processed_digits = set()
    for r in range(2, ws.max_row + 1):
        row_values = [ws.cell(row=r, column=c + 1).value for c in range(len(headers))]
        stato = cell_str(row_values[col["stato_invio"]]).upper()
        if stato == "OK":
            done_ok += 1
            if dedup:
                res = normalize_phone(row_values[header_index[phone_col]], region)
                if res["valid"]:
                    processed_digits.add(res["digits"])
            continue
        if stato == "DUPLICATO":
            done_dup += 1
            continue
        if stato == "ERRORE" and not getattr(args, "retry_errors", False):
            done_err += 1
            continue
        if cell_str(row_values[header_index[phone_col]]) == "":
            continue
        pending.append((r, row_values))

    limit = args.limit if (args.limit and args.limit > 0) else len(pending)
    batch = pending[:limit]

    info("Template   : " + tpl["name"] + " (" + lang + ", " + tpl["category"] + ")")
    info("Account    : " + cell_str(account.get("nome_account")))
    info("File       : " + str(path))
    info("Gia' 'OK'  : " + str(done_ok) + "   |   ERRORE: " + str(done_err)
         + "   |   DUPLICATI: " + str(done_dup))
    info("Da inviare ora: " + str(len(batch)) + "   |   In coda dopo: "
         + str(max(0, len(pending) - len(batch))))
    info("Intervallo : " + str(interval) + "s   |   Deduplica numeri: "
         + ("attiva" if dedup else "DISATTIVATA"))
    print()

    if args.dry_run:
        info("MODALITA' DRY-RUN: nessun messaggio verra' inviato.")
        problems = 0
        dup_preview = 0
        seen = set(processed_digits)
        for r, row_values in batch:
            res = normalize_phone(row_values[header_index[phone_col]], region)
            if not res["valid"]:
                problems += 1
                print("  riga " + str(r) + ": telefono NON valido '"
                      + res["input"] + "'")
                continue
            if dedup and res["digits"] in seen:
                dup_preview += 1
                print("  riga " + str(r) + ": duplicato (" + res["e164"]
                      + ") - verra' saltato")
                continue
            _, err = build_components(tpl, mapping, row_values, header_index, name_cols)
            if err:
                problems += 1
                print("  riga " + str(r) + ": " + err)
                continue
            if dedup:
                seen.add(res["digits"])
        info("Dry-run: " + str(problems) + " righe con problemi, "
             + str(dup_preview) + " duplicati che verranno saltati, su "
             + str(len(batch)) + " righe in coda.")
        if problems == 0:
            info("Nessun problema bloccante: la lista e' pronta per l'invio.")
        else:
            info("Risolvi i problemi segnalati prima di inviare.")
        return

    if not batch:
        info("Nessun contatto da inviare. Lista gia' completata.")
        return

    sent = failed = skipped = duplicates = 0
    for i, (r, row_values) in enumerate(batch, 1):
        tag = "  [" + str(i) + "/" + str(len(batch)) + "] riga " + str(r) + ": "
        res = normalize_phone(row_values[header_index[phone_col]], region)
        if not res["valid"]:
            write_log(ws, r, col, "ERRORE", "", "telefono non valido: " + res["note"])
            save_wb(wb, path)
            skipped += 1
            print(tag + "SALTATA (telefono non valido)")
            continue
        if dedup and res["digits"] in processed_digits:
            write_log(ws, r, col, "DUPLICATO", "",
                      "numero duplicato (" + res["e164"]
                      + ") gia' presente nella lista")
            save_wb(wb, path)
            duplicates += 1
            print(tag + "SALTATA (duplicato di " + res["e164"] + ")")
            continue
        comps, err = build_components(tpl, mapping, row_values, header_index, name_cols)
        if err:
            write_log(ws, r, col, "ERRORE", "", err)
            save_wb(wb, path)
            skipped += 1
            print(tag + "SALTATA (" + err + ")")
            continue
        if dedup:
            processed_digits.add(res["digits"])
        payload = {"messaging_product": "whatsapp", "to": res["digits"],
                   "type": "template",
                   "template": {"name": tpl["name"], "language": {"code": lang}}}
        if comps:
            payload["template"]["components"] = comps
        status, data = graph_request("POST", account,
            str(account["phone_number_id"]) + "/messages", payload=payload)
        if status == 200 and data.get("messages"):
            mid = cell_str(data["messages"][0].get("id"))
            write_log(ws, r, col, "OK", mid, "")
            sent += 1
            print(tag + "INVIATO -> " + res["e164"])
        else:
            emsg = graph_error(data)
            write_log(ws, r, col, "ERRORE", "", emsg)
            failed += 1
            print(tag + "ERRORE -> " + res["e164"] + ": " + emsg)
        save_wb(wb, path)
        if i < len(batch):
            time.sleep(interval)

    remaining = max(0, len(pending) - len(batch))
    print()
    info("Invio completato: " + str(sent) + " inviati, " + str(failed)
         + " errori, " + str(skipped) + " saltati, " + str(duplicates) + " duplicati.")
    info("Contatti ancora in coda: " + str(remaining))
    if remaining > 0:
        info("Esegui di nuovo 'wab.py send' (anche via task programmato) "
             "per il blocco successivo.")
    else:
        info("Lista completata. Se hai un task programmato attivo, puoi disattivarlo.")


# --------------------------------------------------------------- parser

def build_parser():
    p = argparse.ArgumentParser(prog="wab.py",
        description=BRAND + " - motore WABA / invio massivo WhatsApp")
    sub = p.add_subparsers(dest="cmd", required=True)

    def cfg(sp, account=True):
        sp.add_argument("--config", default="waba_config.json",
                        help="percorso di waba_config.json")
        if account:
            sp.add_argument("--account", default=None,
                            help="nome_account (obbligatorio se piu' di uno)")

    v = sub.add_parser("validate", help="verifica le credenziali degli account")
    cfg(v, account=False)
    v.add_argument("--gruppo", default=None,
                   help="verifica solo gli account di questo gruppo")
    v.set_defaults(func=cmd_validate)

    t = sub.add_parser("templates", help="elenca i template di un account")
    cfg(t)
    t.add_argument("--name", default=None, help="filtra per nome template")
    t.add_argument("--json", action="store_true", help="output JSON")
    t.set_defaults(func=cmd_templates)

    tc = sub.add_parser("template-create", help="crea un template da un file JSON")
    cfg(tc)
    tc.add_argument("--definition", required=True, help="file JSON di definizione")
    tc.set_defaults(func=cmd_template_create)

    td = sub.add_parser("template-delete", help="elimina un template per nome")
    cfg(td)
    td.add_argument("--name", required=True, help="nome del template da eliminare")
    td.set_defaults(func=cmd_template_delete)

    l = sub.add_parser("limits", help="mostra limiti di invio e quality rating")
    cfg(l)
    l.set_defaults(func=cmd_limits)

    pr = sub.add_parser("prepare", help="ispeziona l'Excel e aggiunge le colonne di log")
    pr.add_argument("--file", required=True, help="file .xlsx o cartella che lo contiene")
    pr.add_argument("--sheet", default=None)
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_prepare)

    ph = sub.add_parser("phones", help="normalizza i numeri in E.164")
    ph.add_argument("--file", required=True)
    ph.add_argument("--sheet", default=None)
    ph.add_argument("--phone-col", required=True, help="nome della colonna telefono")
    ph.add_argument("--region", default="IT", help="region ISO per i numeri senza prefisso")
    ph.set_defaults(func=cmd_phones)

    s = sub.add_parser("send", help="invia un template a una lista Excel")
    cfg(s)
    s.add_argument("--file", required=True)
    s.add_argument("--sheet", default=None)
    s.add_argument("--mapping", required=True, help="mapping.json")
    s.add_argument("--template", required=True, help="nome del template")
    s.add_argument("--lang", default=None, help="codice lingua (default: quello del template)")
    s.add_argument("--limit", type=int, default=0, help="quanti inviarne ora (0 = tutti)")
    s.add_argument("--interval", type=float, default=1.5, help="secondi tra un invio e l'altro")
    s.add_argument("--dry-run", action="store_true", help="valida senza inviare")
    s.add_argument("--retry-errors", action="store_true",
                   help="ritenta anche i contatti in stato ERRORE")
    s.add_argument("--allow-duplicates", action="store_true",
                   help="invia anche ai numeri duplicati (default: i duplicati vengono saltati)")
    s.set_defaults(func=cmd_send)
    return p

def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        die("interrotto dall'utente. I contatti gia' inviati restano salvati nel log.")
    except Exception as e:
        die("errore imprevisto: " + str(e))

if __name__ == "__main__":
    main()
