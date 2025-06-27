import os
import time
import random
import argparse
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDate
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

BASE_VIEWER_URL = "https://www.pishkhan.com/pdfviewer.php?paper={}&date={}"
WAIT_REDIRECT = 10  # seconds to wait for JS redirect
# NEWSPAPERS
# Setup newspapers
NEWSPAPERS_ALL = ["ArmanMeli", "Asia", "Etemaad", "Afkar", "EghtesadSaramad", "JahanSanat", 
              "JomhouriEslami", "DonyayeEghtesad", "RooyesheMellat", "Shargh", "Shahrvand", "AsreTosee", 
              "AsrGhanoon", "MardomSalari", "AbrarSport"]
WORKING_NEWSPAPERS = ["Shargh", "Etemaad", "KayhanNews", "JomhouriEslami", "Ghods", "ArmanMeli", "Shahrvand",
                      "Asia", "EghtesadSaramad", "MardomSalari", "Afkar", "JahanSanat", "RooyesheMellat", "AsreTosee",
                      "AsrGhanoon", "AbrarSport"]
NOT_WORKING_NEWSPAPERS = [ "DonyayeEghtesad"]

NEWSPAPERS = WORKING_NEWSPAPERS

## LOGGING SETUP
STATUS_FILE = "status_calendar.csv"

def load_status_calendar(all_dates):
    if Path(STATUS_FILE).exists():
        df = pd.read_csv(STATUS_FILE, dtype=str)
    else:
        df = pd.DataFrame({"date": all_dates})
        for paper in NEWSPAPERS:
            df[paper] = "pending"
        df.to_csv(STATUS_FILE, index=False)
    return df

def save_status_calendar(df):
    df.to_csv(STATUS_FILE, index=False)

def format_date(date_str):
    """
    Formats a date string from 'YYYYMMDD' to 'YYYY-MM-DD'.
    """
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"


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
                df.loc[df["date"] == format_date(date_str), paper_name] = "downloaded"
                print(df.loc[df["date"] == format_date(date_str), paper_name])
                save_status_calendar(df)
                continue

            viewer_url = BASE_VIEWER_URL.format(paper_name, date_str)
            try:
                driver.get(viewer_url)
                time.sleep(WAIT_REDIRECT)  # Wait for JS redirect
                final_url = driver.current_url

                if not final_url.endswith(".pdf"):
                    print(f"[FAIL] No redirect to PDF for {paper_name} {date_str}")
                    df.loc[df["date"] == format_date(date_str), paper_name] = "failed"
                    save_status_calendar(df)
                    continue

                success = download_pdf(final_url, output_file)
                if success:
                    print(f"[OK] Downloaded: {paper_name} {date_str}")
                    df.loc[df["date"] == format_date(date_str), paper_name] = "downloaded"
                    save_status_calendar(df)
                else:
                    print(f"[FAIL] PDF not found or invalid for {paper_name} {date_str}")
                    df.loc[df["date"] == format_date(date_str), paper_name] = "failed"
                    save_status_calendar(df)

            except Exception as e:
                print(f"[ERROR] Exception for {paper_name} {date_str}: {e}")

            save_status_calendar(df)
            time.sleep(random.uniform(5, 10))
            

        current_date += timedelta(days=1)
        print(f"[INFO] Completed date: {current_date}")
        
    driver.quit()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Download Iranian newspapers from Pishkhan.")
    parser.add_argument("--start", required=True, help="Start date in Persian format YYYYMMDD (e.g., 14040101)")
    parser.add_argument("--end", required=True, help="End date in Persian format YYYYMMDD (e.g., 14040301)")
    args = parser.parse_args()

    # generate the list of all dates in Jalali calendar
    start_date = JalaliDate(int(args.start[:4]), int(args.start[4:6]), int(args.start[6:]))
    end_date = JalaliDate(int(args.end[:4]), int(args.end[4:6]), int(args.end[6:]))
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    df = load_status_calendar(all_dates)    
    try:
        start = JalaliDate(int(args.start[:4]), int(args.start[4:6]), int(args.start[6:]))
        end = JalaliDate(int(args.end[:4]), int(args.end[4:6]), int(args.end[6:]))
        scrape_newspapers(start, end)
    except Exception as e:
        print(f"[ERROR] Invalid date format: {e}")

    save_status_calendar(df)

# example usage
# python selenium_scraper.py --start 14040101 --end 14040301

