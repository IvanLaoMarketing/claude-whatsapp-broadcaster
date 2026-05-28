---
name: ivanlao-whatsapp-broadcaster
description: >-
  Skill di Ivan Lao Marketing Automation per la WhatsApp Business Cloud
  API di Meta: gestione account WhatsApp Business (WABA) e invio massivo
  di template da un file Excel. Usa SEMPRE questa skill quando l'utente
  vuole: fare un invio massivo, broadcast o campagna WhatsApp; inviare un
  template WhatsApp a una lista o a un Excel di contatti; mandare lo
  stesso messaggio a tutti i clienti; programmare invii WhatsApp a
  blocchi giornalieri; gestire un account WABA; creare, elencare o
  eliminare template WhatsApp; controllare limiti di invio o quality
  rating di un numero; trovare o rimuovere numeri duplicati in una lista
  WhatsApp. Attiva anche quando l'utente carica un Excel o CSV di
  contatti da contattare su WhatsApp, o nomina WABA, phone number id,
  WhatsApp Business Cloud API, template Meta. NON usare per un singolo
  messaggio occasionale, per chatbot o webhook WhatsApp, o per la WAHA
  API non ufficiale: in quei casi usa whatsapp-cloud-api o waha-whatsapp.
compatibility: >-
  Richiede Claude Cowork con accesso a una cartella di progetto. Usa Python 3
  (requests, openpyxl, phonenumbers) e accesso di rete a graph.facebook.com.
---

# Ivan Lao WhatsApp Broadcaster

Skill ufficiale di **Ivan Lao Marketing Automation** ( laoivan.com ) per la
gestione degli account WhatsApp Business (WABA) e per l'invio massivo di
messaggi template tramite la **WhatsApp Business Cloud API** ufficiale di Meta.

Questa skill guida l'utente passo dopo passo: sceglie il template, controlla i
limiti, valida i numeri, verifica i placeholder, costruisce il file di mapping,
invia con un intervallo di sicurezza e registra ogni invio nel file Excel.

## Stile e brand (importante)

Questa skill viene distribuita anche ai clienti di Ivan Lao. Mantieni sempre il
brand presente, senza esagerare:

- Apri la prima risposta operativa presentandoti come **"Ivan Lao WhatsApp
  Broadcaster"**.
- Chiudi le risposte operative con una firma breve, es.:
  `— Ivan Lao WhatsApp Broadcaster · laoivan.com`
- Rispondi in **italiano**, in modo diretto, tecnico e orientato ai risultati.
- Non inventare dati: se un'informazione manca (token, URL media, placeholder),
  **fermati e chiedila** prima di procedere.

## Il principio di sicurezza numero uno

Un invio massivo WhatsApp è irreversibile e può costare denaro reale e la
reputazione del numero. Per questo: **non inviare MAI messaggi senza una
conferma esplicita dell'utente** sul riepilogo pre-invio. In caso di dubbio,
chiedi. È sempre meglio una domanda in più che una campagna sbagliata.

---

## Architettura

Tre componenti lavorano insieme:

| Componente | Ruolo |
|------------|-------|
| **Questa skill** | Orchestrazione: dialogo guidato, controlli, decisioni. |
| **`scripts/wab.py`** | Motore deterministico: chiamate API, normalizzazione numeri, invio, log. |
| **`whatsapp-cloud-api` / `whatsapp-automation`** | Skill di supporto: riferimento approfondito su Cloud API, webhook, tipi di messaggio. Consultale per casi avanzati (chatbot, webhook, flows). |

`wab.py` fa il lavoro ripetitivo e rischioso (loop di invio, intervallo, log
riga per riga, resume). Tu, la skill, fai il lavoro intelligente: capire cosa
vuole l'utente, scegliere il template giusto, costruire il mapping, spiegare i
rischi. **Non scrivere loop di invio a mano: usa sempre `wab.py`.**

### Passo 0 — Check ambiente Claude (OBBLIGATORIO, prima volta e in caso di errore)

**Prima di qualsiasi altra azione** verifica che la sandbox Claude Cowork del
cliente sia configurata correttamente. Senza questo passaggio l'invio via Bash
non funziona e tu finiresti col proporre fallback inutili (es. Chrome MCP) o
bloccare l'utente con errori oscuri tipo `403 blocked-by-allowlist`.

