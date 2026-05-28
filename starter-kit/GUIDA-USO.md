# Ivan Lao WhatsApp Broadcaster — Guida all'uso

Guida completa alla skill per la gestione degli account WhatsApp Business (WABA)
e l'invio massivo di campagne WhatsApp da file Excel.

**Ivan Lao Marketing Automation** · laoivan.com · info@laoivan.com

---

## Indice

1. Che cos'è
2. Requisiti
3. Installazione
4. La configurazione: le due posizioni
5. La struttura a cartelle consigliata
6. Primo avvio
7. Inviare una campagna: il flusso completo
8. Invio unico oppure a blocchi
9. Controllo dei numeri duplicati
10. Gestione dei template
11. Sicurezza, consenso e responsabilità
12. Risoluzione dei problemi
13. Riferimento rapido dei comandi

---

## 1. Che cos'è

Ivan Lao WhatsApp Broadcaster è una skill per Claude Cowork che permette di:

- gestire **uno o più account WhatsApp Business (WABA)**;
- inviare **campagne massive** di messaggi template a partire da un file Excel;
- programmare **invii a blocchi** giorno per giorno per le liste più grandi;
- tenere traccia di ogni invio con un **log scritto nel file Excel**.

Usa la **WhatsApp Business Cloud API ufficiale di Meta**. La skill ti guida
passo per passo: sceglie il template, controlla i limiti, valida i numeri,
verifica i dati e invia in sicurezza.

## 2. Requisiti

### Claude Desktop / Cowork
- App **Claude Desktop** (Mac o Windows). Non funziona da claude.ai web/mobile.
- **Cowork mode** attivo con una cartella di lavoro selezionata.
- In `Impostazioni → Funzionalità`:
  - *Esecuzione di codice cloud e creazione di file* = **ON**
  - *Consenti traffico di rete in uscita* = **ON**
  - *Lista domini consentiti* = **"Tutti i domini"** (oppure aggiungi
    manualmente `graph.facebook.com`).
- Senza queste impostazioni la sandbox non raggiunge la Graph API di Meta e
  l'invio non parte: la skill se ne accorge al primo avvio e ti guida.

### Meta / WhatsApp Business
- Un account **Meta Business** con app WhatsApp e numero verificato.
- Un **System User Token permanente** con i permessi
  `whatsapp_business_messaging` e `whatsapp_business_management`.
- Almeno un **template approvato** da Meta.

### Python (nella sandbox Cowork)
- **Python 3.10+** con `requests`, `openpyxl`, `phonenumbers`.
- Li installa automaticamente lo script `env_check.py` al primo avvio.

## 3. Installazione

1. **Installa il plugin** — apri il file `ivanlao-whatsapp-broadcaster.plugin`
   in Claude Cowork e conferma.
2. **Configura le impostazioni di Claude Desktop** come indicato nella sezione
   *Requisiti → Claude Desktop / Cowork*. Senza queste impostazioni la sandbox
   resta isolata dalla rete e l'invio non funziona.
3. **Check ambiente automatico** — al primo avvio la skill esegue
   `scripts/env_check.py` nella sandbox. Verifica Python, librerie, accesso a
   `graph.facebook.com` e installa ciò che manca. Se qualcosa è bloccato ti
   guida a risolverlo.
4. **Non serve uno slash command**: la skill si attiva da sola quando chiedi
   *"invia questo Excel su WhatsApp"*, *"configura un account WABA"* o simili.

> **Sandbox impossibile da sbloccare (policy IT Team/Enterprise)?** Il plugin
> include `references/fallback-alternative.md` con cinque alternative pronte:
> Make, n8n, Google Apps Script, terminale locale Mac/Win, Postman. La skill
> propone l'opzione più adatta al tuo volume e al tuo ecosistema.

## 4. La configurazione degli account

> **Hai un solo numero WhatsApp e una sola cartella?** E' il caso piu' comune e
> il piu' semplice: la skill crea un unico `waba_config.json` con un account
> nella tua cartella di lavoro e procede. Puoi saltare il discorso delle "due
> posizioni" e dei gruppi: serve solo a chi gestisce piu' clienti.

Le credenziali degli account stanno nel file **`waba_config.json`**. Se gestisci
**piu' clienti**, la skill lo cerca in **due posizioni**, in quest'ordine:

1. **Configurazione di progetto** — `wa_broadcaster/waba_config.json` dentro la
   cartella del singolo cliente. Vale solo per quel cliente.
2. **Configurazione condivisa** — `waba_config.json` nella **radice della
   cartella di lavoro** (la cartella Cowork che selezioni). La ereditano tutte
   le sottocartelle.

Vince sempre la configurazione di progetto, se presente. Questo permette di
**configurare gli account una volta sola** nella radice e usare una config
dedicata solo per i clienti con credenziali proprie.

### Struttura del file

