# Export files with different format
# Convert DragonShield export to Edopro banlist.

# Imports
import requests
import csv
import json
import os
from pathlib import Path
from time import sleep
from datetime import datetime

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

def pop_first_line(file: str) -> str:
    with open(file, 'r+') as f: # open file in read / write mode
        firstLine = f.readline() # read the first line and throw it out
        data = f.read() # read the rest
        f.seek(0) # set the cursor to the top of the file
        f.write(data) # write the data back
        f.truncate() # set the file size to the current size
        return firstLine
    return ""

def write_file(filename: str, content: str) -> bool:
    try:
        with open(filename, 'w', encoding = 'utf8') as f:
            f.write(content)
        return True
    except Exception as e:
        log_err("Error", e)
        return False

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

def process_card_list(card_format: str, export_json_file_name: str, jsonfile_card_conf_list: str, jsonfile_cards_with_error: str, export_conf_file: str):
    # Read from JSON file and request card passcode
    card_json = read_json(export_json_file_name)

    conf_contents: str = f"#[My Cards {card_format}]\n!My Cards {card_format}\n$whitelist\n"
    card_conf_list: list[any] = [] # List of all card to be put to conf file.
    cards_with_error: list[any] = [] # List of all cards with error

    if card_json is not None:
        log(f"JSON file loaded for {card_format} card list")

        for entry in card_json:
            card_id: int = 0
            card_name = str(entry["name"])
            card_setcode = str(entry["set"])
            card_qty = int(entry["qty"])
            card_trade_qty = int(entry["trade_qty"])
            log(f"\tRequesting passcode for {card_name} with setcode '{card_setcode}'")

            # set filename for json file cache
            card_setcode = card_setcode.rstrip('r').rstrip('b')
            jsonfile_setcode: str = os.path.join(folder_setcodes, f"{card_setcode}.json")

            # Write to json file cache, if its not already existing
            if not os.path.exists(jsonfile_setcode):
                # GET request to YGOPRODECK API
                req_object = requests.get(route_setcode.format(card_setcode))
                #log(f"\tRequest response: {req_object.status_code}")

                if req_object.ok:
                    temp_object = json.loads(req_object.text)
                    if "id" in temp_object:
                        # Write to file
                        write_file(jsonfile_setcode, req_object.text)
                        #log(f"\tWrite to cache => {card_setcode}")
                    else:
                        cards_with_error.append(entry)
                        log(f"\tIssue found on saving ({req_object.status_code}) => {card_setcode}")
                else:
                    cards_with_error.append(entry)
                    log(f"\tIssue found on searching ({req_object.status_code}) => {card_setcode}")

                # Toggle variable
                is_request = True
            else:
                log(f"\tUse cached file => {card_setcode}")
                is_request = False
            
            # Sleep for 100 milliseconds, if request is made
            if is_request:
                sleep(0.10)
            
            #break

            # Read setcode info
            if os.path.exists(jsonfile_setcode):
                is_already_exist = False
                try:
                    # Measure quantity
                    total_qty = card_qty
                    if total_qty <= 0:
                        total_qty = card_trade_qty
                    if total_qty > 3:
                        total_qty = 3
                    # Read json file from setcode folder
                    card_json_setcode = read_json(jsonfile_setcode)
                    card_id = int(card_json_setcode["id"])
                    card_name = str(card_json_setcode["name"])
                except Exception as e:
                    cards_with_error.append(entry)
                    log_err(f"Issue found on reading => {card_setcode}.json", e)
                    if os.path.exists(jsonfile_setcode):
                        os.remove(jsonfile_setcode)
                
                try:
                    # Find item if it already exist, and add quantity
                    for x in card_conf_list:
                        if x["id"] and int(x["id"]) == card_id:
                            is_already_exist = True
                            x_qty = int(x["qty"]) + total_qty
                            x_card_id = str(x["id"])
                            x_cardname = str(x["name"])
                            x["qty"] = x_qty
                            log(f"\tCard info updated => [Id: {x_card_id}] [Name: {x_cardname} [Qty: {x_qty}]")
                            break
                    
                    if not is_already_exist:
                        # Append to list
                        #log(f"\tCard info => [Id: {card_id}] [Name: {card_name}")
                        new_card_object = {
                            "id": card_id,
                            "name": card_name,
                            "qty": total_qty
                        }
                        card_conf_list.append(new_card_object)
                    else:
                        continue
                except Exception as e:
                    cards_with_error.append(entry)
                    log_err(f"\tIssue found on looking up {card_setcode}.json - {card_name}", e)
                
        
        # Dump all cards with combined qty
        write_json(jsonfile_card_conf_list, card_conf_list)

        for conf_entry in card_conf_list:
            card_id = int(conf_entry["id"])
            card_name = str(conf_entry["name"])
            total_qty = int(conf_entry["qty"])
            if total_qty > 3:
                total_qty = 3
            # Add new line to conf export file.
            if card_id > 0 and total_qty > 0:
                conf_contents += f"{card_id} {total_qty} #{card_name}\n"

    # Dump error cards
    write_json(jsonfile_cards_with_error, cards_with_error)

    # Dump file
    write_file(export_conf_file, conf_contents)

