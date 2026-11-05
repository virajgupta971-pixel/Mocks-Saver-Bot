# Copyright github.com/devgaganin
# no part of this code/edits is allowed to use for commercial / sale purposes

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
# CONFIGURATION (Railway Environment Variables)
# ─────────────────────────────────────────────
API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
COOKIES = os.getenv("COOKIES", "your_cookies_here")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Telegram User ID

# ─────────────────────────────────────────────
# Initialize the Telethon client
# ─────────────────────────────────────────────
bot = TelegramClient("olive_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Handle /start command"""
    await event.reply(
        "**Welcome to the Mock Extractor Bot!**\n\n"
        "Send `/fetch exam testid` for oliveboard\n\n"
        "**__Example: `/fetch rrbposecpre 1`__**\n\n"
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

# Comprehensive Category Slugs
BASE_URIS = {
    # SSC & Railway
    "cgl1": "https://u1.oliveboard.in/exams/tests/?c=ssc2019&testid={test_id}",
    "chsl": "https://u1.oliveboard.in/exams/tests/?c=chsl&testid={test_id}",
    "chsl2": "https://u1.oliveboard.in/exams/tests/?c=chsl2&testid={test_id}",
    "sscmts": "https://u1.oliveboard.in/exams/tests/?c=sscmts&testid={test_id}",
    "ntpc1": "https://u1.oliveboard.in/exams/tests/?c=ntpc1&os=1&testid={test_id}",
    "ntpc2": "https://u1.oliveboard.in/exams/tests/?c=ntpc2&os=1&testid={test_id}",
    "rrbalp1": "https://u1.oliveboard.in/exams/tests/?c=rrbalp1&os=1&testid={test_id}",
    "rrbalp2": "https://u1.oliveboard.in/exams/tests/?c=rrbalp2&os=1&testid={test_id}",
    "rrbgrpd": "https://u1.oliveboard.in/exams/tests/?c=rrbgrpd&os=1&testid={test_id}",
    # RRB PO & Clerk (Prelims, Mains, Sectionals & Pre-Sectionals)
    "rrbposecpre": "https://u1.oliveboard.in/exams/tests/?c=rrbposecpre&testid={test_id}",
    "rrbpo": "https://u1.oliveboard.in/exams/tests/?c=ibpsrrbscp&testid={test_id}",
    "rrbclerk": "https://u1.oliveboard.in/exams/tests/?c=ibpsrrbscp&testid={test_id}",
    "rrbpomain": "https://u1.oliveboard.in/exams/tests/?c=rrbpomain&testid={test_id}",
    "rrbclerkmain": "https://u1.oliveboard.in/exams/tests/?c=rrbclerkmain&testid={test_id}",
    "rrbposectional": "https://u1.oliveboard.in/exams/tests/?c=rrbposectional&testid={test_id}",
    "rrbclerksectional": "https://u1.oliveboard.in/exams/tests/?c=rrbclerksectional&testid={test_id}",
    # IBPS PO & Clerk
    "ibpspo": "https://u1.oliveboard.in/exams/tests/?c=ibpspo&testid={test_id}",
    "ibpspomain": "https://u1.oliveboard.in/exams/tests/?c=ibpspomain&testid={test_id}",
    "ibpsclerk": "https://u1.oliveboard.in/exams/tests/?c=ibpsclerk&testid={test_id}",
    "ibpsclerkmain": "https://u1.oliveboard.in/exams/tests/?c=ibpsclerkmain&testid={test_id}",
    # SBI PO & Clerk
    "sbipo": "https://u1.oliveboard.in/exams/tests/?c=sbipo&testid={test_id}",
    "sbipomain": "https://u1.oliveboard.in/exams/tests/?c=sbipomain&testid={test_id}",
    "sbiclerk": "https://u1.oliveboard.in/exams/tests/?c=sbiclerk&testid={test_id}",
    "sbiclerkmain": "https://u1.oliveboard.in/exams/tests/?c=sbiclerkmain&testid={test_id}",
}


# ─────────────────────────────────────────────
# /fetch handler
# ─────────────────────────────────────────────
@bot.on(events.NewMessage(pattern=r"/fetch (\w+) (\d+)"))
async def fetch_exam(event):
    # Owner restriction check
    if OWNER_ID and event.sender_id != OWNER_ID:
        await event.reply("Not allowed")
        return

    exam = event.pattern_match.group(1).lower()
    test_id = event.pattern_match.group(2)

    if exam not in BASE_URIS:
        await event.respond(
            "Invalid exam type! Supported types are:\n" + ", ".join(BASE_URIS.keys())
        )
        return

    url = BASE_URIS[exam].format(test_id=test_id)

    file_name = f"exam_{exam}_{test_id}.html"
    file_sol_name = f"solution_exam_{exam}_{test_id}.html"

    try:
        prog = await bot.send_message(event.chat_id, "Fetching Question Paper…")

        # ── 1. Download Question Paper ──
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        if len(response.text) < 500 or "login" in response.text.lower()[:1000]:
            await prog.edit(
                f"⚠️ Received blank or login page for exam `{exam}` with Test ID `{test_id}`.\n"
                "Possible reasons:\n"
                "1. Invalid Test ID for this specific exam category.\n"
                "2. Expired or invalid COOKIES.\n"
                "3. Test requires active purchase/subscription on your account."
            )
            return

        modified_html = modify_html(response.text, url)
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(modified_html)

        await prog.edit("Uploading Test Papers…")
        await event.respond(
            f"**📕 Exam Name: {exam}**\n"
            f"**🆔 Test ID: {test_id}**\n"
            f"**🥹 Type: Question**\n\n"
            "__**Powered by Banking Aura**__",
            file=file_name,
        )

        # ── 2. Fetch Solution ────────────────────────────
        sol_url = url.replace(
            "https://u1.oliveboard.in/exams/tests/",
            "https://u1.oliveboard.in/exams/solution/index3.php",
        )
        print("Solution URL:", sol_url)

        await prog.edit("Trying to fetch the solution…")
        sol_html = fetch_solution(sol_url)

        if not sol_html or len(sol_html) < 500 or (
            "login" in sol_html.lower()[:2000] and "solution" not in sol_html.lower()
        ):
            await prog.edit(
                "⚠️ Could not fetch solution (page is blank or returned login screen)."
            )
            return

        mod_html = mody_html(sol_html, sol_url)
        with open(file_sol_name, "w", encoding="utf-8") as file:
            file.write(mod_html)

        await prog.edit("Uploading Solution…")
        await event.respond(
            f"**📕 Exam Name: {exam}**\n"
            f"**🆔 Test ID: {test_id}**\n"
            f"**🥹 Type: Solution**\n\n"
            "__**Powered by Banking Aura**__",
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
# Fetch solution page
# ─────────────────────────────────────────────
def fetch_solution(url):
    headers = dict(HEADERS)
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print("Solution fetch status:", response.status_code)
        return response.text
    except requests.exceptions.RequestException as e:
        print("Solution fetch failed:", e)
        return None


# ─────────────────────────────────────────────
# HTML rewriting helpers (Robust Dynamic Sectional Timer & Locking Engine)
# ─────────────────────────────────────────────
DEFAULT_BASE_URL = "https://u1.oliveboard.in/exams/tests/"
SOLUTION_BASE_URL = "https://u1.oliveboard.in/exams/solution/"

WATERMARK_TEXT = "Banking Aura"
WATERMARK_HTML = (
    """<style>
#ba-watermark{position:fixed;inset:0;z-index:2147483000;pointer-events:none;overflow:hidden;display:flex;align-items:center;justify-content:center;user-select:none}
#ba-watermark span{font-family:Arial,Helvetica,sans-serif;font-weight:800;font-size:9vw;letter-spacing:.05em;white-space:nowrap;color:rgba(0,0,0,.07);transform:rotate(-30deg)}
@media print{#ba-watermark span{color:rgba(0,0,0,.12)}}
</style>
<div id="ba-watermark" aria-hidden="true"><span>%s</span></div>
"""
    % WATERMARK_TEXT
)

# Robust Dynamic Engine matching Oliveboard Interface
EXTRA_INJECT_SCRIPT = """<script type="text/javascript">
(function() {
    // 1. Block beforeunload popup
    window.onbeforeunload = null;
    const originalAddEventListener = window.addEventListener;
    window.addEventListener = function(type, listener, options) {
        if (type === 'beforeunload') return;
        return originalAddEventListener.call(window, type, listener, options);
    };

    // 2. Exact Sectional Timing & Locking Synchronization
    window.addEventListener('load', function() {
        setTimeout(function() {
            // Pick up exact test parameters or intelligently fallback
            window.secList = (typeof secList !== 'undefined' && Array.isArray(secList) && secList.length > 0) ? secList : ['Reasoning', 'Quantitative Aptitude'];
            window.secTracker = (typeof secTracker !== 'undefined' && Array.isArray(secTracker) && secTracker.length > 0) ? secTracker : [35, 35];
            
            // Handle secTimes mapping properly
            if (typeof secTimes !== 'undefined' && Array.isArray(secTimes) && secTimes.length > 0) {
                window.sectionDurations = secTimes;
            } else {
                window.sectionDurations = [1200, 1200];
            }

            window.currentSecIndex = 0;
            window.activeSecTimeLeft = window.sectionDurations[window.currentSecIndex] || 1200;

            // Create Sectional Timer UI on Top Header matching the screenshot badge position
            let timerBox = document.getElementById('banking-aura-sectimer');
            if (!timerBox) {
                let box = document.createElement('div');
                box.id = 'banking-aura-sectimer';
                box.style.cssText = 'position:fixed; top:8px; right:250px; background:#e74c3c; color:#fff; padding:4px 12px; font-weight:bold; border-radius:4px; z-index:999999; font-size:14px; font-family:Arial;';
                document.body.appendChild(box);
                timerBox = box;
            }

            // Countdown Timer Loop
            window.secTimerHandle = setInterval(function() {
                if (window.activeSecTimeLeft > 0) {
                    window.activeSecTimeLeft--;
                    let mm = Math.floor(window.activeSecTimeLeft / 60);
                    let ss = window.activeSecTimeLeft % 60;
                    timerBox.innerHTML = `Sec Time: ${mm < 10 ? '0'+mm : mm}:${ss < 10 ? '0'+ss : ss}`;
                } else {
                    alert("⏱️ Section Time Over! Moving to the next section.");
                    autoAdvanceSection();
                }
            }, 1000);

            function autoAdvanceSection() {
                if (window.currentSecIndex < window.secList.length - 1) {
                    window.currentSecIndex++;
                    window.activeSecTimeLeft = window.sectionDurations[window.currentSecIndex] || 1200;
                    
                    // Shift to start question of next section
                    let qStartCount = 1;
                    for(let k=0; k<window.currentSecIndex; k++) {
                        qStartCount += parseInt(window.secTracker[k] || 35);
                    }
                    let targetQid = (typeof firstQid !== 'undefined' ? firstQid : 25001) + qStartCount - 1;
                    if (typeof displayQuestions === 'function') {
                        displayQuestions(targetQid);
                    }
                    applyLockStyles();
                } else {
                    alert("Test Time Finished! Submitting test.");
                    if (typeof finalSubmit === 'function') finalSubmit();
                }
            }

            function applyLockStyles() {
                for(let i=0; i<window.secList.length; i++) {
                    let tabElem = document.getElementById("sec-e" + i);
                    if (tabElem) {
                        if (i > window.currentSecIndex) {
                            tabElem.style.opacity = "0.3";
                            tabElem.style.pointerEvents = "none";
                            tabElem.title = "Locked Section";
                        } else {
                            tabElem.style.opacity = "1";
                            tabElem.style.pointerEvents = "auto";
                            tabElem.title = "";
                        }
                    }
                }
            }

            // Intercept manual tab click / shiftSection function
            window.nativeShiftSection = window.shiftSection;
            window.shiftSection = function(sid) {
                if (sid > window.currentSecIndex) {
                    alert("🔒 Section Locked! Aap pehla section complete kiye bina aage nahi ja sakte.");
                    return false;
                }
                if (window.nativeShiftSection) {
                    window.nativeShiftSection(sid);
                }
            };

            // Intercept Next Section / Submit button (sendData)
            window.nativeSendData = window.sendData;
            window.sendData = function() {
                autoAdvanceSection();
            };

            applyLockStyles();
        }, 1200);
    });
})();
</script>
"""


def finalize_html(soup):
    for a in soup.find_all("a"):
        if a.has_attr("onclick"):
            a["href"] = "javascript:void(0)"
            a.attrs.pop("target", None)
            
    # Inject script in head if present, else body
    if soup.head:
        soup.head.append(BeautifulSoup(EXTRA_INJECT_SCRIPT, "html.parser"))
    elif soup.body:
        soup.body.append(BeautifulSoup(EXTRA_INJECT_SCRIPT, "html.parser"))
        
    if soup.body is not None and not soup.find(id="ba-watermark"):
        soup.body.append(BeautifulSoup(WATERMARK_HTML, "html.parser"))
    return soup.prettify()


def _rewrite_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["a", "img", "link", "script"]):
        if tag.has_attr("href") and not tag["href"].startswith("http"):
            tag["href"] = urljoin(base_url, tag["href"])
        if tag.has_attr("src") and not tag["src"].startswith("http"):
            tag["src"] = urljoin(base_url, tag["src"])
    return finalize_html(soup)


def modify_html(html, full_url):
    return _rewrite_links(html, DEFAULT_BASE_URL)


def mody_html(html, full_url):
    return _rewrite_links(html, SOLUTION_BASE_URL)


# ─────────────────────────────────────────────
print("Test Bot started…")
bot.run_until_disconnected()