```json
{
  "accounts": [
    {
      "nome_account": "Cliente Demo",
      "gruppo_account": "Italia",
      "waba_id": "1234567890",
      "phone_number_id": "0987654321",
      "access_token": "EAAB...token...",
      "phone_number": "+39 055 0000000",
      "whatsapp_name": "Demo Srl",
      "default_region": "IT",
      "graph_version": "v22.0",
      "daily_limit_override": null
    }
  ]
}
```

| Campo | Obbligatorio | Significato |
|-------|--------------|-------------|
| `nome_account` | sì | Etichetta con cui scegli l'account. Unica. |
| `gruppo_account` | no | Etichetta per **raggruppare** gli account quando sono molti (es. `Italia`, `Estero`, o per cliente). |
| `waba_id` | sì | WhatsApp Business Account ID. |
| `phone_number_id` | sì | ID del numero (non il numero). |
| `access_token` | sì | System User Token permanente. |
| `phone_number` | no | Numero leggibile, informativo. |
| `whatsapp_name` | no | Nome del profilo WhatsApp Business. |
| `default_region` | no | Region ISO (es. `IT`) per i numeri senza prefisso. |
| `graph_version` | no | Versione Graph API. Default `v22.0`. |
| `daily_limit_override` | no | Limite giornaliero manuale, se non leggibile via API. |

### Dove trovare i valori

- `waba_id` e `phone_number_id`: WhatsApp Manager / Meta for Developers → app →
  prodotto WhatsApp → API Setup.
- `access_token`: Business Settings → System Users → genera un token permanente
  con i permessi indicati al punto 2.

## 5. Come organizzare le cartelle

**Caso semplice — un solo cliente o un solo numero.** Ti basta **una cartella**
con dentro il file Excel dei contatti: la skill ci aggiunge `waba_config.json`
e il resto. Niente sotto-cartelle, niente di piu'.

**Caso multicliente.** Per gestire più clienti, organizza così la cartella di
lavoro:

```
Cartella di lavoro/                ← selezionala come cartella Cowork
├── waba_config.json               ← configurazione condivisa
├── Cliente A/
│   └── lista-contatti.xlsx
├── Cliente B/
│   └── lista-contatti.xlsx
└── Cliente C/
    ├── wa_broadcaster/
    │   └── waba_config.json        ← configurazione dedicata (override)
    └── lista-contatti.xlsx
```

La cartella **DEMO** inclusa nello starter kit è un esempio funzionante di
questa struttura: aprila per vederla in concreto.

## 6. Primo avvio

1. **Apri Claude Cowork** e seleziona la cartella di lavoro.
2. **Verifica ambiente** (v1.4.0): la skill esegue automaticamente
   `python3 wa_broadcaster/scripts/env_check.py`. Output atteso:
   tutti i punti **OK**, incluso `network_graph_api: HTTP 4xx` (la sandbox
   raggiunge `graph.facebook.com`). Se vedi `403 blocked-by-allowlist`,
   apri Impostazioni → Funzionalità → *Lista domini consentiti* =
   "Tutti i domini" e ripeti.
3. **Scrivi una richiesta operativa** in italiano, ad esempio:
   *"Configura gli account WABA"* oppure *"Manda questo Excel su WhatsApp"*.
4. La skill carica `waba_config.json` e copia gli script `wab.py` e
   `env_check.py` nella sottocartella `wa_broadcaster/` del progetto.
5. Da quel momento ogni invio passa per il flusso guidato: scelta template,
   limiti, mapping, dry-run, conferma esplicita, esecuzione.

## 7. Inviare una campagna: il flusso completo

La skill segue sempre questi passi, in ordine:

1. **Scelta del template** — la skill elenca i template approvati; scegli quello
   da inviare. Se sei indeciso, mostra anche i testi.
2. **Analisi del template** — individua i segnaposto (`{{1}}`, `{{2}}` …) e
   l'eventuale intestazione (testo o media).
3. **Controllo dei limiti** — verifica quanti messaggi può inviare il WABA nelle
   24 ore e la *quality rating* del numero.
4. **Conteggio dei contatti** — legge il file Excel e conta i destinatari.
5. **Scelta della modalità** — invio unico oppure a blocchi (vedi sezione 8).
6. **Verifica dei numeri** — normalizza i telefoni in formato E.164 e segnala
   numeri ambigui, non validi e **duplicati**.
7. **Mapping dei dati** — collega le colonne dell'Excel ai segnaposto del
   template; verifica che tutti i segnaposto abbiano un dato.
8. **Avviso di compliance** — promemoria su consenso e responsabilità.
9. **Conferma e invio** — mostra un riepilogo; solo dopo il tuo **sì esplicito**
   parte l'invio, con una pausa di sicurezza di ~1,5 secondi tra un messaggio e
   l'altro. Ogni esito viene scritto nel file Excel.

