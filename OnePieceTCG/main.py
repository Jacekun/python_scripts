# Scrape card info from One Piece EN site.
# https://en.onepiece-cardgame.com/cardlist/

# Imports
import requests
#import csv
import json
import os
from pathlib import Path
#from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup


# Methods
def write_to_log(content: str) -> bool:
    try:
        Path("logs").mkdir(parents=True, exist_ok=True)
        filename: str = f"log_{datetime.today().strftime('%Y-%m-%d')}.log"
        filepath: str = os.path.join("logs", filename)
        with open(filepath, 'a') as f:
            f.write(f"{content}\n")
        return True
    except Exception as e:
        #log_err("Error", e)
        return False

def log(content: str):
    print(f"{content}")
    write_to_log(content)

def log_err(content: str, err: Exception):
    to_write: str = f"{content} => {err}"
    print(to_write)
    write_to_log(to_write)

def write_file(filename: str, content: str) -> bool:
    try:
        with open(filename, 'w', encoding = 'utf8') as f:
            f.write(content)
        return True
    except Exception as e:
        log_err("Error", e)
        return False

def read_file(filename: str) -> any:
    try:
        contents = ""
        with open(filename, 'r', encoding = 'utf8') as file:
            contents = file.read()

        return contents
    except Exception as e:
        log_err("Error", e)
        return None

def write_json(filename: str, content: any) -> bool:
    try:
        with open(filename, 'w') as f:
            json.dump(content, f, indent = 4)
        return True
    except Exception as e:
        log_err("Error", e)
        return False

def read_json(filename: str) -> any:
    try:
        contents = None
        with open(filename) as file:
            contents = json.loads(file.read())

        return contents
    except Exception as e:
        log_err("Error", e)
        return None

def main():
    try:
        route_home: str = "https://en.onepiece-cardgame.com"
        route_cardlist: str = f"{route_home}/cardlist/"

        cardlist_id: str = ""#569001
        file_cardlist_html: str = f"list_{cardlist_id}.html"
        file_output_card: str = ""
        contents_html: str = None

        is_use_cache: bool = False

        #-- Create Folders
        Path("output").mkdir(parents=True, exist_ok=True)

        #-- Load from cache if available
        if os.path.exists(file_cardlist_html) and is_use_cache:
            log(f"Reading cached file : {file_cardlist_html}")
            contents_html = read_file(file_cardlist_html).strip()
        else:
            log("Requesting card list..")
            # POST request to fetch card list
            req_body = {
                "series": str(cardlist_id),
                "freewords": ""
            }
            req_object = requests.post(
                url = route_cardlist,
                json = req_body
            )

            if req_object.ok:
                #write_file(file_cardlist_html, req_object.text)
                #log("Done writing HTMl content.")
                contents_html = req_object.text.strip()

        if contents_html != "":
            soup = BeautifulSoup(contents_html, "html.parser")
            log("Parsing soup...")

            soup_main = soup.find("div", class_="resultCol")
            soup_cards = soup_main.find_all("dl", class_="modalCol")

            log("Parsing card list..")
            for soup_card_div in soup_cards:
                #-- Card Set, Rarity, and Type
                soup_setrarity = soup_card_div.find("div", class_="infoCol").find_all("span")
                soup_setrarity_len = len(soup_setrarity)
                card_set_full = soup_card_div.find("div", class_="getInfo").text
                card_set: str = ""
                card_rarity: str = ""
                card_type: str = ""
                #log(f"Card Info len: {soup_setrarity_len}")
                if soup_setrarity_len == 3:
                    card_set = soup_setrarity[0].text
                    card_rarity = soup_setrarity[1].text
                    card_type = soup_setrarity[2].text
                    #log(f"Card Info => Set: {card_set}. Rarity: {card_rarity}. Type: {card_type}. Full set name: {card_set_full}")

                #-- Card Image
                soup_card_image = soup_card_div.find("div", class_="frontCol").find("img")
                card_image: str = route_home + "/" + str(soup_card_image["src"]).strip().lstrip('.').lstrip('\\').lstrip('/')
                #log(f"Card image => {card_image}")

                #-- Card other text info
                card_name = soup_card_div.find("div", class_="cardName").text.strip()
                card_cost = soup_card_div.find("div", class_="cost").contents[-1].strip()
                card_power = soup_card_div.find("div", class_="power").contents[-1].strip()
                card_color = soup_card_div.find("div", class_="color").contents[-1].strip()
                card_counter = soup_card_div.find("div", class_="counter").contents[-1].strip()
                card_attribute = soup_card_div.find("div", class_="attribute").find("i").text.strip()
                card_feature = soup_card_div.find("div", class_="feature").contents[-1].strip()
                card_text = soup_card_div.find("div", class_="text").text.strip()
                """
                log(f'''Other card info => 
                    Cost: {card_cost} 
                    Power: {card_power}  
                    Color: {card_color} 
                    Counter: {card_counter} 
                    Attribute: {card_attribute} 
                    Feature: {card_feature} 
                    Text: {card_text} 
                    '''
                )
                """

                #-- Setup output file
                file_output_card = os.path.join("output", f"{card_set}.json")
                card_contents = {
                    "Name": card_name,
                    "Set": card_set,
                    "Rarity": card_rarity,
                    "Type": card_type,
                    "Image": card_image,
                    "Cost": card_cost,
                    "Power": card_power,
                    "Color": card_color,
                    "Counter": card_counter,
                    "Attribute": card_attribute,
                    "Feature": card_feature,
                    "Text": card_text
                }

                #-- Save to JSON file
                write_json(file_output_card, card_contents)

        else:
            raise Exception(f"Failed to fetch card list. Status code: {req_object.status_code}. Reason: {req_object.reason}")


        log("Done!")

    except Exception as e:
        log_err("Main", e)
        raise Exception("Error on Main process.")

if __name__ == "__main__":
    main()
