from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv


HOME_URL = "https://itee.dieti.unina.it/index.php/it/"
ADMISSION_URL = "https://itee.dieti.unina.it/index.php/it/ammissione/ammissione"
STATE_FILE = Path(__file__).with_name("state.json")
USER_AGENT = "ITEE-change-monitor/1.0 (personal Telegram notifier)"


@dataclass(frozen=True)
class Watch:
    key: str
    title: str
    url: str
    selectors: tuple[str, ...]


WATCHES = (
    Watch("home_news", "Novità ITEE", HOME_URL, (".sp-module.news-cycle .sp-module-content", ".news-cycle", ".sp-module-content")),
    Watch("admission", "Pagina Ammissione", ADMISSION_URL, ("article.item-page", "#sp-component")),
)


def normalized_content(raw_html: str, watch: Watch) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    root: Tag | None = None
    for selector in watch.selectors:
        candidate = soup.select_one(selector)
        if isinstance(candidate, Tag):
            root = candidate
            break
    if root is None:
        raise ValueError(f"contenuto non trovato (selettori: {', '.join(watch.selectors)})")

    for unwanted in root.select("script, style, noscript, .article-info, .icons, .pager, .print-icon, .email-icon"):
        unwanted.decompose()

    lines: list[str] = []
    for element in root.select("h1, h2, h3, h4, p, li, table tr, a[href]"):
        text = " ".join(element.get_text(" ", strip=True).split())
        if not text or text.lower() in {"leggi tutto...", "read more..."}:
            continue
        if element.name == "a":
            href = urljoin(watch.url, element.get("href", ""))
            line = f"{text} -> {href}" if href and not href.startswith("javascript:") else text
        else:
            line = text
        if not lines or lines[-1] != line:
            lines.append(line)

    if not lines:
        text = "\n".join(" ".join(x.split()) for x in root.get_text("\n").splitlines() if x.strip())
        return text
    return "\n".join(lines)


def fetch(watch: Watch, timeout: int) -> str:
    response = requests.get(watch.url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return normalized_content(response.text, watch)


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Impossibile leggere {path}: {exc}") from exc


def save_state(path: Path, state: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def change_excerpt(before: str, after: str, limit: int = 2500) -> str:
    changes = list(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=1))[2:]
    useful = [line for line in changes if line.startswith(("+", "-"))]
    result = "\n".join(useful) or "Il contenuto della pagina è cambiato."
    return result[:limit] + ("\n…" if len(result) > limit else "")


def send_telegram(token: str, chat_id: str, message: str, timeout: int) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram ha rifiutato il messaggio: {payload}")


def run_check(token: str, chat_id: str, state_path: Path, timeout: int, notify_first: bool) -> int:
    state = load_state(state_path)
    next_state = dict(state)
    failures = 0

    for watch in WATCHES:
        try:
            content = fetch(watch, timeout)
            current_hash = digest(content)
            old = state.get(watch.key)
            changed = old is not None and old.get("hash") != current_hash

            if changed:
                excerpt = change_excerpt(old.get("content", ""), content)
                message = f"🔔 Aggiornamento: {watch.title}\n\n{excerpt}\n\n{watch.url}"
                send_telegram(token, chat_id, message, timeout)
                logging.info("Cambiamento notificato: %s", watch.title)
            elif old is None and notify_first:
                send_telegram(token, chat_id, f"✅ Monitoraggio attivato: {watch.title}\n{watch.url}", timeout)

            next_state[watch.key] = {"hash": current_hash, "content": content, "url": watch.url}
        except Exception as exc:
            failures += 1
            logging.error("Controllo fallito per %s: %s", watch.title, exc)

    if next_state != state:
        save_state(state_path, next_state)
    return 1 if failures else 0


def telegram_chat_ids(token: str, timeout: int) -> list[tuple[str, str]]:
    response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=timeout)
    response.raise_for_status()
    found: dict[str, str] = {}
    for update in response.json().get("result", []):
        chat = (update.get("message") or update.get("channel_post") or {}).get("chat", {})
        if "id" in chat:
            label = chat.get("title") or chat.get("username") or chat.get("first_name") or "senza nome"
            found[str(chat["id"])] = label
    return list(found.items())


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Monitora le pagine ITEE e avvisa via Telegram.")
    parser.add_argument("--once", action="store_true", help="esegue un solo controllo")
    parser.add_argument("--show-chat-id", action="store_true", help="mostra gli ID delle chat che hanno scritto al bot")
    parser.add_argument("--notify-first", action="store_true", help="invia conferma anche al primo avvio")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
    if not token:
        parser.error("TELEGRAM_BOT_TOKEN non configurato nel file .env")
    if args.show_chat_id:
        chats = telegram_chat_ids(token, timeout)
        if not chats:
            print("Nessuna chat trovata: apri il bot su Telegram, premi Avvia e scrivi un messaggio.")
        for found_id, label in chats:
            print(f"{found_id}\t{label}")
        return 0
    if not chat_id:
        parser.error("TELEGRAM_CHAT_ID non configurato nel file .env")

    interval = max(60, int(os.getenv("CHECK_INTERVAL_MINUTES", "30")) * 60)
    while True:
        exit_code = run_check(token, chat_id, STATE_FILE, timeout, args.notify_first)
        if args.once:
            return exit_code
        logging.info("Prossimo controllo tra %s minuti", interval // 60)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
