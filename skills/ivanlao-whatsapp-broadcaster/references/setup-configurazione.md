# Setup e configurazione — Ivan Lao WhatsApp Broadcaster

Guida per configurare uno o più account WhatsApp Business (WABA) nella skill.

## Indice

1. Prerequisiti
2. Dove trovare i 5 valori della configurazione
3. Il token di accesso: temporaneo vs permanente
4. Schema completo di `waba_config.json`
5. Sicurezza del token
6. Dipendenze Python
7. Verifica della configurazione

---

## 1. Prerequisiti

Per inviare con la WhatsApp Business Cloud API ufficiale servono:

- Un account **Meta Business** (Business Manager).
- Un'app su **Meta for Developers** con il prodotto **WhatsApp** aggiunto.
- Un **numero di telefono** registrato e verificato sulla piattaforma WhatsApp
  Business (non un WhatsApp normale).
- Almeno un **template** approvato (per iniziare conversazioni).

Se il cliente non ha ancora nulla di tutto questo, la skill `whatsapp-cloud-api`
inclusa nel pacchetto contiene una guida di setup completa
(`references/setup-guide.md`).

## 2. Dove trovare i 5 valori della configurazione

| Valore | Dove si trova |
|--------|---------------|
| `waba_id` | WhatsApp Manager → Impostazioni account, oppure Meta for Developers → WhatsApp → API Setup ("WhatsApp Business Account ID"). |
| `phone_number_id` | Meta for Developers → WhatsApp → API Setup → "Phone number ID" (è un ID numerico, **non** il numero di telefono). |
| `access_token` | Vedi punto 3. |
| `phone_number` | Il numero in formato leggibile, es. `+39 055 0000000`. Solo informativo. |
| `whatsapp_name` | Il nome visualizzato del profilo WhatsApp Business. Solo informativo. |

`waba_id` e `phone_number_id` sono cose diverse: il primo identifica l'account
WhatsApp Business, il secondo il singolo numero. La skill usa `waba_id` per i
template e `phone_number_id` per inviare e leggere i limiti.

## 3. Il token di accesso: temporaneo vs permanente

- Il token che Meta mostra nella pagina **API Setup** è **temporaneo** (scade
  in ~24 ore). Va bene solo per le prime prove.
- Per l'uso reale serve un **System User Token permanente**:
  1. Business Settings → Users → **System Users** → crea un system user (ruolo
     Admin o Employee).
  2. Assegna al system user gli **asset**: l'app e il WABA.
  3. "Generate New Token" → seleziona l'app → permessi
     `whatsapp_business_messaging` e `whatsapp_business_management`.
  4. Copia il token: **non verrà più mostrato**.

Se un comando restituisce `401 Unauthorized`, quasi sempre il token è scaduto o
non ha i permessi: rigenera un System User Token.

## 4. Schema completo di `waba_config.json`

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

| Campo | Obbligatorio | Note |
|-------|--------------|------|
| `nome_account` | sì (consigliato) | Etichetta per scegliere l'account. Deve essere unica. |
| `gruppo_account` | no | Etichetta per raggruppare gli account quando sono molti (es. `Italia`, `Estero`, o per cliente). |
| `waba_id` | **sì** | WhatsApp Business Account ID. |
| `phone_number_id` | **sì** | ID del numero (non il numero). |
| `access_token` | **sì** | System User Token permanente. |
| `phone_number` | no | Numero leggibile, informativo. |
| `whatsapp_name` | no | Nome profilo, informativo. |
| `default_region` | no | Region ISO (es. `IT`) per normalizzare i numeri senza prefisso. Default `IT`. |
| `graph_version` | no | Versione Graph API. Default `v22.0`. Cambiala solo se Meta lo richiede. |
| `daily_limit_override` | no | Limite giornaliero inserito a mano, se non leggibile via API. |

Per più clienti basta aggiungere altri oggetti all'array `accounts`. La skill
chiederà su quale operare e userà `--account "nome_account"`.

### Dove salvare `waba_config.json`: progetto o condiviso

La skill cerca `waba_config.json` in due posizioni, in quest'ordine:

1. **Config di progetto** — `wa_broadcaster/waba_config.json` nella cartella del
   progetto corrente. Vale solo per quel progetto.
2. **Config condivisa** — `waba_config.json` nella radice della cartella Cowork
   selezionata. Viene ereditata da tutti i sotto-progetti: si configura una
   volta sola.

Vince la config di progetto se esistono entrambe. Usa la **condivisa** se
gestisci più progetti o clienti con gli stessi account WABA; usa quella di
**progetto** quando consegni la skill a un cliente, così le sue credenziali
restano isolate nel suo progetto.

## 5. Sicurezza del token

Il token dà pieno accesso all'invio di messaggi a pagamento. Trattalo come una
password:

- **Non** condividerlo in chat, email o screenshot.
- **Non** committarlo su Git: aggiungi `waba_config.json` a `.gitignore`.
- Conserva il file solo nella cartella del progetto del cliente.
- Se sospetti che sia stato esposto, revocalo da Business Settings → System
  Users e generane uno nuovo.

## 6. Dipendenze Python

Il motore `wab.py` richiede tre librerie. Installale una volta sola:

```
pip install --break-system-packages requests openpyxl phonenumbers
```

- `requests` — chiamate HTTP alla Graph API.
- `openpyxl` — lettura/scrittura dei file Excel `.xlsx`.
- `phonenumbers` — normalizzazione dei numeri in formato E.164.

Se una libreria manca, `wab.py` si ferma con un messaggio che indica il comando
di installazione.

## 7. Verifica della configurazione

Dopo aver scritto `waba_config.json`, verifica subito tutti gli account:

```
python3 wab.py validate --config waba_config.json
```

Per ogni account il comando mostra `[OK]` con numero, nome WhatsApp e quality
rating, oppure `[FAIL]` con il motivo. Non procedere con gli invii finché tutti
gli account non risultano `[OK]`.

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
