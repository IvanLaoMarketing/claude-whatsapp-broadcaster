# Gestione account WABA e template — Ivan Lao WhatsApp Broadcaster

Riferimento per leggere, creare, modificare ed eliminare i template e per
leggere le informazioni dell'account.

## Indice

1. Anatomia di un template
2. Elencare i template
3. Creare un template (file di definizione)
4. Modificare un template
5. Eliminare un template
6. Leggere limiti e quality rating
7. Categorie e regole di approvazione

---

## 1. Anatomia di un template

Un template WhatsApp è composto da `components`:

- **HEADER** (facoltativo): può essere `TEXT` (con al massimo un placeholder) o
  media — `IMAGE`, `VIDEO`, `DOCUMENT`. Un header media richiede sempre un URL
  del file al momento dell'invio.
- **BODY** (obbligatorio): il testo. Può contenere placeholder.
- **FOOTER** (facoltativo): testo breve, senza placeholder.
- **BUTTONS** (facoltativo): bottoni di risposta rapida o URL; un bottone URL
  può avere una parte dinamica.

I placeholder si scrivono `{{1}}`, `{{2}}` … (posizionali) oppure `{{nome}}`
(nominali). Un template usa un solo stile. Il motore `wab.py` riconosce entrambi
e, per i nominali, aggiunge `parameter_name` nella chiamata.

## 2. Elencare i template

```
python3 wab.py templates --config waba_config.json --account "NOME"
```

Mostra nome, stato, lingua, categoria, testo del corpo, intestazione,
placeholder e bottoni di ogni template. Con `--json` restituisce la struttura
completa (utile per costruire il mapping). Con `--name <nome>` filtra.

Sono inviabili **solo** i template in stato `APPROVED`.

## 3. Creare un template (file di definizione)

Scrivi un file JSON di definizione e crealo con:

```
python3 wab.py template-create --config waba_config.json --account "NOME" \
  --definition definizione_template.json
```

Esempio di definizione (corpo con placeholder + footer + bottone):

```json
{
  "name": "promo_primavera_2026",
  "language": "it",
  "category": "MARKETING",
  "components": [
    {
      "type": "HEADER",
      "format": "TEXT",
      "text": "Offerta per te, {{1}}",
      "example": { "header_text": ["Mario"] }
    },
    {
      "type": "BODY",
      "text": "Ciao {{1}}, fino al {{2}} hai il 20% di sconto in negozio.",
      "example": { "body_text": [["Mario", "30 aprile"]] }
    },
    { "type": "FOOTER", "text": "Rispondi STOP per non ricevere altri messaggi." },
    {
      "type": "BUTTONS",
      "buttons": [
        { "type": "QUICK_REPLY", "text": "Mi interessa" },
        { "type": "URL", "text": "Vai al sito", "url": "https://esempio.it" }
      ]
    }
  ]
}
```

Regole importanti:

- `name`: minuscolo, solo lettere/numeri/underscore, senza spazi.
- `category`: `MARKETING`, `UTILITY` o `AUTHENTICATION`. La categoria influenza
  prezzo e criteri di approvazione.
- Il campo `example` è quasi sempre **obbligatorio**: Meta lo usa per valutare
  il template. Fornisci esempi realistici per ogni placeholder.
- Per un header media usa `"format": "IMAGE"` (o `VIDEO`/`DOCUMENT`) e fornisci
  un esempio con l'handle del media o un URL, come da documentazione Meta.
- L'approvazione richiede da pochi minuti a 24 ore.

Per la struttura JSON completa di ogni tipo di componente consulta la skill
`whatsapp-cloud-api` (`references/template-management.md`).

## 4. Modificare un template

Meta consente modifiche **limitate**: in genere si può cambiare la categoria, o
il contenuto di un template in stato `REJECTED` o `APPROVED`, ma con vincoli
(non si cambia nome né lingua, e una modifica rimette il template in revisione).

Per questo, nella pratica: se servono cambiamenti sostanziali, **conviene creare
un nuovo template** con un nome aggiornato (es. `..._v2`) ed eliminare il
vecchio. Spiega questa scelta all'utente invece di forzare una modifica fragile.

Una modifica via API si fa con un `POST` all'ID del template
(`/<template_id>`); per i dettagli usa la skill `whatsapp-cloud-api`.

## 5. Eliminare un template

```
python3 wab.py template-delete --config waba_config.json --account "NOME" \
  --name nome_template
```

L'eliminazione è definitiva. Conferma sempre con l'utente prima di procedere.

## 6. Leggere limiti e quality rating

```
python3 wab.py limits --config waba_config.json --account "NOME"
```

Restituisce:

- **Numero**, **nome WhatsApp**, **throughput**.
- **Quality rating**: `GREEN` (buona), `YELLOW` (media), `RED` (bassa).
- **Limite giornaliero**: numero di conversazioni business-initiated verso
  clienti unici nelle 24 ore.

Dal 2025 i limiti sono calcolati a livello di **Business Portfolio** e condivisi
tra i numeri del portfolio. Il campo API può non essere sempre disponibile: in
quel caso leggi il limite da WhatsApp Manager → Impostazioni account → Limiti di
messaggistica e impostalo come `daily_limit_override` in `waba_config.json`.

Se la quality rating è `RED`, **non inviare campagne**: prima va recuperata la
qualità riducendo i volumi e migliorando i contenuti, altrimenti il numero
rischia la sospensione.

## 7. Categorie e regole di approvazione

- **MARKETING**: promozioni, novità, inviti. Più costoso, soggetto ai limiti
  giornalieri e al pacing di Meta.
- **UTILITY**: aggiornamenti su un'azione/ordine in corso dell'utente.
- **AUTHENTICATION**: codici OTP e verifiche.

Usare la categoria sbagliata (es. marketing mascherato da utility) porta a
declassamento o rifiuto. I template di un invio massivo "a freddo" sono quasi
sempre **MARKETING**.

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