Esegui sempre, **al primo avvio della skill nel progetto** e **ogni volta che
un comando `wab.py` fallisce con errore di rete**:

```
python3 wa_broadcaster/scripts/env_check.py
```

(al primo avvio lo script `env_check.py` non è ancora copiato nel progetto:
eseguilo direttamente dal percorso della skill, oppure copialo subito insieme
a `wab.py` — vedi Passo 0.5.)

Lo script verifica 8 punti:

1. **Ambiente** — siamo davvero nella sandbox Cowork (non nel terminale Mac
   del cliente).
2. **Python ≥ 3.10**.
3. **pip** disponibile.
4. **curl** disponibile.
5. **Librerie**: `requests`, `openpyxl`, `phonenumbers` (le installa
   automaticamente se mancanti).
6. **Auto-install** riuscito.
7. **Network egress verso `graph.facebook.com`** (HTTP 4xx atteso senza
   token, *non* deve essere 403 `blocked-by-allowlist`).

**Decisioni in base all'esito:**

| Stato `env_check` | Cosa fai |
|-------------------|----------|
| `all_ok = true` | Procedi con il Passo 0.5 e il flusso standard. |
| Libreria mancante + auto-install OK | Lo script l'ha già risolto. Continua. |
| `network_graph_api: 403 blocked-by-allowlist` | **Non procedere**. Apri `references/onboarding-ambiente.md` e guida il cliente a impostare `Lista domini consentiti = "Tutti i domini"` nelle Impostazioni Claude. |
| `network_graph_api: rete sandbox disabilitata` | Stesso: il cliente deve attivare *Consenti traffico di rete in uscita*. |
| `ambiente: locale` | La skill sta girando fuori dalla sandbox: indirizza il cliente a Claude Desktop + Cowork. |
| Sandbox impossibile da sbloccare (account Enterprise / policy IT) | Apri `references/fallback-alternative.md` e proponi la soluzione adatta al volume (Make, n8n, Google Apps Script, terminale locale, Postman). |

**Regola d'oro:** se il check fallisce, **non ripiegare mai su Chrome MCP per
inviare i template**. Chrome non è uno strumento adatto a campagne massive
WhatsApp e non sostituisce Graph API. Le uniche alternative valide sono nel
file `fallback-alternative.md`.

### Passo 0.5 — Preparazione della cartella di progetto

Alla prima esecuzione in un progetto, **dopo** che `env_check` è verde:

1. Copia `scripts/wab.py`, `scripts/env_check.py` e la cartella `assets/` di
   questa skill **dentro la cartella del progetto**, in una sottocartella
   `wa_broadcaster/`. Così configurazione, Excel, mapping e log restano
   insieme e il task programmato (invio a blocchi) avrà percorsi stabili.
2. Le dipendenze Python sono già installate da `env_check.py`. In caso di
   reinstallazione manuale:
   ```
   pip install --break-system-packages requests openpyxl phonenumbers
   ```
3. Gli script vanno eseguiti con `python3` nella sandbox. Usa il percorso
   della cartella di progetto così come è montata nel sandbox.

---

## Configurazione multi-account WABA

**Adatta la complessità all'utente.** La maggior parte degli utenti ha **un
solo numero WhatsApp e una sola cartella di lavoro**. In quel caso non parlare
di configurazione condivisa, gruppi o sotto-cartelle: crea un unico
`waba_config.json` con un account nella cartella di lavoro e procedi. Le due
posizioni e i gruppi descritti qui sotto servono **solo** a chi gestisce più
clienti o più numeri.

Le credenziali stanno in **`waba_config.json`**. La skill supporta più account
WABA contemporaneamente e cerca il file in **due posizioni**, in quest'ordine:

1. **Config di progetto** — `wa_broadcaster/waba_config.json` dentro la cartella
   del progetto su cui stai lavorando. Vale solo per quel progetto.
