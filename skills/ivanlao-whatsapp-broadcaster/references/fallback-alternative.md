# Fallback — alternative quando la sandbox Cowork e' bloccata

Quando la sandbox di Claude Cowork del cliente **non puo' raggiungere
`graph.facebook.com`** (allowlist proxy, policy IT, account Pro non
modificabile, ecc.), il plugin non puo' usare il flusso standard via Bash.

Questo riferimento elenca le **alternative reali** ordinate per
scalabilita' + facilita' d'uso, cosi' la skill puo' instradare l'utente
verso la soluzione piu' adatta al suo caso.

## Tabella decisionale

| Scenario | Soluzione consigliata | Effort setup |
|----------|----------------------|--------------|
| Cliente ha gia' Make/n8n e fa marketing automation | **Make scenario** o **n8n workflow** | Basso |
| Cliente usa Google Workspace, no automazioni | **Google Apps Script + Google Sheets** | Basso |
| Cliente ha solo Mac/Win e poca tech | **Terminale locale** (script `.command` o `.bat`) | Medio |
| Test singolo / max 50 invii spot | **Postman + CSV runner** | Basso |
| Volume enterprise + SLA | **Webhook su VPS** (`api.laoivan.com`) o **BSP** (360dialog, Twilio) | Alto |

---

## 1. Make.com — scenario WhatsApp broadcaster

**Quando:** il cliente e' gia' su Make o vuole un'automazione gestita; volume
fino a migliaia di invii/giorno; rivendibile come servizio.

**Architettura tipo:**

```
[Schedule] -> [Google Sheets: Search rows status=da_inviare]
           -> [Iterator]
              -> [HTTP: Make a request POST graph.facebook.com/.../messages]
              -> [Google Sheets: Update row status=OK + message_id + timestamp]
              -> [Sleep 1.5s]
           -> [Aggregate report]
           -> [Email/Slack: report invii]
```

**Vantaggi:**
- Esecuzione fuori dalla sandbox -> nessun problema di network.
- Scheduler integrato (invio a blocchi giornalieri come Cowork).
- Log strutturato in Sheets.
- Error handler nativi Make (retry, fallback).

**Setup minimo:**
1. Spreadsheet con colonne: `Telefono`, `Nome`, `stato_invio`, `message_id`,
   `timestamp_invio`, `errore`.
2. Scenario con `Schedule` ogni X ore + `Sheets Search rows`
   `stato_invio is empty`.
3. Modulo `HTTP > Make a request`:
   - URL: `https://graph.facebook.com/v22.0/{{PHONE_NUMBER_ID}}/messages`
   - Header: `Authorization: Bearer {{TOKEN}}`
   - Body JSON: payload template Meta (vedi `references/invio-massivo.md`).
4. `Sleep` 1.5 secondi tra una riga e l'altra.

Template Make pronti: chiedi a Ivan (`info@laoivan.com`).

---

## 2. n8n self-hosted

**Quando:** il cliente ha un VPS o vuole autonomia totale; volume illimitato;
costo zero in software.

Pattern equivalente a Make, nodi:

```
[Cron] -> [Google Sheets / Excel / Baserow: Get rows]
       -> [Split In Batches]
          -> [HTTP Request: POST Graph API]
          -> [Set: stato_invio, message_id]
          -> [Google Sheets: Update row]
          -> [Wait 1.5s]
       -> [Send Email/Telegram: report]
```

**Vantaggi:** zero limiti operazioni, codice JS nei nodi Code per logica
custom (mapping placeholder, deduplica, blocchi).

---

## 3. Google Apps Script — semplice e gratis

**Quando:** il cliente vive su Google Sheets, niente piattaforme di
automazione, fino a ~500 invii per esecuzione (limite 6 min Apps Script).

