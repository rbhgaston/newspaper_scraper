import os
import time
import random
import requests
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDate
from tqdm import tqdm

# List of newspapers to scrape
NEWSPAPERS = [
    "etemaad", "hamshahri", "iran", "kayhan", "shargh", "JomhouriEslami",
    "resalat", "ebtekar", "arman", "DonyayeEghtesad", "khorasan", "ghods"
]

NEWSPAPERS_WORKING = ["JomhouriEslami", "DonyayeEghtesad"]

# Base URLs
BASE_VIEWER_URL = "https://www.pishkhan.com/pdfviewer.php?paper={}&date={}"

# Headers to simulate a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def generate_dates(start_persian: str, end_persian: str):
    start_gregorian = JalaliDate.strptime(start_persian, "%Y%m%d").to_gregorian()
    end_gregorian = JalaliDate.strptime(end_persian, "%Y%m%d").to_gregorian()
    delta = (end_gregorian - start_gregorian).days
    for i in range(delta + 1):
        yield JalaliDate(start_gregorian + timedelta(days=i))

def download_pdf(paper, persian_date):
    date_str = persian_date.strftime("%Y%m%d")
    year = date_str[:4]
    month = date_str[4:6]
    folder_path = f"newspapers/{paper}/{year}/{month}/{date_str}"
    os.makedirs(folder_path, exist_ok=True)
    filename = f"{folder_path}/{paper}_{date_str}.pdf"
    if os.path.exists(filename):
        print(f"[SKIP] Already downloaded: {filename}")
        return

    viewer_url = BASE_VIEWER_URL.format(paper, date_str)
    try:
        response = requests.get(viewer_url, headers=HEADERS, allow_redirects=True, timeout=20)
        if response.history and response.status_code == 200:
            pdf_url = response.url
            pdf_response = requests.get(pdf_url, headers=HEADERS, timeout=10)
            print(pdf_response.ok, pdf_response.headers.get("Content-Type"))
            
            if pdf_response.ok and pdf_response.headers.get("Content-Type") == "application/pdf":
                with open(filename, "wb") as f:
                    f.write(pdf_response.content)
                print(f"[OK] Downloaded: {filename}")
            else:
                print(f"[FAIL] PDF not found or invalid content for {paper} {date_str}")
        else:
            print(f"[FAIL] No redirect to PDF for {paper} {date_str}")
            # print(viewer_url)
    except Exception as e:
        print(f"[ERROR] {paper} {date_str}: {e}")

def scrape_pishkhan(start_date: str, end_date: str):
    dates = list(generate_dates(start_date, end_date))
    for date in tqdm(dates, desc="Scraping dates"):
        for paper in NEWSPAPERS_WORKING:
            for _ in range(3):  # Retry logic
                try:
                    download_pdf(paper, date)
                    break
                except Exception as e:
                    print(f"[RETRY] {paper} {date} due to {e}")
                    time.sleep(3)
            time.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    # Example: 14040404 to 14040404 for testing
    scrape_pishkhan("14040404", "14040404")