2. **Config condivisa** — `waba_config.json` nella **radice della cartella
   Cowork** (la cartella di lavoro principale selezionata dall'utente). Viene
   **ereditata da tutti i sotto-progetti**: si configura una volta sola.

Usa la **prima** che trovi (la config di progetto ha la precedenza). Risolvi
questo percorso a inizio lavoro e passalo a `--config` in **ogni** comando
`wab.py`. Nei comandi di esempio di questa skill, `--config waba_config.json` è
un **segnaposto**: sostituiscilo sempre con il percorso effettivo della config
risolta (di progetto o condivisa).

Schema (vedi `assets/waba_config.example.json`):

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

- `nome_account` è l'etichetta con cui l'utente sceglie l'account.
- `gruppo_account` (facoltativo): etichetta per **raggruppare** gli account
  quando sono molti (es. `Italia`, `Estero`, o per cliente). `wab.py validate`
  li mostra raggruppati e accetta `--gruppo` per verificarne uno solo.
- `waba_id`, `phone_number_id`, `access_token` sono **obbligatori**.
- `default_region` (ISO, es. `IT`) serve a normalizzare i numeri senza prefisso.
- `daily_limit_override`: usalo solo se il limite non è leggibile via API.

**Onboarding configurazione** — se non trovi `waba_config.json` in nessuna delle
due posizioni, oppure è incompleto:

1. Spiega all'utente, in modo semplice, dove trovare i valori: WhatsApp Manager
   / Meta for Developers → app → prodotto WhatsApp. Per i dettagli leggi
   `references/setup-configurazione.md`.
2. **Decidi dove salvare la configurazione:**
   - **Utente con un solo numero e una sola cartella** (caso più comune) →
     salva direttamente `waba_config.json` nella cartella di lavoro, senza
     fare domande sulla struttura.
   - **Utente che gestisce più clienti** → chiedi se preferisce una config
     **condivisa** (radice della cartella Cowork, ereditata da tutti i
     sotto-progetti) o **di progetto** (`wa_broadcaster/`, isolata per il
     singolo cliente).
3. Raccogli i dati per ogni account e scrivi `waba_config.json` nella posizione
   scelta.
4. Avvisa che il file contiene un token sensibile: **non va condiviso né
   committato su Git** (aggiungilo a `.gitignore`).
5. Verifica subito le credenziali (con il percorso della config risolta):
   ```
   python3 wab.py validate --config <percorso-waba_config.json>
   ```
6. Se più account sono presenti, da qui in avanti chiedi sempre **su quale
   account** operare e passa `--account "nome"` a ogni comando.

Quando crei il task programmato per l'invio a blocchi (Step 10), inserisci nel
prompt il **percorso assoluto della config risolta**: così il task continua a
funzionare in modo prevedibile anche se in futuro viene aggiunta o rimossa una
config di progetto.

**Configurazione demo.** Se la config risolta contiene `_demo: true` (o valori
segnaposto tipo `INSERISCI_...`), **non usarla per inviare**: è un modello da
popolare. Avvia subito l'onboarding per inserire i dati reali e, quando scrivi
la configurazione definitiva, **non includere** il campo `_demo`. Questo vale in
particolare nella cartella demo dello starter kit: al primo avvio la
configurazione va sempre completata con i dati reali.

---

## I due flussi operativi

Capisci cosa serve all'utente e instrada:

- Vuole **gestire l'account / i template** (vedere, creare, modificare,
  cancellare template; controllare limiti e qualità) → **Flusso A**.
- Vuole **inviare messaggi a una lista / un Excel** → **Flusso B** (il flusso
  principale).

---

## FLUSSO A — Gestione account WABA

| Obiettivo | Comando |
|-----------|---------|
| Verificare le credenziali | `python3 wab.py validate --config waba_config.json` |
| Elencare i template | `python3 wab.py templates --config waba_config.json --account "NOME"` |
| Limiti e quality rating | `python3 wab.py limits --config waba_config.json --account "NOME"` |
| Creare un template | `python3 wab.py template-create --config ... --account "NOME" --definition def.json` |
| Eliminare un template | `python3 wab.py template-delete --config ... --account "NOME" --name nome_template` |

Per **creare o modificare** template (struttura del file di definizione,
categorie, intestazioni media, bottoni, limiti alla modifica imposti da Meta)
leggi `references/gestione-waba.md`. La modifica di un template approvato è
limitata: spesso conviene crearne uno nuovo.

