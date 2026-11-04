# Copyright github.com/devgaganin
# no part of this code/edits is allowed to use for commercial / sale purposes

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from telethon import TelegramClient, events

# ─────────────────────────────────────────────
# CONFIGURATION (Railway Environment Variables)
# ─────────────────────────────────────────────
API_ID = int(os.getenv("API_ID", "1234567"))          
API_HASH = os.getenv("API_HASH", "your_api_hash")     
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")  
COOKIES = os.getenv("COOKIES", "your_cookies_here")   

# ─────────────────────────────────────────────
# Initialize the Telethon client
# ─────────────────────────────────────────────
bot = TelegramClient("olive_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Handle /start command"""
    await event.reply(
        "Welcome to the Mock Extractor Bot!\n\n"
        "Send /fetch exam testid for oliveboard\n\n"
        "Example: /fetch sbiclerkmain25 2\n"
        "Example: /fetch sbiclerkmain26 2\n\n"
        "Powered by Team SPY"
    )


# ─────────────────────────────────────────────
# OLIVEBOARD — headers
# ─────────────────────────────────────────────
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cookie": COOKIES,
    "Host": "u1.oliveboard.in",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Yahan aap 2025 aur 2026 ke alag-alag codes define kar sakte hain
BASE_URIS = {
    # SSC & Railway
    "cgl1":        "https://u1.oliveboard.in/exams/tests/?c=ssc2019&testid={test_id}",
    "chsl":        "https://u1.oliveboard.in/exams/tests/?c=chsl&testid={test_id}",
    "ntpc1":       "https://u1.oliveboard.in/exams/tests/?c=ntpc1&os=1&testid={test_id}",
    
    # Banking - 2025 & 2026 Mains Examples
    "sbiclerkmain25": "https://u1.oliveboard.in/exams/tests/?c=sbiclerkmain&testid={test_id}",
    "sbiclerkmain26": "https://u1.oliveboard.in/exams/tests/?c=sbiclerkmain26&testid={test_id}",
    "sbipomain25":    "https://u1.oliveboard.in/exams/tests/?c=sbipomain&testid={test_id}",
    "sbipomain26":    "https://u1.oliveboard.in/exams/tests/?c=sbipomain26&testid={test_id}",
    "ibpspomain25":   "https://u1.oliveboard.in/exams/tests/?c=ibpspomain&testid={test_id}",
    "ibpspomain26":   "https://u1.oliveboard.in/exams/tests/?c=ibpspomain26&testid={test_id}",
}


# ─────────────────────────────────────────────
# /fetch handler
# ─────────────────────────────────────────────
@bot.on(events.NewMessage(pattern=r"/fetch (\w+) (\d+)"))
async def fetch_exam(event):
    exam    = event.pattern_match.group(1).lower()
    test_id = event.pattern_match.group(2)

    if exam not in BASE_URIS:
        await event.respond(
            "Invalid exam type! Supported types are: " + ", ".join(BASE_URIS.keys())
        )
        return

    url = BASE_URIS[exam].format(test_id=test_id)

    # Alag-alag saal ke hisaab se file names clear rahenge
    file_name     = f"exam_{exam}_{test_id}.html"
    file_sol_name = f"solution_exam_{exam}_{test_id}.html"

    try:
        # ── 1. Download question paper ─────────────────────
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        modified_html = modify_html(response.text, url)
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(modified_html)

        prog = await bot.send_message(event.chat_id, "Extracting Questions…")

        await prog.edit("Uploading Test Papers…")
        await event.respond(
            f"📕 Exam: {exam}\n"
            f"🆔 Test ID: {test_id}\n"
            f"📂 Type: Question Paper\n\n"
            "Powered by Team SPY",
            file=file_name,
        )
        
        # ── 2. Submit the test ────────────────────────────
        await prog.edit("Auto Submitting the test…")
        ok = submit_test(url, test_id, exam)

        if not ok:
            await prog.edit(
                "⚠️ Test submission failed (invalid/expired cookies or already submitted). "
                "Skipping solution fetch."
            )
            return

        await prog.edit("Test Submitted Successfully…")

        # ── 3. Fetch solution ────────────────────────────
        sol_url = url.replace(
            "https://u1.oliveboard.in/exams/tests/",
            "https://u1.oliveboard.in/exams/solution/index3.php",
        )
        print("Solution URL:", sol_url)

        await prog.edit("Trying to fetch the solution…")
        sol_html = fetch_solution(sol_url)

        if not sol_html or "login" in sol_html.lower()[:2000] and "solution" not in sol_html.lower():
            await prog.edit("⚠️ Could not fetch solution (login page returned).")
            return

        mod_html = mody_html(sol_html, sol_url)
        with open(file_sol_name, "w", encoding="utf-8") as file:
            file.write(mod_html)

        await prog.edit("Uploading Solution…")
        await event.respond(
            f"📕 Exam: {exam}\n"
            f"🆔 Test ID: {test_id}\n"
            f"📂 Type: Solution\n\n"
            "Powered by Team SPY",
            file=file_sol_name,
        )
        await prog.delete()

    except requests.exceptions.RequestException as e:
        await event.respond(f"Network error while fetching test details: {e}")
    except Exception as e:
        await event.respond(f"Unexpected error: {e}")
    finally:
        for f in (file_name, file_sol_name):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass


# ─────────────────────────────────────────────
# Submit the test
# ─────────────────────────────────────────────
def submit_test(url, test_id, exam):
    surl = "https://u1.oliveboard.in/exams/tests/p/submittestfull.cgi"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": COOKIES,
        "Host": "u1.oliveboard.in",
        "Origin": "https://u1.oliveboard.in",
        "Referer": url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    q_value = str(test_id)

    raw_data = (
        f"data=%7B%22{q_value}001%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2201%3A30%3A00%22%2C%22end%22%3A%2201%3A29%3A58%22%7D%5D%2C%22o%22%3A%22%22%7D%2C"
        f"%22{q_value}002%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2200%3A59%3A57%22%2C%22end%22%3A%2200%3A59%3A53%22%7D%5D%2C%22o%22%3A%221%22%7D%2C"
        f"%22{q_value}003%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2200%3A59%3A53%22%2C%22end%22%3A%2200%3A59%3A47%22%7D%5D%2C%22o%22%3A%22%22%7D%2C"
        f"%22{q_value}004%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2200%3A59%3A47%22%2C%22end%22%3A%2200%3A59%3A46%22%7D%2C%7B%22st%22%3A%2200%3A59%3A46%22%2C%22end%22%3A%2200%3A59%3A43%22%7D%5D%2C%22o%22%3A%22%22%7D%7D"
        f"&uid=&qpi={test_id}&ppi=-1&lang=eqt&c={exam}&source=web"
    )

    try:
        response = requests.post(surl, headers=headers, data=raw_data, timeout=30)
    except requests.exceptions.RequestException as e:
        print("Submit request failed:", e)
        return False

    if response.status_code != 200:
        return False

    body = response.text.strip().lower()
    if any(bad in body for bad in ("invalid", "error", "login", "expired", "not found")):
        return False

    return True


# ─────────────────────────────────────────────
# Fetch solution page
# ─────────────────────────────────────────────
def fetch_solution(url):
    headers = dict(HEADERS)
    try:
        response = requests.get(url, headers=headers, timeout=30)
        return response.text
    except requests.exceptions.RequestException as e:
        print("Solution fetch failed:", e)
        return None


# ─────────────────────────────────────────────
# HTML rewriting helpers
# ─────────────────────────────────────────────
DEFAULT_BASE_URL  = "https://u1.oliveboard.in/exams/tests/"
SOLUTION_BASE_URL = "https://u1.oliveboard.in/exams/solution/"


def _rewrite_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["a", "img", "link", "script"]):
        if tag.has_attr("href") and not tag["href"].startswith("http"):
            tag["href"] = urljoin(base_url, tag["href"])
        if tag.has_attr("src") and not tag["src"].startswith("http"):
            tag["src"] = urljoin(base_url, tag["src"])
    return soup.prettify()


def modify_html(html, full_url):
    return _rewrite_links(html, DEFAULT_BASE_URL)


def mody_html(html, full_url):
    return _rewrite_links(html, SOLUTION_BASE_URL)


# ─────────────────────────────────────────────
print("Bot started…")
bot.run_until_disconnected()
