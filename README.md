# Bot Telegram per aggiornamenti ITEE

Il bot controlla:

- la sezione **News** della [homepage ITEE](https://itee.dieti.unina.it/index.php/it/);
- tutto il contenuto dell'articolo [Ammissione](https://itee.dieti.unina.it/index.php/it/ammissione/ammissione), inclusi testi e link.

Al primo avvio salva la situazione corrente senza inviare vecchie notizie. Dai controlli successivi manda su Telegram un breve riepilogo delle righe aggiunte o rimosse.

## 1. Creare il bot Telegram

1. In Telegram apri **@BotFather**.
2. Invia `/newbot`, scegli nome e username, poi copia il token ricevuto.
3. Apri il nuovo bot, premi **Avvia** e mandagli un messaggio qualsiasi.

## 2. Configurare il progetto (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Apri `.env`, incolla il token in `TELEGRAM_BOT_TOKEN`, quindi trova il chat ID:

```powershell
python bot.py --show-chat-id
```

Copia il numero mostrato in `TELEGRAM_CHAT_ID` dentro `.env`.

## 3. Avviare

Prova un singolo controllo e ricevi una conferma:

```powershell
python bot.py --once --notify-first
```

Poi lascia il monitor in esecuzione (controllo ogni 30 minuti):

```powershell
python bot.py
```

Puoi cambiare la frequenza modificando `CHECK_INTERVAL_MINUTES` nel file `.env` (minimo 1 minuto). Per tenerlo sempre attivo è possibile eseguirlo su un piccolo server oppure pianificare `python bot.py --once` con l'Utilità di pianificazione di Windows.

## Esecuzione online con GitHub Actions

Il file `.github/workflows/monitor.yml` esegue automaticamente il controllo online due volte all'ora, anche quando il computer è spento.

Nel repository GitHub vai in **Settings → Secrets and variables → Actions** e crea questi due repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Non caricare il file `.env` su GitHub. Dopo aver aggiunto i secrets, apri **Actions → Controllo aggiornamenti ITEE → Run workflow** per inizializzare lo snapshot. I controlli successivi verranno eseguiti automaticamente.

## Note

- `state.json` contiene l'ultimo snapshot e viene creato automaticamente.
- Se un controllo di rete fallisce, lo snapshot precedente resta valido e il bot riprova al ciclo seguente.
- Non pubblicare mai `.env`: contiene il token segreto del bot.
