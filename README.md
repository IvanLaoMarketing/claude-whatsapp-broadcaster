# Ivan Lao WhatsApp Broadcaster

**Suite di Ivan Lao Marketing Automation** per gestire account WhatsApp Business
(WABA) e inviare campagne massive di messaggi template tramite la **WhatsApp
Business Cloud API** ufficiale di Meta, a partire da un file Excel.

> Ivan Lao Marketing Automation — laoivan.com — info@laoivan.com

## Cosa contiene il plugin

| Skill | Funzione |
|-------|----------|
| **ivanlao-whatsapp-broadcaster** | Skill principale. Gestione WABA multi-account, scelta guidata del template, controllo limiti, validazione numeri (E.164), verifica placeholder, invio massivo o a blocchi programmato, log riga per riga nell'Excel. |
| **whatsapp-cloud-api** | Skill di supporto: riferimento completo sulla Cloud API di Meta (tipi di messaggio, webhook, template, compliance). |
| **whatsapp-automation** | Skill di supporto: automazione WhatsApp Business via Rube MCP (Composio). |

Le tre skill lavorano in tandem: la principale orchestra il flusso operativo, le
altre due forniscono il riferimento tecnico per gli scenari avanzati.

## Cosa fa la skill principale

- Gestione di **più account WABA** da un unico file di configurazione.
- Lettura, creazione ed eliminazione dei **template**.
- Controllo dei **limiti di invio giornalieri** e della **quality rating**.
- **Invio massivo** di template da Excel, con intervallo di sicurezza tra i
  messaggi (1,5 s) e **log di invio** scritto riga per riga nel file.
- **Invio a blocchi** programmato giorno per giorno tramite task Cowork, per le
  liste più grandi del limite giornaliero.
- Normalizzazione automatica dei **numeri di telefono in formato E.164**.
- Verifica della **copertura dei placeholder** del template rispetto alle
  colonne dell'Excel.
- Formattazione automatica di **nomi e cognomi in Start Case**.

## Struttura della repository

- `.claude-plugin/plugin.json` — manifest del plugin.
- `skills/` — sorgenti delle tre skill (`ivanlao-whatsapp-broadcaster`, `whatsapp-cloud-api`, `whatsapp-automation`).
- `starter-kit/` — pacchetto pronto all'uso:
  - `ivanlao-whatsapp-broadcaster.plugin` — plugin precompilato da installare in Claude Cowork.
  - `INSTALLAZIONE.md`, `GUIDA-USO.md`, `GUIDA-USO.pdf` — guide complete.
  - `DEMO - Ivan Lao WhatsApp Broadcaster/` — esempio di struttura cartelle multicliente.

## Installazione

### Opzione A — Plugin precompilato (consigliata)

1. Scarica [`starter-kit/ivanlao-whatsapp-broadcaster.plugin`](starter-kit/ivanlao-whatsapp-broadcaster.plugin) e installalo in Claude Cowork.
2. Installa le dipendenze Python (una sola volta):
   ```
   pip install --break-system-packages requests openpyxl phonenumbers
   ```

### Opzione B — Dai sorgenti

Clona la repo: `.claude-plugin/plugin.json` e `skills/` sono pronti all'uso per Claude Cowork.

## Primo utilizzo

1. Apri la cartella di un progetto in Cowork.
2. **Esegui il check ambiente** (la skill lo fa per te al primo avvio):
   `python3 wa_broadcaster/scripts/env_check.py`. Verifica Python, librerie,
   raggiungibilità di `graph.facebook.com` dalla sandbox.
3. Se il check segnala blocchi di rete, segui
   `skills/ivanlao-whatsapp-broadcaster/references/onboarding-ambiente.md` per
   impostare Claude Desktop (Impostazioni → Funzionalità → *Lista domini
   consentiti = "Tutti i domini"*).
4. Chiedi, ad esempio: *"Configura un account WABA"* oppure *"Invia questo
   Excel di contatti su WhatsApp"*: la skill si attiva e ti guida.
5. Alla prima esecuzione la skill crea `waba_config.json` (credenziali) e copia
   il proprio motore nella cartella del progetto.

> **Sandbox bloccata e non sbloccabile?** Vedi
> `references/fallback-alternative.md`: Make, n8n, Google Apps Script,
> terminale locale, Postman, webhook hostato.

## Requisiti

### Claude Desktop / Cowork
- App **Claude Desktop** (Mac/Win), non Web.
- **Cowork mode** con cartella selezionata.
- Impostazioni → Funzionalità:
  - *Esecuzione di codice cloud e creazione di file* = **ON**
  - *Consenti traffico di rete in uscita* = **ON**
  - *Lista domini consentiti* = **"Tutti i domini"** (o lista che include
    `graph.facebook.com`).

### Meta / WhatsApp Business
- Account Meta Business con app WhatsApp e numero verificato.
- **System User Token permanente** con i permessi
  `whatsapp_business_messaging` e `whatsapp_business_management`.
- Almeno un template approvato.

### Python
- Python 3.10+ con `requests`, `openpyxl`, `phonenumbers`
  (lo script `env_check.py` li installa automaticamente).

## Nota legale

L'invio di messaggi marketing via WhatsApp richiede il **consenso esplicito
(opt-in)** dei destinatari e il rispetto del GDPR e delle policy di WhatsApp.
La responsabilità dell'invio e del trattamento dei dati è **interamente a carico
di chi effettua l'invio**.

---

© Ivan Lao Marketing Automation · laoivan.com
