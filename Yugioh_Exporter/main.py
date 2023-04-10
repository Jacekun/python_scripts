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
        with open(filename, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        log_err("Error", e)
        return False

def write_json(filename: str, content: any) -> bool:
    try:
        with open(filename, 'w') as f:
            json.dump(content, f)
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
# Main
try:
    # Constants
    folder_setcodes = "setcodes"
    route_setcode = "https://db.ygoprodeck.com/api/v7/cardsetsinfo.php?setcode={0}&includeAliased&num=1&offset=0"
    index_cardname: int = 3
    index_cardnumber: int = 6
    index_qty: int = 1
    index_folder_name: int = 0
    index_tradeqty: int = 2

    # File paths
    csv_file_name: str = "all-folders.csv"
    export_json_file_name: str = "cards.json"
    export_conf_file: str = "MyCards.lflist.conf"
    jsonfile_cards_with_error: str = "cards_with_error.json"
    jsonfile_card_conf_list: str = "conf_cards.json"

    # Variables
    card_count: int = 0
    sep: str = ","
    conf_contents: str = "#[My Cards]\n!My Cards\n$whitelist\n"
    skip_folders: any = ['OCG', 'Rush']

    cards: list[any] = [] # List of all cards from Imported csv file
    cards_with_error: list[any] = [] # List of all cards with error
    card_conf_list: list[any] = [] # List of all card to be put to conf file.

    # Dynamic variables for local use
    jsonfile_setcode: str = ""
    card_setcode: str = ""
    row_card_name: str = ""
    card_folder_name: str = ""
    card_setcode_split: any = None
    card_json: any = None
    card_json_setcode: any = None
    req_object: any = None
    temp_object: any = None
    is_request: bool = False

    # Create necessary folders
    Path(folder_setcodes).mkdir(parents=True, exist_ok=True)

    # Ask for export file
    csv_file_name = "all-folders"#input("DragonShield export file name => ")

    # Verify file
    if not csv_file_name.endswith(".csv"):
        csv_file_name += ".csv"

    #csv_file_name = os.path.join(".", csv_file_name)
    log(f"DragonShield Export File => {csv_file_name}")

    if not os.path.exists(csv_file_name):
        log(f"Invalid file => {csv_file_name}")
        pass

    # Get delimeter from csv file
    try:
        remove_first_row: bool = False
        with open(csv_file_name, 'rt', encoding='utf-8') as f:
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
        #if remove_first_row:
        #    pop_first_line(csv_file_name)
        #    log("Removed first row for separator")

    except Exception as e:
        sep = ","
        log_err("CSV delimeter error", e)

    # Read CSV file
    try:
        with open(csv_file_name, 'rt', encoding='utf-8', newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=sep)
            #csv_reader = csv.DictReader(csv_file)
            line_count: int = -1
            for row in csv_reader:
                line_count = line_count + 1
                if line_count <= 1:
                    log(f"L{line_count}; empty line => {str(row)}")
                #elif line_count == 1:
                #    log(f'Column names are {", ".join(row)}')
                else:
                    card_folder_name = str(row[index_folder_name])
                    row_card_name = str(row[index_cardname])
                    if card_folder_name not in skip_folders:
                        log(f"\tL{line_count}; Processing {row_card_name} with cardset '{row[index_cardnumber]}'")
                        card_count += 1
                        # Initialize new card object
                        card_setcode = str(row[index_cardnumber])
                        card_setcode_split = card_setcode.split('-')
                        new_card_object = {
                            "name": row_card_name,
                            "set": card_setcode,
                            "set_global": f"{card_setcode_split[0]}-{str(card_setcode_split[1])[2:]}",
                            "qty": int(row[index_qty]),
                            "trade_qty": int(row[index_tradeqty])
                        }
                        cards.append(new_card_object)
                    else:
                        log(f"Skip card from folder => {card_folder_name}; {row_card_name}")
    except Exception as e:
        log_err("CSV file error", e)
        
    log(f"Processed {card_count} cards.")

    write_json(export_json_file_name, cards)
    log(f"Exported to file => {export_json_file_name}")

    # Read from JSON file and request card passcode
    card_json = read_json(export_json_file_name)

    if card_json is not None:
        log("JSON file loaded!")

        for entry in card_json:
            card_name = str(entry["name"])
            card_setcode = str(entry["set"])
            card_qty = int(entry["qty"])
            card_trade_qty = int(entry["trade_qty"])
            card_id: str = ""
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
            
            # Sleep for 50 milliseconds, if request is made
            if is_request:
                sleep(0.05)
            
            #break

            # Read setcode info
            if os.path.exists(jsonfile_setcode):
                is_already_exist = False
                card_id: int = 0
                card_name: str = ""
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

except Exception as e:
    log_err("Error, main", e)
