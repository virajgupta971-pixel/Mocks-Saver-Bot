# Copyright github.com/devgaganin

from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin
import requests
from telethon import TelegramClient, events
from telethon.tl.types import InputFile
from config import API_ID, API_HASH, BOT_TOKEN, COOKIES, OWNER_ID

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


# --- OLIVEBOARD ---

# Headers for HTTP requests
HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/132.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": (
        '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"'
    ),
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Base URIs for different exam types (Banking + SSC + Railways)
BASE_URIS = {
    # Banking Exams
    "rrbpo": (
        "https://u1.oliveboard.in/exams/tests/?c=rrbpo&os=1&testid={test_id}"
    ),
    "rrbclerk": (
        "https://u1.oliveboard.in/exams/tests/?c=rrbclerk&os=1&testid={test_id}"
    ),
    "ibpspo": (
        "https://u1.oliveboard.in/exams/tests/?c=ibpspo&os=1&testid={test_id}"
    ),
    "ibpsclerk": (
        "https://u1.oliveboard.in/exams/tests/?c=ibpsclerk&os=1&testid={test_id}"
    ),
    "sbipo": (
        "https://u1.oliveboard.in/exams/tests/?c=sbipo&os=1&testid={test_id}"
    ),
    "sbiclerk": (
        "https://u1.oliveboard.in/exams/tests/?c=sbiclerk&os=1&testid={test_id}"
    ),
    # SSC & Railway Exams
    "cgl1": "https://u1.oliveboard.in/exams/tests/?c=ssc2019&testid={test_id}",
    "chsl": "https://u1.oliveboard.in/exams/tests/?c=chsl&testid={test_id}",
    "chsl2": "https://u1.oliveboard.in/exams/tests/?c=chsl2&testid={test_id}",
    "sscmts": "https://u1.oliveboard.in/exams/tests/?c=sscmts&testid={test_id}",
    "ntpc1": "https://u1.oliveboard.in/exams/tests/?c=ntpc1&os=1&testid={test_id}",
    "ntpc2": "https://u1.oliveboard.in/exams/tests/?c=ntpc2&os=1&testid={test_id}",
    "rrbalp1": (
        "https://u1.oliveboard.in/exams/tests/?c=rrbalp1&os=1&testid={test_id}"
    ),
    "rrbalp2": (
        "https://u1.oliveboard.in/exams/tests/?c=rrbalp2&os=1&testid={test_id}"
    ),
    "rrbgrpd": (
        "https://u1.oliveboard.in/exams/tests/?c=rrbgrpd&os=1&testid={test_id}"
    ),
}


