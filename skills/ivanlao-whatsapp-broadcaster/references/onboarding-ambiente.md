# Onboarding ambiente — preparazione di Claude Desktop / Cowork

Questo riferimento copre **il primissimo passo** del plugin: assicurarsi che la
sandbox di Claude Cowork del cliente sia configurata in modo da poter eseguire
`wab.py` e raggiungere la **Graph API di Meta** (`graph.facebook.com`).

Senza questi requisiti l'invio via Bash non funziona e il plugin deve
ripiegare sulle alternative documentate in `fallback-alternative.md`.

## I 5 requisiti

| # | Requisito | Come si verifica |
|---|-----------|------------------|
| 1 | App **Claude Desktop** (non Web/Mobile) | Versione visibile da `Aiuto -> Informazioni` |
| 2 | **Cowork mode** attivo + cartella selezionata | Sidebar Cowork con folder visibile |
| 3 | **Esecuzione codice cloud** (sandbox Linux) ON | `Impostazioni -> Funzionalita' -> Esecuzione del codice e creazione di file` |
| 4 | **Consenti traffico di rete in uscita** ON | Stessa sezione, sotto |
| 5 | **Lista domini consentiti = "Tutti i domini"** (o lista che include `graph.facebook.com`) | Dropdown sotto la voce precedente |

## Procedura guidata (Mac/Win)

1. Apri **Claude Desktop**.
2. Vai su `Claude` (menu top) -> `Impostazioni` -> sezione **Funzionalita'**.
3. Controlla i toggle:
   - **Artefatti** -> ON
   - **Esecuzione di codice cloud e creazione di file** -> **ON**
   - **Consenti traffico di rete in uscita** -> **ON**
4. Sotto compare il box **"Lista domini consentiti"**: deve essere su **"Tutti
   i domini"**. Sotto deve leggere *"Claude puo' accedere a tutti i domini su
   internet."*
5. Se sei un account **Team/Enterprise** e il dropdown e' bloccato:
   - L'Owner deve abilitarlo da **Admin Settings -> Capabilities -> Network
     access** (vedi rischi piu' sotto).
6. Riavvia Claude Desktop dopo le modifiche, per sicurezza.
7. Apri (o seleziona) la **cartella di lavoro** del progetto in Cowork. Senza
   cartella il plugin non puo' leggere `waba_config.json`.

## Test rapido — la skill lo fa per te

Dopo aver applicato le impostazioni, chiedi a Claude:

> Esegui il check ambiente del plugin Ivan Lao WhatsApp Broadcaster.

La skill esegue `scripts/env_check.py` nella sandbox. L'esito atteso:

```
[OK ] ambiente               : sandbox Cowork
[OK ] python_version         : 3.10+ / 3.12+
[OK ] pip                    : /usr/local/bin/pip
[OK ] curl                   : /usr/bin/curl
[OK ] lib_requests           : x.y.z
[OK ] lib_openpyxl           : x.y.z
[OK ] lib_phonenumbers       : x.y.z
[OK ] network_graph_api      : HTTP 4xx  -> Sandbox raggiunge graph.facebook.com.
```

Un HTTP **400/401** sul check di rete e' normale: significa che la chiamata
arriva a Meta ma manca un token valido. L'importante e' che **non sia 403
con `blocked-by-allowlist`** (proxy Cowork che blocca il dominio).

## Errori comuni e soluzione

| Sintomo nel check | Causa | Cosa fare |
|-------------------|-------|-----------|
| `network_graph_api: 403 blocked-by-allowlist` | Allowlist Cowork ristretta | Settings -> Funzionalita' -> Lista domini = **Tutti i domini** |
| `network_graph_api: rete sandbox disabilitata` | Network egress OFF | Abilita **Consenti traffico di rete in uscita** |
| `network_graph_api: DNS bloccato` | Sandbox isolata | Stesso fix di sopra |
| `lib_requests: non installata` | Setup non eseguito | La skill esegue automaticamente `pip install --break-system-packages requests openpyxl phonenumbers` |
| `ambiente: locale (...)` | Stai eseguendo fuori da Cowork | Apri Claude Desktop e attiva Cowork |
| Claude propone Chrome MCP invece di Bash | Tool Bash non disponibile o skill non triggerata | Settings -> Esecuzione codice cloud = ON; invoca la skill esplicitamente |

## Test corretto vs test sbagliato

Test **sbagliato** (terminale locale del Mac):

```
emanuele@Mac % curl -v https://graph.facebook.com
# Connessione OK, ma e' il Mac, NON la sandbox Cowork.
```

Test **corretto** (sandbox Cowork - lo esegue Claude tramite Bash tool):

```
[Ivan Lao WhatsApp Broadcaster] Esegui nella sandbox:
curl -v https://graph.facebook.com 2>&1 | head -20
```

Il prompt deve essere quello della sandbox (`jolly-...@...` o simile), non
`utente@Mac`.

## Privacy e sicurezza

Aprire la sandbox a **"Tutti i domini"** amplia la superficie. Anthropic
mostra l'avviso *"rischi per la sicurezza"*. Indicazioni operative:

- Mantieni `waba_config.json` fuori da Git (`.gitignore` gia' presente nel
  plugin).
- Non incollare token o segreti in chat: lascia che la skill li legga dal file.
- Per ambienti regolati (account Enterprise) preferisci una **allowlist
  ristretta** che includa solo:
  - `graph.facebook.com`
  - `lookaside.fbsbx.com` (download media WhatsApp)
  - eventuali domini dei media template (`bot.laoivan.com`, ecc.)

## Se la sandbox del cliente resta bloccata

Account Team/Enterprise con policy IT restrittive potrebbero non poter
modificare le impostazioni: in quel caso il plugin instrada il cliente verso
`fallback-alternative.md` (Make / n8n / Google Apps Script / terminale locale /
Postman) e propone il workflow piu' adatto al volume di invii.

---

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
