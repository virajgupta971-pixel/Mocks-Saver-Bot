# Copyright github.com/devgaganin
# no part of this code/edits is allowed to use for commercial / sale purposes

import os
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from telethon import TelegramClient, events, Button

# Logging enable karein taaki Railway logs mein pata chale bot kahan hai
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────
# CONFIGURATION (Railway Environment Variables)
# ─────────────────────────────────────────────
API_ID = int(os.getenv("API_ID", "1234567"))          
API_HASH = os.getenv("API_HASH", "your_api_hash")     
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")  
COOKIES = os.getenv("COOKIES", "your_cookies_here")   

bot = TelegramClient("olive_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# User states track karne ke liye
user_states = {}

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cookie": COOKIES,
    "Host": "u1.oliveboard.in",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}

BASE_URIS = {
    "ibpsclerk_pre_25":  "https://u1.oliveboard.in/exams/tests/?c=ibpsclerk&testid={test_id}",
    "ibpsclerk_main_25": "https://u1.oliveboard.in/exams/tests/?c=ibpsclerkmain&testid={test_id}",
    "ibpsclerk_pre_26":  "https://u1.oliveboard.in/exams/tests/?c=ibpsclerk26&testid={test_id}",
    "ibpsclerk_main_26": "https://u1.oliveboard.in/exams/tests/?c=ibpsclerkmain26&testid={test_id}",

    "rrbpo_pre_25":  "https://u1.oliveboard.in/exams/tests/?c=rrbpo&testid={test_id}",
    "rrbpo_main_25": "https://u1.oliveboard.in/exams/tests/?c=rrbpomain&testid={test_id}",
    "rrbpo_pre_26":  "https://u1.oliveboard.in/exams/tests/?c=rrbpo26&testid={test_id}",
    "rrbpo_main_26": "https://u1.oliveboard.in/exams/tests/?c=rrbpomain26&testid={test_id}",

    "rrbclerk_pre_25":  "https://u1.oliveboard.in/exams/tests/?c=rrbclerk&testid={test_id}",
    "rrbclerk_main_25": "https://u1.oliveboard.in/exams/tests/?c=rrbclerkmain&testid={test_id}",
    "rrbclerk_pre_26":  "https://u1.oliveboard.in/exams/tests/?c=rrbclerk26&testid={test_id}",
    "rrbclerk_main_26": "https://u1.oliveboard.in/exams/tests/?c=rrbclerkmain26&testid={test_id}",

    "sbiclerk_main_25": "https://u1.oliveboard.in/exams/tests/?c=sbiclerkmain&testid={test_id}",
    "sbiclerk_main_26": "https://u1.oliveboard.in/exams/tests/?c=sbiclerkmain26&testid={test_id}",
    "sbipo_main_25":    "https://u1.oliveboard.in/exams/tests/?c=sbipomain&testid={test_id}",
    "sbipo_main_26":    "https://u1.oliveboard.in/exams/tests/?c=sbipomain26&testid={test_id}",
}

@bot.on(events.NewMessage(pattern=r"^/fetch$"))
async def fetch_menu(event):
    buttons = [
        [Button.inline("📘 IBPS Clerk Pre '25", data="ibpsclerk_pre_25"), Button.inline("📙 IBPS Clerk Mains '25", data="ibpsclerk_main_25")],
        [Button.inline("📘 IBPS Clerk Pre '26", data="ibpsclerk_pre_26"), Button.inline("📙 IBPS Clerk Mains '26", data="ibpsclerk_main_26")],
        [Button.inline("📗 RRB PO Pre '25", data="rrbpo_pre_25"), Button.inline("📕 RRB PO Mains '25", data="rrbpo_main_25")],
        [Button.inline("📗 RRB PO Pre '26", data="rrbpo_pre_26"), Button.inline("📕 RRB PO Mains '26", data="rrbpo_main_26")],
        [Button.inline("📒 RRB Clerk Pre '25", data="rrbclerk_pre_25"), Button.inline("📓 RRB Clerk Mains '25", data="rrbclerk_main_25")],
        [Button.inline("📒 RRB Clerk Pre '26", data="rrbclerk_pre_26"), Button.inline("📓 RRB Clerk Mains '26", data="rrbclerk_main_26")],
        [Button.inline("💳 SBI Clerk Mains '25", data="sbiclerk_main_25"), Button.inline("💳 SBI Clerk Mains '26", data="sbiclerk_main_26")],
        [Button.inline("💰 SBI PO Mains '25", data="sbipo_main_25"), Button.inline("💰 SBI PO Mains '26", data="sbipo_main_26")],
    ]
    await event.respond("📂 **Select Exam:**", buttons=buttons)

