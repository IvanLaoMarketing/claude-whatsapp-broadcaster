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

- **Claude Cowork** installato.
- Un account **Meta Business** con app WhatsApp e numero verificato.
- Un **System User Token permanente** con i permessi `whatsapp_business_messaging`
  e `whatsapp_business_management`.
- Almeno un **template approvato** da Meta.
- **Python 3** con le librerie `requests`, `openpyxl`, `phonenumbers`.

## 3. Installazione

1. Installa il plugin: apri il file `ivanlao-whatsapp-broadcaster.plugin` in
   Claude Cowork e conferma.
2. Installa le dipendenze Python (una sola volta):
   ```
   pip install --break-system-packages requests openpyxl phonenumbers
   ```
3. Non serve avviare nulla con uno slash: la skill si attiva **da sola** quando
   chiedi qualcosa come *"invia questo Excel su WhatsApp"* o *"configura un
   account WABA"*.

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

Apri la cartella di lavoro con Claude Cowork e scrivi una richiesta, ad esempio
*"configura il mio account WABA"*. La skill:

1. Cerca `waba_config.json` nelle due posizioni.
2. Se non lo trova, o se trova una **configurazione demo** (campo `_demo: true`),
   avvia l'**onboarding guidato**: ti chiede dove salvare la configurazione
   (condivisa o di progetto) e raccoglie i dati degli account.
3. Verifica subito le credenziali.

Nella cartella DEMO la configurazione è un modello con valori segnaposto: al
primo avvio va sempre completata con i dati reali.

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
| Errore `401` sulle credenziali | Token scaduto o errato | Genera un nuovo System User Token. |
| "Configurazione demo" all'avvio | Config con valori segnaposto | Completa l'onboarding con i dati reali. |
| Numeri segnalati come non validi | Formato errato nell'Excel | Correggi i numeri o salva la colonna come testo. |
| Limite di invio raggiunto | Tier giornaliero esaurito | Passa all'invio a blocchi. |
| L'Excel non viene salvato | File aperto in Excel | Chiudi il file e rilancia. |
| Libreria Python mancante | Dipendenze non installate | `pip install --break-system-packages requests openpyxl phonenumbers` |

## 13. Riferimento rapido dei comandi

Il motore della skill è `wab.py`. Comandi principali:

| Comando | Funzione |
|---------|----------|
| `validate` | Verifica le credenziali (con `--gruppo` filtra un gruppo). |
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