```javascript
function sendBroadcast() {
  const PHONE_NUMBER_ID = 'XXXXX';
  const TOKEN = PropertiesService.getScriptProperties().getProperty('WA_TOKEN');
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const PHONE = headers.indexOf('Telefono');
  const NOME = headers.indexOf('Nome');
  const STATO = headers.indexOf('stato_invio');

  for (let i = 1; i < data.length; i++) {
    if (data[i][STATO] === 'OK') continue;
    const payload = {
      messaging_product: 'whatsapp',
      to: data[i][PHONE],
      type: 'template',
      template: {
        name: 'optin_lead',
        language: { code: 'it' },
        components: [
          { type: 'body', parameters: [{ type: 'text', text: data[i][NOME] }] }
        ]
      }
    };
    const res = UrlFetchApp.fetch(
      `https://graph.facebook.com/v22.0/${PHONE_NUMBER_ID}/messages`,
      {
        method: 'post',
        contentType: 'application/json',
        headers: { Authorization: `Bearer ${TOKEN}` },
        payload: JSON.stringify(payload),
        muteHttpExceptions: true,
      });
    const body = JSON.parse(res.getContentText());
    if (body.messages) {
      sheet.getRange(i + 1, STATO + 1).setValue('OK');
    } else {
      sheet.getRange(i + 1, STATO + 1).setValue('ERRORE: ' + JSON.stringify(body.error));
    }
    Utilities.sleep(1500);
  }
}
```

**Vantaggi:** zero costi, integrato con Google Sheets, trigger temporali
nativi.

**Limiti:** 6 min/esecuzione, 20 000 chiamate UrlFetch/giorno (free).

---

## 4. Terminale locale — fallback rapido

**Quando:** il cliente non puo' usare nessuna piattaforma esterna ed e' ok
con un setup tecnico locale.

La skill genera due artefatti pronti:

- `run_wa.command` (macOS) o `run_wa.bat` (Windows).
- Excel + `mapping.json` gia' confezionati nella cartella Cowork.

**Cliente esegue una volta sola:**

```
# macOS
brew install python
pip3 install --break-system-packages requests openpyxl phonenumbers

# Windows (PowerShell)
winget install Python.Python.3.12
pip install --break-system-packages requests openpyxl phonenumbers
```

**Per ogni invio:** il cliente fa doppio click su `run_wa.command` /
`run_wa.bat`. Il log viene scritto sull'Excel nella cartella Cowork, che la
skill rilegge per riferire l'esito.

**Limiti:** task programmati Cowork inutili (la sandbox non puo' lanciare
script sul Mac). Per invii ricorrenti si usa `crontab` Mac / Task Scheduler
Windows.

---

## 5. Postman — solo test

**Quando:** test di un singolo template o batch di max ~50 numeri.

1. Importa la collezione Postman *"WhatsApp Cloud API"* (esiste sul Postman
   Public API Network o chiedi a Ivan).
2. Configura environment con `phone_number_id` e `access_token`.
3. Usa **Collection Runner** + CSV per iterare la lista.

**Non per produzione:** errori manuali, nessun log strutturato, nessuna
gestione duplicati/retry.

---

## 6. Webhook hostato (`api.laoivan.com`) — soluzione enterprise

**Quando:** vuoi standardizzare il comportamento del plugin per **tutti** i
clienti, indipendentemente dalla policy della sandbox.

**Architettura:**

```
[Plugin/Skill] -> POST https://api.laoivan.com/wa/send (allowlist Cowork)
              -> Cloudflare Workers / Express
                 -> POST graph.facebook.com (token lato server)
                 -> Risposta + log
```

**Pro:**
- Funziona anche se il dominio Meta e' bloccato dal proxy Cowork
  (l'allowlist deve permettere solo `api.laoivan.com`).
- Token WABA centralizzato e ruotabile.
- Audit log lato server.
- Monetizzabile come SaaS (tier per volume).

**Contro:**
- Diventi responsabile del relay (uptime, sicurezza, GDPR).
- Costi infrastruttura (free tier Cloudflare Workers copre la maggior parte
  dei casi).

Roadmap plugin: `wab.py` v1.5+ supportera' `mode: relay` in
`waba_config.json` -> chiamate dirottate al webhook invece che a Graph API.

---

## 7. BSP (Business Solution Provider)

**Quando:** il cliente non vuole gestire l'infrastruttura e accetta di pagare
un BSP (360dialog, Twilio, Wati, Vonage, MessageBird).

**Pro:** API stabili, conformita' garantita, supporto enterprise.

**Contro:** costo per messaggio in aggiunta al pricing Meta; lock-in fornitore.

Non e' parte del plugin, ma e' un fallback valido per progetti enterprise.

---

## Come la skill decide

Pseudo-flusso:

```
env_check.py -> all_ok?
   |- SI  -> usa Bash + wab.py (flusso standard)
   |- NO  -> mostra all'utente il blocco
            -> chiedi: vuoi sbloccare la sandbox o passare a un fallback?
               |- sbloccare -> guida con onboarding-ambiente.md
               |- fallback  -> chiedi volume + ecosistema:
                  - < 100 invii spot     -> Postman / Apps Script
                  - 100-1000 ricorrenti  -> Make / Apps Script
                  - 1000+ ricorrenti     -> Make / n8n / webhook
                  - enterprise/SLA       -> webhook hostato / BSP
```

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