---

## FLUSSO B — Invio massivo da un file Excel

Segui questi step **in ordine**. Non saltarne nessuno: ognuno protegge l'utente
da un errore costoso.

### Step 1 — Chiedi il template PRIMA di tutto

È la primissima cosa da fare. Elenca i template approvati dell'account:

```
python3 wab.py templates --config waba_config.json --account "NOME"
```

Presenta all'utente i **nomi** dei template approvati. Se l'utente è incerto,
mostra anche il **testo del corpo** e l'eventuale intestazione, così sceglie con
cognizione. Considera solo i template in stato `APPROVED`: gli altri non sono
inviabili.

### Step 2 — Analizza il template scelto

Dal template scelto identifica:

- I **placeholder del corpo** (`{{1}}`, `{{2}}` … oppure nominali `{{nome}}`).
- L'**intestazione**: nessuna / testo / media (IMAGE, VIDEO, DOCUMENT).
- Eventuali **bottoni** con URL dinamico.

Se l'intestazione è media, l'utente dovrà fornirti un **URL pubblico HTTPS** del
file sorgente (foto/video/PDF). Se ci sono placeholder, ti serviranno i dati per
popolarli. Tienine nota: serviranno allo Step 6.

### Step 3 — Controlla i limiti di invio

**Prima di qualsiasi invio**, controlla quanti messaggi può inviare il WABA:

```
python3 wab.py limits --config waba_config.json --account "NOME"
```

Comunica all'utente il **limite giornaliero** (conversazioni business-initiated
verso clienti unici nelle 24h) e la **quality rating**:

- `RED` → **non inviare campagne**: rischio sospensione del numero. Fermati.
- `YELLOW` → procedi con cautela, volumi ridotti.
- `GREEN` → ok.

Se il limite non è leggibile via API, chiedi all'utente di leggerlo da WhatsApp
Manager e inseriscilo come `daily_limit_override` in `waba_config.json`.

### Step 4 — Ispeziona l'Excel e conta i contatti

```
python3 wab.py prepare --file <cartella-del-progetto-o-file.xlsx>
```

Questo comando: trova l'Excel, elenca le colonne, conta le righe dati e
**aggiunge le colonne di log** se mancano (`stato_invio`, `message_id`,
`timestamp_invio`, `errore`). Comunica all'utente quanti contatti ci sono.

### Step 5 — Invio unico o invio a blocchi? (decisione chiave)

Confronta il **numero di contatti** con il **limite giornaliero**:

- **Contatti ≤ limite giornaliero** → di norma **invio unico**.
- **Contatti > limite giornaliero** → serve un **invio a blocchi** su più
  giorni. Calcola: `giorni ≈ contatti / dimensione_blocco`, con
  `dimensione_blocco` pari a circa il 90% del limite (margine di sicurezza).

**Chiedi esplicitamente all'utente** quale modalità vuole, presentando il
calcolo. Se sceglie i blocchi, configura il task programmato (Step 10).

### Step 6 — Verifica numeri di telefono e duplicati

```
python3 wab.py phones --file <file.xlsx> --phone-col "NomeColonnaTelefono" --region IT
```

Il comando classifica i numeri in **validi / ambigui / non validi** e segnala i
**duplicati** (stesso numero E.164 ripetuto, anche se scritto in modo diverso):

- **Ambigui** o **non validi** → elencali all'utente e **chiedi conferma o
  correzione in fase di onboarding**, prima di inviare. Non tirare a indovinare.
- **Duplicati** → comunica all'utente quanti sono. In fase di invio il motore
  contatta **una sola volta** ogni numero: la prima occorrenza viene inviata, le
  successive vengono marcate `DUPLICATO` nel log e saltate, così nessun contatto
  riceve il messaggio due volte. Se l'utente vuole davvero inviare anche ai
  duplicati c'è l'opzione `--allow-duplicates`.
- Tutti i numeri vengono inviati in formato **E.164** dal motore.

Suggerisci all'utente di salvare la colonna telefono come **testo** in Excel,
per non perdere lo zero iniziale o il `+`.

