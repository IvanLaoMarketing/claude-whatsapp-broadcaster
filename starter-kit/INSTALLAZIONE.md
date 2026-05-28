# Installazione rapida — Ivan Lao WhatsApp Broadcaster

Benvenuto. Questo starter kit contiene tutto il necessario per gestire campagne
WhatsApp Business con la skill *Ivan Lao WhatsApp Broadcaster*.

> Ivan Lao Marketing Automation · laoivan.com

## Contenuto del kit

| Elemento | A cosa serve |
|----------|--------------|
| `ivanlao-whatsapp-broadcaster.plugin` | Il plugin da installare in Claude Cowork. |
| `GUIDA-USO.pdf` / `GUIDA-USO.md` | La guida completa all'uso. |
| `DEMO - Ivan Lao WhatsApp Broadcaster/` | Una cartella di esempio con la struttura multicliente consigliata. |
| `INSTALLAZIONE.md` | Questo file. |

## 4 passi per partire

1. **Installa il plugin** — apri `ivanlao-whatsapp-broadcaster.plugin` con
   Claude Cowork e conferma l'installazione.

2. **Configura Claude Desktop per usare la rete della sandbox** (v1.4.0)
   — Impostazioni → Funzionalità:
   - *Esecuzione di codice cloud e creazione di file* = **ON**
   - *Consenti traffico di rete in uscita* = **ON**
   - *Lista domini consentiti* = **"Tutti i domini"** (o aggiungi
     `graph.facebook.com` manualmente).

   Senza questo passaggio Claude proverà a usare Chrome MCP invece della
   Graph API di Meta, e l'invio non funzionerà.

3. **Verifica ambiente** — la skill esegue automaticamente
   `scripts/env_check.py` al primo avvio. Controlla Python, librerie e
   raggiungibilità di `graph.facebook.com`. Installa anche le dipendenze
   mancanti.

4. **Prova con la cartella DEMO** — apri in Claude Cowork la cartella
   `DEMO - Ivan Lao WhatsApp Broadcaster` e scrivi, ad esempio:
   *"Configura gli account WABA"*. La skill rileva la configurazione demo e ti
   guida a inserire i dati reali.

> **La sandbox è bloccata dalla policy IT (account Team/Enterprise)?** Vedi
> `skills/ivanlao-whatsapp-broadcaster/references/fallback-alternative.md`
> per Make, n8n, Google Apps Script, terminale locale o Postman.

## Prossimi passi

- Leggi `GUIDA-USO.pdf` per il flusso completo (configurazione, invio,
  invio a blocchi, duplicati, template).
- Apri `DEMO .../LEGGIMI - Struttura della cartella.md` per capire come
  organizzare le cartelle dei tuoi clienti.

## Requisiti

- Claude Cowork.
- Account Meta Business con app WhatsApp, numero verificato e un System User
  Token permanente.
- Almeno un template WhatsApp approvato.
- Python 3.

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