# Main
try:
    # Constants
    folder_setcodes = "setcodes"
    folder_outputs = "output"
    route_setcode = "https://db.ygoprodeck.com/api/v7/cardsetsinfo.php?setcode={0}&includeAliased&num=1&offset=0"
    route_image = "https://images.ygoprodeck.com/images/cards/{0}.jpg" # card passcode
    index_folder_name: int = 0
    index_qty: int = 1
    index_tradeqty: int = 2
    index_cardname: int = 3
    index_set_name: int = 5
    index_cardnumber: int = 6
    index_rarity: int = 7
    index_printing: int = 9
    index_price_low: int = 13
    index_price_mid: int = 14
    index_price_market: int = 15
    csv_text_encoding: str = "utf-8"
    price_conversion_php: float = 55.00
    # Use for array holders
    index_all: int = 0
    index_tcg: int = 1
    index_ocg: int = 2
    index_ae: int = 3

    # File paths
    csv_file_name: str = "all-folders-output.csv"
    csv_file_name_source: str = "all-folders"
    # Export filepaths
    export_json_file_name: list[str] = [ 
        os.path.join(folder_outputs, "cards.json"),
        os.path.join(folder_outputs, "TCG_cards.json"), 
        os.path.join(folder_outputs, "OCG_cards.json"),
        os.path.join(folder_outputs, "AE_cards.json")
    ]
    export_conf_file: list[str] = [ 
        os.path.join(folder_outputs, "MyCards.lflist.conf"),
        os.path.join(folder_outputs, "MyCards_TCG.lflist.conf"),
        os.path.join(folder_outputs, "MyCards_OCG.lflist.conf"),
        os.path.join(folder_outputs, "MyCards_AE.lflist.conf")
    ]
    jsonfile_cards_with_error: list[str] = [ 
        os.path.join(folder_outputs, "cards_error.json"),
        os.path.join(folder_outputs, "TCG_cards_error.json"),
        os.path.join(folder_outputs, "OCG_cards_error.json"),
        os.path.join(folder_outputs, "AE_cards_error.json")
    ]
    jsonfile_card_conf_list: list[str] = [ 
        os.path.join(folder_outputs, "cards_conf.json"),
        os.path.join(folder_outputs, "TCG_cards_conf.json"),
        os.path.join(folder_outputs, "OCG_cards_conf.json"),
        os.path.join(folder_outputs, "AE_cards_conf.json")
    ]
    jsonfile_listings: list[str] = [ 
        os.path.join(folder_outputs, "listings.json"),
        os.path.join(folder_outputs, "TCG_listings.json"),
        os.path.join(folder_outputs, "OCG_listings.json"),
        os.path.join(folder_outputs, "AE_listings.json")
    ]

    # Variables
    card_count: int = 0
    sep: str = ","
    folder_skip: list[str] = ['Rush']
    folder_listing: list[str] = ['Binder', 'Gold Binder']

    cards: list[any] = [] # List of all cards from Imported csv file
    cards_tcg: list[any] = [] # TCG-only list
    cards_ocg: list[any] = [] # OCG and AE List
    cards_ae: list[any] = [] # AE-only List
    card_listings: list[any] = [] # List of card listings with rarity. For shop use.

    # Dynamic variables for local use
    jsonfile_setcode: str = ""
    card_setcode: str = ""
    card_setname: str = ""
    card_rarity: str = ""
    card_printing: str = ""
    card_format: str = "TCG"
    row_card_name: str = ""
    card_folder_name: str = ""
    contents_decode: str = ""
    card_qty: int = 0
    card_setcode_split: any = None
    card_json: any = None
    card_json_setcode: any = None
    req_object: any = None
    temp_object: any = None
    is_request: bool = False
    is_ocg: bool = False
    is_ae: bool = False
    is_tcg: bool = False

    # Create necessary folders
    Path(folder_setcodes).mkdir(parents=True, exist_ok=True)
    Path(folder_outputs).mkdir(parents=True, exist_ok=True)

    # Ask for export file
    #csv_file_name = input("DragonShield export file name => ")

    # Verify file
    if not csv_file_name_source.endswith(".csv"):
        csv_file_name_source += ".csv"

    #csv_file_name = os.path.join(".", csv_file_name_source)
    log(f"DragonShield Export File => {csv_file_name_source}")

    if not os.path.exists(csv_file_name_source):
        log(f"Invalid file => {csv_file_name_source}")
        raise Exception("File not found")

    # Convert csv encoding from 'utf-16-le' to 'utf-8'
    try:
        with open(csv_file_name_source, "r", encoding = "utf-8") as sourceFile:
            log("Opening source file..")
            with open(csv_file_name, "w", encoding = csv_text_encoding) as targetFile:
                log("Reading source file..")
                contents = sourceFile.read()
                log("Saving output file..")
                targetFile.write(contents)
                log("Saving output file..Done!")

    except Exception as e:
        log_err("CSV Encoding error", e)
        raise Exception("CSV Encoding error")

    # Get delimeter from csv file
    try:
        #csv_contents: str = ""
        remove_first_row: bool = False
        with open(csv_file_name, 'rt', encoding = csv_text_encoding) as f:
            first_line = f.readline().strip('\n').strip().strip('"')
            log(f"First line => {str(first_line)}")
            
            first_line_split = first_line.split("=")
            log(f"First line split => {str(first_line_split)}")

            if len(first_line_split) > 1:
                first_line_right = str(first_line_split[1])
                sep = first_line_right.replace("\"", "").strip()
                log(f"Separator => {sep}")

                remove_first_row = True

        #Remove first line
        if remove_first_row:
            pop_first_line(csv_file_name)
            log("Removed first row for separator")

    except Exception as e:
        sep = ","
        log_err("CSV delimeter error", e)
        raise Exception("CSV Delimeter error")

    # Read CSV file
    try:
        with open(csv_file_name, 'rt', encoding = csv_text_encoding, newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=sep)
            #csv_reader = csv.DictReader(csv_file)
            line_count: int = -1

            headers = next(csv_reader)
            log(f"Headers => {str(headers)}")
            for row in csv_reader:
                line_count = line_count + 1
                if line_count < 0:
                    log(f"L{line_count}; empty line => {str(row)}")
                #elif line_count == 1:
                #    log(f'Column names are {", ".join(row)}')
                else:
                    card_folder_name = str(row[index_folder_name])
                    row_card_name = str(row[index_cardname])
                    is_ae = card_folder_name.strip().startswith("AE")
                    is_ocg = card_folder_name.strip().startswith("OCG")
                    card_format = "OCG" if is_ocg else "TCG"
                    if is_ae:
                        card_format = "AE"
                    elif is_ocg:
                        card_format = "OCG"
                    else:
                        is_tcg = True
                        card_format = "TCG"
                    
                    log(f"\tL{line_count}; Processing {row_card_name} with cardset '{row[index_cardnumber]}'")
                    card_count += 1
                    # Initialize new card object
                    card_setcode = str(row[index_cardnumber])
                    card_setname = str(row[index_set_name])
                    card_setcode_split = card_setcode.split('-')
                    card_rarity = str(row[index_rarity])
                    card_printing = str(row[index_printing])
                    card_qty = int(row[index_qty])
                    new_card_object = {
                        "name": row_card_name,
                        "set": card_setcode,
                        "set_global": f"{ card_setcode_split[0] }-{ str(card_setcode_split[1])[2:] }",
                        "qty": card_qty,
                        "trade_qty": int(row[index_tradeqty]),
                        "format": card_format
                    }
                    if card_folder_name not in folder_skip:
                        cards.append(new_card_object)
                        if is_ocg:
                            cards_ocg.append(new_card_object)
                        elif is_ae:
                            cards_ocg.append(new_card_object)
                            cards_ae.append(new_card_object)
                        else:
                            cards_tcg.append(new_card_object)

                    # Add to listings
                    #if card_folder_name in folder_listing: # Check condition for listing
                    if is_tcg and card_rarity != "Common": # Check condition for listing
                        price_low: float = round(float(row[index_price_low]) * price_conversion_php, 2) if row[index_price_low] else 0
                        price_mid: float = round(float(row[index_price_mid]) * price_conversion_php, 2) if row[index_price_mid] else 0
                        price_market: float = round(float(row[index_price_market]) * price_conversion_php, 2) if row[index_price_market] else 0
                        new_obj_listing = {
                        "name": f"Yu-Gi-Oh! { card_format } { row_card_name } ({ card_setcode } { card_rarity })",
                        "qty": card_qty,
                        "desc": f"""Yugioh { card_format } card
                            Name: { row_card_name }
                            Set: { card_setname }
                            Edition: { card_printing }
                            Condition: Near Mint

                            (Price based on yugiohprices.com)""".replace('                        ', ''), # looks ugly but necessary to prevent useless whitespaces.
                        
                        "price_low": price_low,
                        "price_mid": price_mid,
                        "price_market": index_price_market,
                        "rarity" : card_rarity
                        }
                        # Add to list
                        card_listings.append(new_obj_listing)

    except Exception as e:
        log_err("CSV file error", e)
        raise Exception("CSV File error")
        
    log(f"Processed {card_count} cards.")

    # Process All cards OCG/TCG
    write_json(export_json_file_name[index_all], cards)
    log(f"Exported OCG/TCG card list.")

    write_json(jsonfile_listings[index_all], card_listings)
    log(f"Exported OCG/TCG listings.")

    process_card_list("OCG/TCG", export_json_file_name[index_all], jsonfile_card_conf_list[index_all], jsonfile_cards_with_error[index_all], export_conf_file[index_all])

    #"""
    # Process OCG cards
    write_json(export_json_file_name[index_ocg], cards_ocg)
    log(f"Exported OCG card list.")

    process_card_list("OCG", export_json_file_name[index_ocg], jsonfile_card_conf_list[index_ocg], jsonfile_cards_with_error[index_ocg], export_conf_file[index_ocg])
    #"""

    #"""
    # Process AE cards
    write_json(export_json_file_name[index_ae], cards_ae)
    log(f"Exported AE card list.")

    process_card_list("AE", export_json_file_name[index_ae], jsonfile_card_conf_list[index_ae], jsonfile_cards_with_error[index_ae], export_conf_file[index_ae])
    #"""

    #"""
    # Process TCG cards
    write_json(export_json_file_name[index_tcg], cards_tcg)
    log(f"Exported TCG card list.")

    write_json(jsonfile_listings[index_tcg], card_listings)
    log(f"Exported TCG listings.")

    process_card_list("TCG", export_json_file_name[index_tcg], jsonfile_card_conf_list[index_tcg], jsonfile_cards_with_error[index_tcg], export_conf_file[index_tcg])
    #"""


except Exception as e:
    log_err("Error, main", e)