@bot.on(events.NewMessage(pattern=r"/fetch (\w+) (\d+)"))
async def fetch_exam(event):
  """Fetches test details based on the exam type and test ID."""
  if event.sender_id != OWNER_ID:
    await event.reply("Not allowed")
    return
  exam = event.pattern_match.group(1).lower()
  test_id = event.pattern_match.group(2)

  if exam not in BASE_URIS:
    await event.respond(
        "Invalid exam type! Supported types are: "
        + ", ".join(BASE_URIS.keys())
    )
    return

  # Construct the URL
  url = BASE_URIS[exam].format(test_id=test_id)

  try:
    # Fetch the HTML content
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    html_content = response.text
    modified_html = modify_html(html_content, url)

    # Save the modified HTML to a file
    file_name = f"exam_{exam}_{test_id}.html"
    with open(file_name, "w", encoding="utf-8") as file:
      file.write(modified_html)

    prog = await bot.send_message(event.chat_id, "Extracting Questions")

    # Send the Question file back to the user
    await prog.edit("Uploading Test Papers... ")
    await event.respond(
        f"**📕 Exam Name: {exam}**\n**🆔 Test ID:"
        f" {test_id}**\n**🥹 Type: Question**\n\n__**Powered by Banking"
        " Aura**__",
        file=file_name,
    )

    await prog.edit("Auto Submitting the test")
    submit_test(url, test_id, exam)  # Bypasses section lock / auto submits

    await prog.edit("Test Submitted Successfully... ")
    t = url.replace(
        "https://u1.oliveboard.in/exams/tests/",
        "https://u1.oliveboard.in/exams/solution/index3.php",
    )
    print(t)
    k = fetch_solution(t)
    await prog.edit("Trying to fetch the solution... ")
    mod_html = mody_html(k, url)

    file_sol_name = f"solution_exam_{exam}_{test_id}.html"
    with open(file_sol_name, "w", encoding="utf-8") as file:
      file.write(mod_html)

    # Send the Solution file back to the user
    await prog.edit("Uploading Solution... ")
    await event.respond(
        f"**📕 Exam Name: {exam}**\n**🆔 Test ID:"
        f" {test_id}**\n**🥹 Type: Solution**\n\n__**Powered by Banking"
        " Aura**__",
        file=file_sol_name,
    )
    await prog.delete()

    # Cleanup temporary local files
    if os.path.exists(file_name):
      os.remove(file_name)
    if file_sol_name and os.path.exists(file_sol_name):
      os.remove(file_sol_name)

  except requests.exceptions.RequestException as e:
    await event.respond(f"Failed to fetch the test details: {e}")


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
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/132.0.0.0 Safari/537.36"
      ),
      "X-Requested-With": "XMLHttpRequest",
      "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
  }
  q_value = f"{test_id}001"
  raw_data = f"data=%7B%22{q_value}001%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2201%3A30%3A00%22%2C%22end%22%3A%2201%3A29%3A58%22%7D%5D%2C%22o%22%3A%22%22%7D%2C%22{q_value}002%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2200%3A59%3A57%22%2C%22end%22%3A%2200%3A59%3A53%22%7D%5D%2C%22o%22%3A%221%22%7D%2C%22{q_value}003%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2200%3A59%3A53%22%2C%22end%22%3A%2200%3A59%3A47%22%7D%5D%2C%22o%22%3A%22%22%7D%2C%22{q_value}004%22%3A%7B%22q%22%3A%22{q_value}%22%2C%22t%22%3A%5B%7B%22st%22%3A%2200%3A59%3A47%22%2C%22end%22%3A%2200%3A59%3A46%22%7D%2C%7B%22st%22%3A%2200%3A59%3A46%22%2C%22end%22%3A%2200%3A59%3A43%22%7D%5D%2C%22o%22%3A%22%22%7D%7D&uid=&qpi={test_id}&ppi=-1&lang=eqt&c={exam}&source=web"

  print(f"Submitting test payload for exam: {exam}, test_id: {test_id}")
  response = requests.post(surl, headers=headers, data=raw_data)
  print(f"Test Submission Response Status Code: {response.status_code}")


# Step 2: Fetch Solution
def fetch_solution(url):
  headers = {
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
      ),
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
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/132.0.0.0 Safari/537.36"
      ),
      "sec-ch-ua": (
          '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"'
      ),
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
  }
  response = requests.get(url, headers=headers)
  html_content = response.text
  print(f"Solution Fetch Response Status Code: {response.status_code}")
  return html_content


DEFAULT_BASE_URL = "https://u1.oliveboard.in/exams/tests/"

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


def finalize_html(soup):
  """Fix button links and add the watermark."""
  for a in soup.find_all("a"):
    if a.has_attr("onclick"):
      a["href"] = "javascript:void(0)"
      a.attrs.pop("target", None)
  if soup.body is not None and not soup.find(id="ba-watermark"):
    soup.body.append(BeautifulSoup(WATERMARK_HTML, "html.parser"))
  return soup.prettify()


def modify_html(html, full_url):
  """Modifies HTML content for relative links."""
  soup = BeautifulSoup(html, "html.parser")

  for tag in soup.find_all(["a", "img", "link", "script"]):
    if tag.has_attr("href"):
      if not tag["href"].startswith("http"):
        tag["href"] = urljoin(DEFAULT_BASE_URL, tag["href"])

    if tag.has_attr("src"):
      if not tag["src"].startswith("http"):
        tag["src"] = urljoin(DEFAULT_BASE_URL, tag["src"])

  return finalize_html(soup)


SOLUTION_BASE_URL = "https://u1.oliveboard.in/exams/solution/"


def mody_html(html, full_url):
  """Modifies solution HTML content for relative links."""
  soup = BeautifulSoup(html, "html.parser")

  for tag in soup.find_all(["a", "img", "link", "script"]):
    if tag.has_attr("href"):
      if not tag["href"].startswith("http"):
        tag["href"] = urljoin(SOLUTION_BASE_URL, tag["href"])

    if tag.has_attr("src"):
      if not tag["src"].startswith("http"):
        tag["src"] = urljoin(SOLUTION_BASE_URL, tag["src"])

  return finalize_html(soup)


# Run the bot
print("Bot started...")
bot.run_until_disconnected()

# Copyright github.com/devgaganin
