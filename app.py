import logging
import io
from collections import defaultdict
import urllib3


import argparse
import firebase_admin
import requests
import pdfplumber
import tabula
from bs4 import BeautifulSoup
from firebase_admin import credentials, firestore

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Parser RU')
logger.setLevel(logging.INFO)

class MenuParser:
    def __init__(self, *, debug=False):
        self.debug = debug
        self.db = None

        if not debug:
            cred = credentials.Certificate("firebase_credentials.json")
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        else:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def parse_trindade(self):
        url = "https://ru.ufsc.br/ru/"
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error requesting page: {url} {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        pdf_url = soup.select_one("div.content a")["href"]
        # pdf_url = soup.select("div.content a")[0]["href"]

        response = requests.get(pdf_url, verify=False)
        pdf_file = io.BytesIO(response.content)

        menu = defaultdict(lambda: defaultdict(list))
        menu["url"] = pdf_url

        try:
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
        finally:
            pdf_file.close()

        return menu


    def parse_ararangua(self):
        url = 'https://ararangua.ufsc.br/cardapio-do-r-u/'
        pass

    def parse_cca(self):
        url = "https://ru.ufsc.br/cca-2/"

        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error requesting page: {url} {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        pdf_url = soup.select_one("div.content a")["href"]
        # pdf_url = soup.select("div.content a")[0]["href"]

        response = requests.get(pdf_url, verify=False)

        pdf_file = io.BytesIO(response.content)

        menu = defaultdict(lambda: defaultdict(list))
        menu["url"] = pdf_url

        tables = tabula.read_pdf(pdf_file, pages='all')

        week_map = {
            0: 'monday',
            1: 'tuesday',
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturnday',
            7: 'sunday',
        }

        for table in tables:
            current_key = ''
            # Imprime o conteúdo de cada célula
            for _, row in table.iterrows():
                i = 0
                for cell in row:
                    if not cell:
                        continue

                    lower_val = str(cell).lower().strip()

                    if lower_val and (lower_val == 'nan' or lower_val == '--' or lower_val == 'dia não letivo'):
                        continue

                    if lower_val == 'saladas':
                        current_key = 'salads'
                        continue

                    if lower_val == 'acompanhamentos':
                        current_key = 'accompaniments'
                        continue

                    if lower_val == 'carne':
                        current_key = 'meat'
                        continue

                    if lower_val == 'sobremesa':
                        current_key = 'dessert'
                        continue

                    if week_day := week_map.get(i):
                        menu[week_day][current_key].append(cell)

                    i += 1

        pdf_file.close()
        return menu

    def parse_blumenau(self):
        return {
            'url': 'https://ru.blumenau.ufsc.br/cardapios/',
        }

    def parse_joinville(self):
        url = 'https://restaurante.joinville.ufsc.br/cardapio-da-semana/'

        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error requesting page: {url} {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        pdf_url = soup.select_one("div.content a")["href"]

        menu = defaultdict(lambda: defaultdict(list))
        menu["url"] = pdf_url

        return menu

    def parse_curitibanos(self):
        url = "https://restaurante.curitibanos.ufsc.br/cardapio"

        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error requesting page: {url} {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        pdf_url = soup.select_one("div.content a")["href"]

        print('pdf url', pdf_url)
        # pdf_url = soup.select("div.content a")[0]["href"]

        response = requests.get(pdf_url, verify=False)

        pdf_file = io.BytesIO(response.content)

        menu = defaultdict(lambda: defaultdict(list))
        menu["url"] = pdf_url

        return menu

        with pdfplumber.open(pdf_file) as pdf:
                current_day = None
                lunch_count = 0
                is_lunch = False
                initial_date = None
                for page in pdf.pages:
                    texts = page.extract_text().split('\n')
                    for text in texts:
                        print(repr(text))

        return

        tables = tabula.read_pdf(pdf_file, pages='all')

        for table in tables:
            print(table)
            current_key = ''
            # Imprime o conteúdo de cada célula
            for _, row in table.iterrows():
                i = 0
                for cell in row:
                    if not cell:
                        continue

                    lower_val = str(cell).lower().strip()

                    # print(cell)

                    # if lower_val and (lower_val == 'nan' or lower_val == '--'):
                    #     continue

                    # if lower_val == 'saladas':
                    #     current_key = 'salads'
                    #     continue

                    # if lower_val == 'acompanhamentos':
                    #     current_key = 'accompaniments'
                    #     continue

                    # if lower_val == 'carne':
                    #     current_key = 'meat'
                    #     continue

                    # if lower_val == 'sobremesa':
                    #     current_key = 'dessert'
                    #     continue

                    # if week_day := week_map.get(i):
                    #     menu[week_day][current_key].append(cell)

                    i += 1

        pdf_file.close()
        return menu


    def update_menus(self, locations):
        for local in locations:
            try:
                method_name = 'parse_' + local
                method = getattr(self, method_name, None)
                if method is not None and callable(method):
                    menu = method()

                    if self.debug:
                        logger.info(f'{local}')
                        logger.info(menu)

                    if self.db is not None:
                        if menu:
                            self.db.collection("restaurant").document(local).set(menu)
                            logger.info("Successful Update - " + local)
            except Exception as e:
                logger.error(f"Error {local}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    menu_parser = MenuParser(debug=args.debug)
    menu_parser.update_menus((
        'cca',
        'trindade',
        'curitibanos',
        'blumenau',
        'joinville',
    ))
