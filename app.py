import datetime
import logging
import io
import re
from collections import defaultdict

import firebase_admin
import requests
import pdfplumber
from bs4 import BeautifulSoup
from firebase_admin import credentials, firestore

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Parser RU')
logger.setLevel(logging.INFO)


def parse_trindade():
    url = "https://ru.ufsc.br/ru/"
    response = requests.get(url)

    if response.status_code != 200:
        logger.error(f"Error requesting page: {url} {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    pdf_url = soup.select_one("div.content a")["href"]
    # pdf_url = soup.select("div.content a")[0]["href"]

    response = requests.get(pdf_url)
    pdf_file = io.BytesIO(response.content)

    menu = defaultdict(lambda: defaultdict(list))

    with pdfplumber.open(pdf_file) as pdf:
        current_day = None
        lunch_count = 0
        is_lunch = False
        initial_date = None
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.split("\n"):
                line_lower = line.lower().replace("ç", "c").replace("á", "a")

                if "segunda-feira:" in line_lower:
                    current_day = "monday"

                    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", line_lower)
                    if match:
                        data = match.group(0)
                        initial_date = "-".join(reversed(data.split("/")))
                    else:
                        initial_date = datetime.today().strftime("%Y-%m-%d")
                    continue

                elif "terca-feira:" in line_lower:
                    current_day = "tuesday"
                    continue

                elif "quarta-feira:" in line_lower:
                    current_day = "wednesday"
                    continue

                elif "quinta-feira:" in line_lower:
                    current_day = "thursday"
                    continue

                elif "sexta-feira:" in line_lower:
                    current_day = "friday"
                    continue

                elif "sabado:" in line_lower:
                    current_day = "saturday"
                    continue

                elif "domingo:" in line_lower:
                    current_day = "sunday"
                    continue

                if current_day:
                    if line_lower == "almoco":
                        is_lunch = True
                        continue

                    if line_lower == "jantar":
                        is_lunch = False
                        continue

                    if ":" not in line:
                        continue

                    food = line.split(":")[0].capitalize()

                    if is_lunch:
                        lunch_count += 1
                        menu[current_day]["lunch"].append(food)
                    elif lunch_count > 0:  # Is dinner
                        lunch_count -= 1
                        menu[current_day]["dinner"].append(food)
                    else:
                        menu[current_day]["common"].append(food)

    return {initial_date: menu}


def update_menu():
    try:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)

        db = firestore.client()
        menu = parse_trindade()
        if menu:
            db.collection("restaurant").document("trindade").set(menu, merge=True)
            logger.info("Successful Update")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    update_menu()
