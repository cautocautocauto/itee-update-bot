# ITEE Update Bot

Controlla ogni 15 minuti:

- la sezione News della homepage ITEE;
- il contenuto della pagina Ammissione, compresi testi e link.
- la sezione Scorrimento graduatorie della pagina Unina dedicata al 42° ciclo;
- la sezione Modalità d'iscrizione della stessa pagina Unina.

Quando rileva una modifica invia su Telegram le parti aggiunte o rimosse e il collegamento alla pagina.

## Esecuzione

Il controllo è eseguito esclusivamente da GitHub Actions tramite `.github/workflows/monitor.yml`. Non richiede un computer acceso o un processo locale.

Le credenziali sono conservate nei repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Lo stato precedente delle pagine viene conservato nella cache di GitHub Actions. Il primo controllo crea lo snapshot iniziale senza inviare messaggi.