Le colonne di log aggiunte automaticamente all'Excel sono: `stato_invio`
(`OK` / `ERRORE` / `DUPLICATO`), `message_id`, `timestamp_invio`, `errore`.

L'invio è **ripartibile**: i contatti già `OK` non vengono mai reinviati. Se
qualcosa si interrompe, basta rilanciare.

## 8. Invio unico oppure a blocchi

Confronta il numero di contatti con il limite giornaliero del WABA:

- **Contatti entro il limite** → invio unico, tutto in una volta.
- **Contatti oltre il limite** → invio **a blocchi** su più giorni.

Per l'invio a blocchi la skill crea un **task programmato** di Claude Cowork che,
ogni giorno, invia il blocco successivo finché la lista non è completata. Ogni
giorno vengono inviati solo i contatti non ancora gestiti: i blocchi si
concatenano da soli.

## 9. Controllo dei numeri duplicati

La skill invia **una sola volta per numero di telefono**. I duplicati nella
lista — stesso numero, anche se scritto in modo diverso (`+39 333 1234567` e
`3331234567`) — vengono riconosciuti: la prima occorrenza viene inviata, le
altre vengono marcate `DUPLICATO` nel log e saltate. Nessun contatto riceve il
messaggio due volte. I duplicati vengono segnalati anche **prima** dell'invio.

## 10. Gestione dei template

Oltre all'invio, la skill gestisce i template del WABA: **elenco**, **creazione**
ed **eliminazione**. I template vanno approvati da Meta prima dell'uso; sono
inviabili solo quelli in stato `APPROVED`. Per modifiche sostanziali conviene
creare un nuovo template invece di modificarne uno approvato.

## 11. Sicurezza, consenso e responsabilità

- Il file `waba_config.json` contiene un **token sensibile**: non condividerlo,
  non caricarlo su Git (aggiungilo a `.gitignore`).
- L'invio di messaggi marketing via WhatsApp richiede il **consenso esplicito
  (opt-in)** dei destinatari e il rispetto del GDPR e delle policy di WhatsApp.
- L'invio senza consenso può causare blocchi, segnalazioni come spam e la
  **sospensione del numero WABA**.
- La responsabilità dell'invio e del trattamento dei dati è **interamente a
  carico di chi effettua l'invio**.

## 12. Risoluzione dei problemi

| Problema | Causa probabile | Soluzione |
|----------|-----------------|-----------|
| Claude propone Chrome MCP invece di inviare via Bash | Sandbox bloccata o skill non triggerata | Esegui `python3 wa_broadcaster/scripts/env_check.py` e segui i fix indicati. Vedi anche `references/onboarding-ambiente.md`. |
| `403 blocked-by-allowlist` su `graph.facebook.com` | Allowlist Cowork ristretta | Impostazioni Claude Desktop → Funzionalità → *Lista domini consentiti* = "Tutti i domini". |
| `connection refused` / `DNS bloccato` nella sandbox | Network egress OFF | Impostazioni Claude → *Consenti traffico di rete in uscita* = ON. |
| La sandbox è bloccata e non posso modificare i settings (Team/Enterprise) | Policy IT del cliente | Usa un fallback: vedi `references/fallback-alternative.md` (Make, n8n, Apps Script, terminale locale, Postman). |
| Errore `401` sulle credenziali | Token scaduto o errato | Genera un nuovo System User Token. |
| "Configurazione demo" all'avvio | Config con valori segnaposto | Completa l'onboarding con i dati reali. |
| Numeri segnalati come non validi | Formato errato nell'Excel | Correggi i numeri o salva la colonna come testo. |
| Limite di invio raggiunto | Tier giornaliero esaurito | Passa all'invio a blocchi. |
| L'Excel non viene salvato | File aperto in Excel | Chiudi il file e rilancia. |
| Libreria Python mancante | Dipendenze non installate | `pip install --break-system-packages requests openpyxl phonenumbers` (lo fa `env_check.py` automaticamente). |

## 13. Riferimento rapido dei comandi

Il motore della skill è `wab.py`. Comandi principali:

| Comando | Funzione |
|---------|----------|
| `env_check.py` | **Da eseguire per primo (v1.4.0):** verifica sandbox, Python, librerie, network egress, allowlist proxy. Auto-installa le librerie mancanti. |
| `validate` | Verifica le credenziali WABA (con `--gruppo` filtra un gruppo). |
| `templates` | Elenca i template di un account. |
| `template-create` / `template-delete` | Crea o elimina un template. |
| `limits` | Mostra limiti di invio e quality rating. |
| `prepare` | Ispeziona l'Excel e aggiunge le colonne di log. |
| `phones` | Normalizza i numeri e segnala ambigui, non validi e duplicati. |
| `send` | Invia il template alla lista (opzioni: `--limit`, `--dry-run`, `--retry-errors`, `--allow-duplicates`). |

Normalmente non lanci tu questi comandi: è la skill a usarli durante il dialogo
guidato.

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
