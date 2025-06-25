import os
import time
import random
import argparse
import requests
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDate
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Setup newspapers with correct slugs
NEWSPAPERS = ["JomhouriEslami"]

BASE_VIEWER_URL = "https://www.pishkhan.com/pdfviewer.php?paper={}&date={}"

# Configure ChromeDriver (visible browser)
def init_browser():
    chrome_options = Options()
    # Remove next line if you want to see browser
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=chrome_options)

# Download file
def download_pdf(pdf_url, output_path):
    try:
        response = requests.get(pdf_url, stream=True, timeout=15)
        if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"[ERROR] Failed to download PDF: {e}")
    return False

# Build date string
def persian_date_string(date: JalaliDate) -> str:
    return f"{date.year:04d}{date.month:02d}{date.day:02d}"

# Main scraping function
def scrape_newspapers(start_date: JalaliDate, end_date: JalaliDate):
    driver = init_browser()
    current_date = start_date

    while current_date <= end_date:
        date_str = persian_date_string(current_date)
        year, month = f"{current_date.year}", f"{current_date.month:02d}"

        for paper_name in NEWSPAPERS:
            folder = f"newspapers/{paper_name}/{year}/{month}/"
            os.makedirs(folder, exist_ok=True)
            output_file = os.path.join(folder, f"{date_str}.pdf")

            if os.path.exists(output_file):
                print(f"[SKIP] Already exists: {output_file}")
                continue

            viewer_url = BASE_VIEWER_URL.format(paper_name, date_str)
            try:
                driver.get(viewer_url)
                time.sleep(15)  # Wait for JS redirect
                final_url = driver.current_url

                if not final_url.endswith(".pdf"):
                    print(f"[FAIL] No redirect to PDF for {paper_name} {date_str}")
                    continue

                success = download_pdf(final_url, output_file)
                if success:
                    print(f"[OK] Downloaded: {paper_name} {date_str}")
                else:
                    print(f"[FAIL] PDF not found or invalid for {paper_name} {date_str}")

            except Exception as e:
                print(f"[ERROR] Exception for {paper_name} {date_str}: {e}")

            time.sleep(random.uniform(5, 10))

        current_date += timedelta(days=1)

    driver.quit()

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Iranian newspapers from Pishkhan.")
    parser.add_argument("--start", required=True, help="Start date in Persian format YYYYMMDD (e.g., 14040101)")
    parser.add_argument("--end", required=True, help="End date in Persian format YYYYMMDD (e.g., 14040301)")
    args = parser.parse_args()

    try:
        start = JalaliDate(int(args.start[:4]), int(args.start[4:6]), int(args.start[6:]))
        end = JalaliDate(int(args.end[:4]), int(args.end[4:6]), int(args.end[6:]))
        scrape_newspapers(start, end)
    except Exception as e:
        print(f"[ERROR] Invalid date format: {e}")


