# Invio massivo — Ivan Lao WhatsApp Broadcaster

Riferimento per l'invio di template a una lista Excel: spec del file di mapping,
invio a blocchi programmato, gestione del log e degli errori.

## Indice

1. Il file Excel: colonne e log
2. Spec completa di `mapping.json`
3. Esempi di mapping
4. Il comando `send`
5. Invio a blocchi con task programmato
6. Le colonne di log
7. Errori di invio frequenti

---

## 1. Il file Excel: colonne e log

La lista contatti è un file `.xlsx` nella cartella del progetto. La prima riga
sono le intestazioni. Serve almeno una colonna con il numero di telefono; le
altre colonne alimentano i placeholder del template.

Il comando `prepare` aggiunge automaticamente quattro **colonne di log** in coda
se non esistono: `stato_invio`, `message_id`, `timestamp_invio`, `errore`.

Consigli da dare all'utente:

- Salvare la colonna del telefono come **testo** (per non perdere `+` e zeri).
- Una riga = un destinatario.
- Non lasciare aperto il file in Excel durante l'invio: bloccherebbe la
  scrittura del log.

**Invio univoco (deduplica).** Il motore invia **una sola volta per numero di
telefono**. I duplicati nella lista — stesso numero in formato E.164, anche se
scritto diversamente (`+39 333 1234567` e `3331234567`) — vengono individuati al
momento dell'invio: la prima occorrenza viene inviata, le altre vengono marcate
`DUPLICATO` nel log e saltate. Il comando `phones` li segnala in anticipo. Per
inviare comunque anche ai duplicati si usa `send --allow-duplicates`.

## 2. Spec completa di `mapping.json`

Il `mapping.json` collega le colonne dell'Excel ai placeholder del template.

```json
{
  "phone_column": "Telefono",
  "default_region": "IT",
  "name_columns": ["Nome", "Cognome"],
  "header": {
    "format": "IMAGE",
    "link": "https://esempio.it/banner.jpg",
    "filename": "catalogo.pdf"
  },
  "header_text_params": [
    { "from": "column", "value": "Citta" }
  ],
  "body_params": [
    { "placeholder": "1", "from": "column",  "value": "Nome" },
    { "placeholder": "2", "from": "literal", "value": "30 aprile" }
  ],
  "button_url_params": [
    { "index": 0, "from": "column", "value": "CodiceSconto" }
  ]
}
```

| Campo | Obbligatorio | Significato |
|-------|--------------|-------------|
| `phone_column` | **sì** | Nome esatto della colonna con il numero di telefono. |
| `default_region` | no | Region ISO per i numeri senza prefisso (default `IT`). |
| `name_columns` | no | Colonne di nome/cognome: i loro valori vengono formattati in **Start Case**. |
| `header` | solo se il template ha header media | `format` = `IMAGE`/`VIDEO`/`DOCUMENT`; `link` = URL o sorgente colonna; `filename` solo per `DOCUMENT`. |
| `header_text_params` | solo se header testo con placeholder | Lista ordinata di sorgenti. |
| `body_params` | se il corpo ha placeholder | Lista **ordinata**: un elemento per ogni placeholder del corpo. |
| `button_url_params` | solo per bottoni URL dinamici | `index` = posizione del bottone (da 0). |

### Sorgenti di valore

Ogni parametro è una sorgente, in due forme:

- `{ "from": "column", "value": "NomeColonna" }` → prende il valore dalla cella
  di quella colonna, per ogni riga.
- `{ "from": "literal", "value": "testo fisso" }` → usa lo stesso testo per
  tutti i destinatari.

In `header.link` la sorgente può essere una **stringa diretta** (l'URL) oppure
un oggetto `{from, value}` se l'URL del media cambia riga per riga.

### Regole

- **Ordine dei body_params**: deve seguire l'ordine dei placeholder del
  template (`{{1}}` → primo elemento, `{{2}}` → secondo, ecc.). Il campo
  `placeholder` è solo descrittivo; conta la posizione nella lista.
- **Copertura totale**: ogni placeholder del template deve avere una sorgente.
  Il comando `send --dry-run` blocca se manca qualcosa.
- **Celle vuote**: se in una riga manca il valore di un placeholder, quella riga
  viene marcata `ERRORE` e **saltata** (non si invia un messaggio con un buco).
- **Nomi**: le colonne in `name_columns` vengono sempre formattate in Start
  Case, anche se citate nei `body_params`.

## 3. Esempi di mapping

**Template solo testo, un placeholder (il nome):**

```json
{
  "phone_column": "Cellulare",
  "default_region": "IT",
  "name_columns": ["Nome"],
  "body_params": [
    { "placeholder": "1", "from": "column", "value": "Nome" }
  ]
}
```

**Template con header immagine fissa e due placeholder:**

```json
{
  "phone_column": "Telefono",
  "default_region": "IT",
  "name_columns": ["Nome"],
  "header": { "format": "IMAGE", "link": "https://esempio.it/promo.jpg" },
  "body_params": [
    { "placeholder": "1", "from": "column",  "value": "Nome" },
    { "placeholder": "2", "from": "literal", "value": "offerta di primavera" }
  ]
}
```

**Template senza placeholder (basta il telefono):**

```json
{ "phone_column": "Telefono", "default_region": "IT" }
```

## 4. Il comando `send`

```
python3 wab.py send --config waba_config.json --account "NOME" \
  --file lista.xlsx --mapping mapping.json --template nome_template \
  --lang it [--limit N] [--interval 1.5] [--dry-run]
```

| Opzione | Effetto |
|---------|---------|
| `--dry-run` | Valida tutto (numeri, placeholder, mapping) senza inviare nulla. Usalo sempre prima dell'invio reale. |
| `--limit N` | Invia solo i prossimi `N` contatti non ancora `OK`. È la base dell'invio a blocchi. Senza `--limit` invia tutti i rimanenti. |
| `--interval` | Secondi tra un messaggio e l'altro. Default `1.5`, minimo `1.0`. |
| `--lang` | Codice lingua del template; se omesso usa quello del template. |
| `--retry-errors` | Ritenta anche i contatti in stato `ERRORE` di una run precedente. |
| `--allow-duplicates` | Invia anche ai numeri duplicati. Default: i duplicati vengono saltati e registrati come `DUPLICATO`. |

Il `send` è **idempotente e ripartibile**: i contatti con `stato_invio = OK` non
vengono mai reinviati. Se l'invio si interrompe (rete, file bloccato, stop
manuale), basta rilanciare lo stesso comando per riprendere da dove si era
fermato.

