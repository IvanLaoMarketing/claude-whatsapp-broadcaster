# Cartella DEMO — Ivan Lao WhatsApp Broadcaster

Questa cartella è un **esempio funzionante** della struttura consigliata per
gestire più clienti con la skill *Ivan Lao WhatsApp Broadcaster*.

> Ivan Lao Marketing Automation · laoivan.com

## Come è organizzata

```
DEMO - Ivan Lao WhatsApp Broadcaster/      ← la "cartella Cowork" (workspace)
├── waba_config.json                       ← CONFIGURAZIONE CONDIVISA
├── 01 - Cliente Alfa Srl/                 ← un cliente = una sottocartella
│   └── contatti-esempio.xlsx
├── 02 - Cliente Beta Spa/
│   └── contatti-esempio.xlsx
└── 03 - Cliente Gamma (configurazione dedicata)/
    ├── wa_broadcaster/
    │   └── waba_config.json               ← CONFIGURAZIONE DEDICATA (override)
    └── contatti-esempio.xlsx
```

## Le due posizioni della configurazione

La skill cerca `waba_config.json` in quest'ordine:

1. **Config di progetto** — dentro `<cartella cliente>/wa_broadcaster/`. Vale
   solo per quel cliente. È il caso di **Cliente Gamma**.
2. **Config condivisa** — `waba_config.json` nella **radice** di questa cartella.
   La ereditano **tutti** i clienti che non hanno una config propria. È il caso
   di **Cliente Alfa** e **Cliente Beta**.

Vince sempre la config di progetto, se presente. Così configuri gli account una
volta sola nella radice, e usi una config dedicata solo per i clienti che hanno
credenziali WABA proprie.

## Primo avvio

I due file `waba_config.json` di questa demo sono **modelli da compilare**:
contengono valori segnaposto e il campo `"_demo": true`. Quando apri questa
cartella con la skill, al primo avvio la skill **rileva la configurazione demo**
e ti **guida a inserire le credenziali WABA reali**. Dopo la compilazione il
campo `_demo` viene rimosso.

## Le liste contatti

Ogni cliente ha un `contatti-esempio.xlsx` che mostra il formato atteso:
colonne **Nome, Cognome, Telefono, Citta**. La skill aggiunge da sola le colonne
di log (`stato_invio`, `message_id`, `timestamp_invio`, `errore`).

La lista di *Cliente Alfa* contiene di proposito numeri scritti in **formati
diversi** (con e senza `+39`, con spazi) e un **numero duplicato**: serve a
mostrare che la skill normalizza i numeri in formato E.164 e invia una sola
volta per numero.

## Il campo `gruppo_account`

Nella config condivisa gli account hanno un campo facoltativo `gruppo_account`
(es. `Italia`, `Estero`): serve a **raggruppare** gli account quando sono molti.

---

Per la guida completa vedi **GUIDA-USO** nello starter kit.

*Ivan Lao WhatsApp Broadcaster — Ivan Lao Marketing Automation · laoivan.com*
