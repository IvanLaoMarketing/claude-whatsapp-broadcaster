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

## 3 passi per partire

1. **Installa il plugin** — apri `ivanlao-whatsapp-broadcaster.plugin` con
   Claude Cowork e conferma l'installazione.

2. **Installa le dipendenze Python** — una sola volta:
   ```
   pip install --break-system-packages requests openpyxl phonenumbers
   ```

3. **Prova con la cartella DEMO** — apri in Claude Cowork la cartella
   `DEMO - Ivan Lao WhatsApp Broadcaster` e scrivi, ad esempio:
   *"Configura gli account WABA"*. La skill rileva la configurazione demo e ti
   guida a inserire i dati reali.

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