I contatti in `ERRORE` **non** vengono ritentati automaticamente: questo evita di sprecare quota su numeri non validi e fa terminare correttamente le campagne a blocchi. Per ritentarli (es. dopo aver corretto la lista) usa `--retry-errors`.

## 5. Invio a blocchi con task programmato

Quando i contatti superano il limite giornaliero, l'invio va spalmato su più
giorni. La skill usa un **task programmato Cowork** (nessun tool esterno).

Procedura:

1. **Dimensione del blocco**: circa il 90% del limite giornaliero (margine di
   sicurezza). Esempio: limite 1000 → blocco 900.
2. **Numero di giorni**: `ceil(contatti / blocco)`. Esempio: 5000 contatti,
   blocco 900 → 6 giorni.
3. Crea il task con `mcp__scheduled-tasks__create_scheduled_task`, cadenza
   giornaliera, all'orario concordato. Prompt del task (autosufficiente):

   > Ivan Lao WhatsApp Broadcaster — invio blocco giornaliero. Cartella
   > progetto: `<PERCORSO>`. Account WABA: `<NOME>`. Invia il prossimo blocco di
   > `<BLOCCO>` messaggi del template `<TEMPLATE>` (lingua `<LANG>`) dalla lista
   > `<FILE.xlsx>`, eseguendo `wab.py send` con `--limit <BLOCCO>` e
   > `--mapping mapping.json`. Aggiorna il log nell'Excel e riferisci quanti
   > inviati e quanti rimasti. Se i rimasti sono 0, avvisa che il task va
   > disattivato.

4. Ogni giorno il task lancia `send --limit <BLOCCO>`: vengono inviati solo i
   contatti non ancora `OK`, quindi i blocchi si concatenano automaticamente.
5. A lista esaurita, ricorda all'utente di disattivare il task.

L'intervallo di 1,5 s tra i messaggi vale anche dentro ogni blocco.

## 6. Le colonne di log

Per ogni contatto, dopo il tentativo di invio:

| Colonna | Contenuto |
|---------|-----------|
| `stato_invio` | `OK` inviato, `ERRORE` fallito o saltato, `DUPLICATO` numero già presente nella lista (non inviato). |
| `message_id` | ID del messaggio restituito da Meta (solo se `OK`). |
| `timestamp_invio` | Data e ora del tentativo (`AAAA-MM-GG HH:MM:SS`). |
| `errore` | Descrizione dell'errore, se presente. |

Il log viene salvato **dopo ogni singolo invio**, sia per l'invio unico sia per
ogni blocco: anche un'interruzione improvvisa non perde dati e non causa doppi
invii.

## 7. Errori di invio frequenti

| Codice / sintomo | Significato | Azione |
|------------------|-------------|--------|
| `131030` | Numero non valido o non su WhatsApp | Riga marcata `ERRORE`, l'invio prosegue. Pulisci la lista. |
| `132xxx` | Parametri del template errati | Controlla `mapping.json` vs placeholder del template; rifai `--dry-run`. |
| `131049` / `130472` | Limite giornaliero o pacing per-utente raggiunto | Passa all'invio a blocchi su più giorni. |
| `131026` | Messaggio non recapitabile | Il destinatario potrebbe non poter ricevere; normale su liste grandi. |
| `100` (parametro) | Campo mancante o malformato | Verifica `mapping.json` e l'URL del media. |
| `80007` / rate limit | Troppe richieste | Aumenta `--interval`. |
| `wb.save` fallisce | Excel aperto o non scrivibile | Chiudi il file e rilancia: i già `OK` non si reinviano. |

Per l'elenco completo dei codici di errore Meta, consulta la skill
`whatsapp-cloud-api` (`references/api-reference.md`).

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