### Step 7 — Costruisci il mapping e verifica i placeholder

Crea `mapping.json` nella cartella del progetto (vedi
`assets/mapping.example.json` e la spec completa in
`references/invio-massivo.md`). Esempio:

```json
{
  "phone_column": "Telefono",
  "default_region": "IT",
  "name_columns": ["Nome", "Cognome"],
  "header": { "format": "IMAGE", "link": "https://esempio.it/banner.jpg" },
  "body_params": [
    { "placeholder": "1", "from": "column",  "value": "Nome" },
    { "placeholder": "2", "from": "literal", "value": "promo di primavera" }
  ]
}
```

Regole da rispettare:

- **Copertura placeholder**: ogni placeholder del template deve avere una
  sorgente nel mapping, e ogni colonna citata deve esistere nell'Excel. Se un
  placeholder non ha dati nel file, **avvisa l'utente** e non inviare finché
  non è risolto.
- **Nomi e cognomi**: ogni colonna usata per nome/cognome va messa in
  `name_columns`. Il motore la formatta automaticamente in **Start Case**
  (`mario rossi` → `Mario Rossi`).
- **Intestazione media**: se il template ha header IMAGE/VIDEO/DOCUMENT, in
  `header.link` va l'**URL fornito dall'utente**. Se manca, chiedilo.

Poi esegui una **prova a vuoto** che valida tutto senza inviare nulla:

```
python3 wab.py send --config waba_config.json --account "NOME" \
  --file <file.xlsx> --mapping mapping.json --template nome_template \
  --lang it --dry-run
```

Risolvi ogni problema segnalato dal dry-run prima di procedere.

### Step 8 — Avviso di compliance e responsabilità

Prima dell'invio, comunica all'utente, con chiarezza ma senza allarmismi:

> Stai per inviare messaggi marketing via WhatsApp. Assicurati di avere il
> **consenso (opt-in)** dei destinatari e di rispettare GDPR e le policy di
> WhatsApp. L'invio senza consenso può causare blocchi, segnalazioni come spam
> e la **sospensione del numero WABA**. La responsabilità dell'invio e del
> trattamento dei dati è **interamente a carico di chi effettua l'invio**.

Registra che l'utente ne è consapevole, poi procedi.

### Step 9 — Riepilogo, conferma ed esecuzione dell'invio

Mostra un **riepilogo pre-invio**: account, template e lingua, n. contatti da
inviare, modalità (unico / blocchi), intervallo, URL media se presente.
**Attendi un "sì" esplicito.** Solo allora:

```
python3 wab.py send --config waba_config.json --account "NOME" \
  --file <file.xlsx> --mapping mapping.json --template nome_template \
  --lang it --interval 1.5
```

Il motore invia un messaggio alla volta, con **intervallo di 1,5 s** (minimo 1 s),
e scrive **riga per riga** l'esito nelle colonne di log. È **ripartibile**: i
contatti già `OK` non vengono mai reinviati, quindi se qualcosa si interrompe
basta rilanciare lo stesso comando. Invia inoltre **una sola volta per numero**:
i duplicati nella lista vengono saltati e registrati come `DUPLICATO`.

A fine invio, riporta all'utente: inviati, errori, saltati, e dove vedere il log.

### Step 10 — Invio a blocchi con task programmato Cowork

Se al passo 5 l'utente ha scelto i blocchi:

1. Concorda la **dimensione del blocco** (≈90% del limite giornaliero) e l'orario.
2. Crea un **task programmato Cowork** giornaliero con
   `mcp__scheduled-tasks__create_scheduled_task`. Il prompt del task deve essere
   autosufficiente, ad esempio:

   > Ivan Lao WhatsApp Broadcaster — invio blocco giornaliero. Cartella
   > progetto: `<PERCORSO>`. Account WABA: `<NOME>`. Invia il prossimo blocco
   > di `<N>` messaggi del template `<TEMPLATE>` dalla lista `<FILE.xlsx>`,
   > eseguendo `wab.py send` con `--limit <N>`. Aggiorna il log nell'Excel e
   > riferisci quanti inviati e quanti rimasti. Quando la lista è completa,
   > avvisa che il task può essere disattivato.