@bot.on(events.CallbackQuery)
async def button_click(event):
    data = event.data.decode("utf-8")
    if data in BASE_URIS:
        user_states[event.sender_id] = data
        await event.edit(f"✅ Selected: **{data.upper()}**\n\n💬 Ab apna Test ID (number) type karke bhejein:")

@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_test_id(event):
    user_id = event.sender_id
    if user_id not in user_states:
        return  # Agar user ne exam select nahi kiya hai toh ye message ignore hoga

    text = event.text.strip()
    if text.startswith("/"):
        user_states.pop(user_id, None)
        return

    if not text.isdigit():
        await event.reply("⚠️ Kripya valid Test ID (sirf numbers) bhejein!")
        return

    exam = user_states.pop(user_id)
    test_id = text

    url = BASE_URIS[exam].format(test_id=test_id)
    file_name = f"exam_{exam}_{test_id}.html"
    file_sol_name = f"solution_exam_{exam}_{test_id}.html"

    prog = await event.respond("⏳ Extracting Questions…")
    
    try:
        session = requests.Session()
        session.headers.update(HEADERS)

        response = session.get(url, timeout=30)
        response.raise_for_status()

        if "login" in response.text.lower()[:2000]:
            await prog.edit("⚠️ Invalid/Expired Cookies! Railway variables mein COOKIES update karein.")
            return

        modified_html = modify_html(response.text)
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(modified_html)

        await prog.edit("📤 Uploading Question Paper…")
        await event.respond(f"📕 Exam: {exam}\n🆔 Test ID: {test_id}\n📂 Question Paper", file=file_name)

        # Auto Submit Test
        await prog.edit("🔄 Auto Submitting test…")
        ok = submit_test(session, url, test_id, exam)

        # Solution Page Request
        sol_url = f"https://u1.oliveboard.in/exams/solution/index3.php?c={exam.split('_')[0]}&testid={test_id}"
        
        await prog.edit("🔎 Fetching Solution…")
        sol_response = session.get(sol_url, timeout=30)
        sol_html = sol_response.text

        if not sol_html or len(sol_html) < 1000:
            await prog.edit("⚠️ Solution fetch nahi ho paya (Test submit nahi hua ya locked hai).")
            return

        mod_html = mody_html(sol_html)
        with open(file_sol_name, "w", encoding="utf-8") as file:
            file.write(mod_html)

        await prog.edit("📤 Uploading Solution…")
        await event.respond(f"📕 Exam: {exam}\n🆔 Test ID: {test_id}\n📂 Solution Paper", file=file_sol_name)
        await prog.delete()

    except Exception as e:
        await event.respond(f"❌ Error aagayi: {e}")
    finally:
        for f in (file_name, file_sol_name):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

def submit_test(session, url, test_id, exam_code):
    surl = "https://u1.oliveboard.in/exams/tests/p/submittestfull.cgi"
    clean_exam = exam_code.split('_')[0]
    
    post_headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://u1.oliveboard.in",
        "Referer": url,
        "X-Requested-With": "XMLHttpRequest",
    }
    
    q_val = str(test_id)
    raw_data = (
        f"data=%7B%22{q_val}001%22%3A%7B%22q%22%3A%22{q_val}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2201%3A30%3A00%22%2C%22end%22%3A%2201%3A29%3A58%22%7D%5D%2C%22o%22%3A%22%22%7D%7D"
        f"&uid=&qpi={test_id}&ppi=-1&lang=eqt&c={clean_exam}&source=web"
    )

    try:
        resp = session.post(surl, headers=post_headers, data=raw_data, timeout=30)
        return resp.status_code == 200
    except Exception:
        return False

def _rewrite_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    if not soup.find("base"):
        base_tag = soup.new_tag("base", href=base_url)
        if soup.head:
            soup.head.insert(0, base_tag)
            
    for tag in soup.find_all(["a", "img", "link", "script"]):
        if tag.has_attr("href") and not tag["href"].startswith(("http", "data:")):
            tag["href"] = urljoin(base_url, tag["href"])
        if tag.has_attr("src") and not tag["src"].startswith(("http", "data:")):
            tag["src"] = urljoin(base_url, tag["src"])
    return soup.prettify()

def modify_html(html):
    return _rewrite_links(html, "https://u1.oliveboard.in/exams/tests/")

def mody_html(html):
    return _rewrite_links(html, "https://u1.oliveboard.in/exams/solution/")

print("Bot started and running...")
bot.run_until_disconnected()
