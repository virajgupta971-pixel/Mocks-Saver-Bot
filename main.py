# Copyright github.com/devgaganin # no part of this code/edits is allowed to use for commercial / sale purposes
import json
import logging
import os
from bs4 import BeautifulSoup
from telethon import TelegramClient, events
from urllib.parse import urljoin
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# ─────────────────────────────────────────────
# CONFIGURATION (Environment Variables)
# ─────────────────────────────────────────────
API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
COOKIES = os.getenv("COOKIES", "your_cookies_here")

# Initialize the Telethon client
bot = TelegramClient("olive_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Handle /start command"""
    await event.reply(
        "**Welcome to the Mock Extractor Bot!**\n\n"
        "Send `/fetch exam testid` for oliveboard\n\n"
        "**__Example: `/fetch rrbpo 1`__**\n\n"
        "__**Powered by Banking Aura**__"
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

# Base URIs for different exam types
BASE_URIS = {
    "cgl1": "https://u1.oliveboard.in/exams/tests/?c=ssc2019&testid={test_id}",
    "chsl": "https://u1.oliveboard.in/exams/tests/?c=chsl&testid={test_id}",
    "chsl2": "https://u1.oliveboard.in/exams/tests/?c=chsl2&testid={test_id}",
    "sscmts": "https://u1.oliveboard.in/exams/tests/?c=sscmts&testid={test_id}",
    "ntpc1": "https://u1.oliveboard.in/exams/tests/?c=ntpc1&os=1&testid={test_id}",
    "ntpc2": "https://u1.oliveboard.in/exams/tests/?c=ntpc2&os=1&testid={test_id}",
    "rrbalp1": "https://u1.oliveboard.in/exams/tests/?c=rrbalp1&os=1&testid={test_id}",
    "rrbalp2": "https://u1.oliveboard.in/exams/tests/?c=rrbalp2&os=1&testid={test_id}",
    "rrbgrpd": "https://u1.oliveboard.in/exams/tests/?c=rrbgrpd&os=1&testid={test_id}",
    "ibpspo": "https://u1.oliveboard.in/exams/tests/?c=ibpspo&testid={test_id}",
    "ibpsclerk": "https://u1.oliveboard.in/exams/tests/?c=ibpsclerk&testid={test_id}",
    "sbipo": "https://u1.oliveboard.in/exams/tests/?c=sbipo&testid={test_id}",
    "sbiclerk": "https://u1.oliveboard.in/exams/tests/?c=sbiclerk&testid={test_id}",
    "rrbpo": "https://u1.oliveboard.in/exams/tests/?c=ibpsrrbscp&testid={test_id}",
    "rrbclerk": "https://u1.oliveboard.in/exams/tests/?c=ibpsrrbscp&testid={test_id}",
    "rrbpomain": "https://u1.oliveboard.in/exams/tests/?c=rrbpomain&testid={test_id}",
    "rrbclerkmain": "https://u1.oliveboard.in/exams/tests/?c=rrbclerkmain&testid={test_id}",
}

# ─────────────────────────────────────────────
# /fetch handler
# ─────────────────────────────────────────────
@bot.on(events.NewMessage(pattern=r"/fetch (\w+) (\d+)"))
async def fetch_exam(event):
    exam = event.pattern_match.group(1).lower()
    test_id = event.pattern_match.group(2)
    
    if exam not in BASE_URIS:
        await event.respond("Invalid exam type! Supported types are: " + ", ".join(BASE_URIS.keys()))
        return

    url = BASE_URIS[exam].format(test_id=test_id)
    file_name = f"exam_{exam}_{test_id}.html"
    file_sol_name = f"solution_exam_{exam}_{test_id}.html"

    try:
        prog = await bot.send_message(event.chat_id, "Extracting Questions & Enforcing Timers...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
        modified_html = modify_html(html_content, url)
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(modified_html)

        await prog.edit("Uploading Test Papers...")
        await event.respond(
            f"**📕 Exam Name: {exam}**\n"
            f"**🆔 Test ID: {test_id}**\n"
            f"**✅ Type: Question (With Native Timer Support)**\n\n"
            "__**Powered by @Dark_V1rus**__",
            file=file_name,
        )
        
        await prog.edit("Auto Submitting the test...")
        submit_test(url, test_id, exam)
        
        await prog.edit("Test Submitted Successfully...")
        t = url.replace("https://u1.oliveboard.in/exams/tests/", "https://u1.oliveboard.in/exams/solution/index3.php")
        
        k = fetch_solution(t)
        if k:
            await prog.edit("Trying to fetch the solution...")
            mod_html = mody_html(k, url)
            with open(file_sol_name, "w", encoding="utf-8") as file:
                file.write(mod_html)

            await prog.edit("Uploading Solution...")
            await event.respond(
                f"**📕 Exam Name: {exam}**\n"
                f"**🆔 Test ID: {test_id}**\n"
                f"**✅ Type: Solution**\n\n"
                "__**Powered by Banking Aura@Dark_V1rus**__",
                file=file_sol_name,
            )
        await prog.delete()
        
    except requests.exceptions.RequestException as e:
        await event.respond(f"Failed to fetch the test details: {e}")
    except Exception as e:
        await event.respond(f"An unexpected error occurred: {e}")
    finally:
        for f in [file_name, file_sol_name]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

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
    }
    q_value = f"{test_id}001"
    raw_data = f"data=%7B%22{q_value}001%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2201%3A30%3A00%22%2C%22end%22%3A%2201%3A29%3A58%22%7D%5D%2C%22o%22%3A%22%22%7D%7D&uid=&qpi={test_id}&ppi=-1&lang=eqt&c={exam}&source=web"
    try:
        requests.post(surl, headers=headers, data=raw_data, timeout=15)
    except Exception:
        pass

def fetch_solution(url):
    headers = {
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
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        return response.text
    except Exception:
        return None

DEFAULT_BASE_URL = "https://u1.oliveboard.in/exams/tests/"
SOLUTION_BASE_URL = "https://u1.oliveboard.in/exams/solution/"
WATERMARK_TEXT = "BANKING AURA"

WATERMARK_HTML = """<style> #ba-watermark{position:fixed;inset:0;z-index:2147483000;pointer-events:none;overflow:hidden;display:flex;align-items:center;justify-content:center;user-select:none} #ba-watermark span{font-family:Arial,Helvetica,sans-serif;font-weight:800;font-size:9vw;letter-spacing:.05em;white-space:nowrap;color:rgba(0,0,0,.07);transform:rotate(-30deg)} @media print{#ba-watermark span{color:rgba(0,0,0,.12)}} </style> <div id="ba-watermark" aria-hidden="true"><span>%s</span></div> """ % WATERMARK_TEXT

# Injection script targeting Oliveboard's detected timer functions: timerActivate & checkTimer
SECTION_TIMER_INJECT_SCRIPT = """<script>
window.addEventListener('DOMContentLoaded', (event) => {
    console.log("Banking Aura: Oliveboard Sectional Timer Enforcer Active");
    window.onbeforeunload = null;

    // Periodically hook into Oliveboard's native timer and section functions
    setInterval(() => {
        try {
            if (typeof window.timerActivate === 'function') {
                window.timerActivate();
            }
            if (typeof window.checkTimer === 'function') {
                window.checkTimer();
            }
        } catch (e) {
            // Suppress background sync errors
        }
    }, 1000);
});
</script>
"""

def finalize_html(soup):
    for a in soup.find_all("a"):
        if a.has_attr("onclick"):
            a["href"] = "javascript:void(0)"
        a.attrs.pop("target", None)
        
    if soup.head:
        soup.head.append(BeautifulSoup(SECTION_TIMER_INJECT_SCRIPT, "html.parser"))
        
    if soup.body is not None and not soup.find(id="ba-watermark"):
        soup.body.append(BeautifulSoup(WATERMARK_HTML, "html.parser"))
    return soup.prettify()

def modify_html(html, full_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["a", "img", "link", "script"]):
        if tag.has_attr("href") and not tag["href"].startswith("http"):
            tag["href"] = urljoin(DEFAULT_BASE_URL, tag["href"])
        if tag.has_attr("src") and not tag["src"].startswith("http"):
            tag["src"] = urljoin(DEFAULT_BASE_URL, tag["src"])
    return finalize_html(soup)

def mody_html(html, full_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["a", "img", "link", "script"]):
        if tag.has_attr("href") and not tag["href"].startswith("http"):
            tag["href"] = urljoin(SOLUTION_BASE_URL, tag["href"])
        if tag.has_attr("src") and not tag["src"].startswith("http"):
            tag["src"] = urljoin(SOLUTION_BASE_URL, tag["src"])
    return finalize_html(soup)

print("Bot started...")
bot.run_until_disconnected()