3. Ogni esecuzione lancia `wab.py send ... --limit <N>`: il motore invia solo i
   contatti non ancora `OK`, quindi i blocchi si concatenano da soli giorno
   dopo giorno fino a fine lista.
4. Quando i contatti rimasti sono 0, ricorda all'utente di disattivare il task.

Dettagli ed esempi completi: `references/invio-massivo.md`.

---

## Checklist pre-invio (riepilogo)

Prima di lanciare un `send` reale, verifica di aver fatto tutto:

1. Template scelto dall'utente ed `APPROVED`.
2. Limiti e quality rating controllati (`limits`).
3. Contatti contati; modalità unico/blocchi decisa con l'utente.
4. Numeri verificati (`phones`); ambigui/non validi chiariti con l'utente; duplicati segnalati (il motore invia una sola volta per numero).
5. `mapping.json` completo; **tutti** i placeholder coperti da dati reali.
6. URL del file fornito, se il template ha intestazione media.
7. Nomi/cognomi in `name_columns` (Start Case automatico).
8. `--dry-run` superato senza problemi.
9. Avviso compliance/responsabilità comunicato.
10. Riepilogo mostrato e **conferma esplicita** ricevuta.

---

## Riferimenti e script

| File | Quando leggerlo |
|------|-----------------|
| `references/onboarding-ambiente.md` | **PRIMA COSA**: come impostare Claude Desktop perché la sandbox raggiunga Graph API |
| `references/fallback-alternative.md` | Soluzioni alternative quando la sandbox è bloccata: Make, n8n, Apps Script, terminale locale, Postman |
| `references/setup-configurazione.md` | Dove trovare waba_id/phone_id/token, token permanenti, sicurezza, dipendenze |
| `references/gestione-waba.md` | Anatomia dei template, creazione/modifica/cancellazione, lettura account |
| `references/invio-massivo.md` | Spec completa di `mapping.json`, invio a blocchi, errori di invio |
| `scripts/env_check.py` | **Esegui sempre per primo**: verifica sandbox, librerie, network egress, allowlist proxy |
| `scripts/wab.py` | Motore operativo (tutti i sottocomandi). Esegui `python3 wab.py -h` |
| `assets/waba_config.example.json` | Modello di configurazione multi-account |
| `assets/mapping.example.json` | Modello di mapping per l'invio |

Le skill `whatsapp-cloud-api` e `whatsapp-automation` (incluse nel pacchetto)
restano disponibili per scenari avanzati: webhook, chatbot, messaggi interattivi.

---

## Troubleshooting rapido

| Sintomo | Causa probabile | Cosa fare |
|---------|-----------------|-----------|
| `validate` → 401 / errore token | Token scaduto o errato | Genera un nuovo System User Token (vedi setup) |
| Invio → `131030` o numero non in WhatsApp | Numero non valido o non su WhatsApp | Il motore lo segna ERRORE e prosegue; verifica la lista |
| Invio → `132000` / parametri | Placeholder non corrispondenti | Controlla `mapping.json` vs template; rifai `--dry-run` |
| Invio → `131049` / `130472` | Limite o pacing raggiunto | Passa all'invio a blocchi su più giorni |
| `wb.save` / Excel non salvabile | File aperto in Excel | Chiudi il file e rilancia: i già `OK` non si reinviano |
| Libreria Python mancante | Dipendenze non installate | `pip install --break-system-packages requests openpyxl phonenumbers` |
| `403 blocked-by-allowlist` su Graph API | Sandbox Cowork con allowlist ristretta | Settings Claude -> Funzionalità -> Lista domini = "Tutti i domini" (vedi `references/onboarding-ambiente.md`) |
| Claude propone Chrome MCP per inviare | Tool Bash non disponibile o skill non triggerata | Esegui `env_check.py`; abilita Esecuzione codice cloud nelle Impostazioni |
| Sandbox impossibile da sbloccare (Team/Enterprise) | Policy IT del cliente | Passa a un fallback (`references/fallback-alternative.md`): Make, n8n, Apps Script, terminale locale |

Per i codici di errore Meta consulta anche la skill `whatsapp-cloud-api`
(`references/api-reference.md`).

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
