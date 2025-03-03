from sys import platform
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup as bs
import requests
from datetime import datetime
from slack_sdk import WebClient
from PIL import Image
from os import getenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint
from pathlib import Path
import re

"""
TODOs:
Download image from story every day
Crop image to where content is
Get info from every other food place website
Create text with every food place
Write text into slack bot
Attach image to slack bot
Send slack bot message in right channel

places to scrape:
bryggan
lemani
finn ut
ica????
mop
taste the chinese?
"""

# CONSTANTS
PROJECT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = ""


def get_weekday(date=None):
    # Get today's weekday number (0 = Monday, 6 = Sunday)
    if date:
        weekday_number = date.weekday()
    else:
        weekday_number = datetime.today().weekday()

    # List of weekdays in Swedish
    weekdays = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]

    # Print today's weekday in Swedish
    return weekdays[weekday_number]


def get_date():
    # Format the current date as "day month" in Swedish (e.g., "28 oktober")
    chosen_date = datetime.now().strftime("%-d %B").lower()

    months_translation = {
        "january": "januari",
        "february": "februari",
        "march": "mars",
        "april": "april",
        "may": "maj",
        "june": "juni",
        "july": "juli",
        "august": "augusti",
        "september": "september",
        "october": "oktober",
        "november": "november",
        "december": "december"
    }
    for eng_month, swe_month in months_translation.items():
        if eng_month in chosen_date.lower():
            chosen_date = chosen_date.lower().replace(eng_month, swe_month)

    return chosen_date


def scrape_mop():
    url = "https://morotenopiskan.se/"
    response = requests.get(url)
    with open("results.html", "w", encoding="utf-8") as file:
        file.write(response.text)
    html = response.content
    soup = bs(html, "lxml")
    all_info = soup.find("div", "event-info")
    food_list = all_info.find_all("p")

    i, j = 0, 0
    green = food_list[i].text
    normal = food_list[j].text

    while "gröna" not in green.lower():
        i += 1
        green = food_list[i].text
    while "dagens" not in normal.lower() or "gröna" in normal.lower():
        j += 1
        normal = food_list[j].text

    if "dagens" not in green.lower() or "dagens" not in normal.lower():
        exit("Error on mop check consistency")

    return f"\n{normal}\n{green}"


def scrape_bryggan():
    url = "https://mersmak.me/vara-stallen/bryggan/"
    response = requests.get(url)
    content = response.content
    soup = bs(content, "lxml")

    # Get todays weekday in Swedish
    week_day = get_weekday()

    pattern = re.compile(r"LUNCHMENY", re.IGNORECASE)
    result = soup.find(string=pattern)
    foods = result.next.next.text

    foods_list = foods.split("\n")

    rel_index = foods_list.index(week_day)
    foods = foods_list[rel_index + 1: rel_index + 3]

    return "\n".join(foods)



def scrape_finnut():
    chosen_date = get_date()

    # URL to scrape
    url = "https://www.finnut.se/"

    options = webdriver.FirefoxOptions()
    options.add_argument("-profile")

    options.add_argument(PROFILE_DIR)
    options.add_argument("--headless")
    # Open the URL

    if platform == "darwin":
        # path for testing on mac
        driver = webdriver.Firefox(options=options)
    elif platform == "linux":
        geckodriver_path = "/snap/bin/geckodriver"
        driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
        driver = webdriver.Firefox(options=options, service=driver_service)
    else:
        raise EnvironmentError("Provide path to profile")

    driver.get(url)

    # Loop to find the chosen date or navigate to the next week
    found_date = False
    attempts = 0  # Counter to prevent infinite loops

    while not found_date and attempts < 10:  # Limit to 10 attempts for safety
        # Wait for page elements to load
        time.sleep(2)

        # Locate all weekday menu entries
        menu_entries = driver.find_elements(By.CSS_SELECTOR, "div.week-menu-entry")

        # Loop through each entry to check for the chosen date
        for entry in menu_entries:
            date = entry.find_element(By.CSS_SELECTOR, "div.col-md-2 em").text
            if date == chosen_date:
                # If date is found, retrieve and print the food information
                weekday = entry.find_element(By.CSS_SELECTOR, "div.col-md-2 strong").text
                food_info = entry.find_element(By.CSS_SELECTOR, "div.menu-entry-content").text
                # print(f"Finn ut {weekday} {date}:\n{food_info}\n")
                found_date = True
                driver.quit()
                return f"{food_info}\n\n"

        # If date is not found, click the "next week" button to navigate forward
        if not found_date:
            next_week_button = driver.find_element(By.CSS_SELECTOR, "a i.fa.fa-chevron-circle-right")
            next_week_button.click()
            attempts += 1

    # Close the browser
    driver.quit()
    raise RuntimeError("Didnt find food")


def scrape_lemani():
    # LE MANI TIME
    url = "https://www.instagram.com/stories/lemanilund"
    print("Trying Le mani")

    # Get the absolute path to the project directory
    #project_dir = Path(__file__).resolve().parent

    options = webdriver.FirefoxOptions()
    options.add_argument("-profile")
    options.add_argument(PROFILE_DIR)
    options.add_argument("--headless")
    options.add_argument("--enable-javascript")
    options.add_argument("--incognito")
    options.add_argument("--nogpu")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1280")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-blink-features=AutomationControlled')

    if platform == "darwin":
        # path for testing on mac
        driver = webdriver.Firefox(options=options)
    elif platform == "linux":
        geckodriver_path = "/snap/bin/geckodriver"
        driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)
        driver = webdriver.Firefox(options=options, service=driver_service)
    else:
        raise EnvironmentError("Provide path to profile")
    print("Webdriver created.")

    driver.get(url)
    print("Url received.")

    # In case cookies for some reason reset
    try:
        wait = WebDriverWait(driver, 3)
        button_def = (By.XPATH, "//button[text()='Tillåt alla cookies']")
        button = wait.until(EC.element_to_be_clickable(button_def))
        button.click()
        print("Clicked cookie")
        time.sleep(2)
    except (NoSuchElementException, TimeoutException):
        try:
            wait = WebDriverWait(driver, 3)
            button_def = (By.XPATH, "//button[text()='Allow all cookies']")
            button = wait.until(EC.element_to_be_clickable(button_def))
            button.click()
            print("Clicked cookie")
            time.sleep(2)
        except (NoSuchElementException, TimeoutException):
            print("No cookie option")
            pass

    time.sleep(1)

    try:
        driver.find_element(By.XPATH, '//div[text()="Visa händelse"]').click()
        print("Shown story")
    except NoSuchElementException:
        try:
            driver.find_element(By.XPATH, '//div[text()="View story"]').click()
            print("Shown story")
        except NoSuchElementException:
            # TODO implement a check to see if breaking or just no story.
            print("Story could not be found, not adding picture.")
            driver.quit()

            return 1

    time.sleep(1)

    print("Saving lemani screenshot")
    driver.get_screenshot_as_file(f'{PROJECT_DIR}/lemani.png')

    driver.quit()

    with Image.open(f"{PROJECT_DIR}/lemani.png") as im:
        # Size of the image in pixels (size of original image)
        # (This is not mandatory)
        width, height = im.size

        # Setting the points for cropped image
        left = 400
        top = 0
        right = 850
        bottom = height

        # Cropped image of above dimension
        # (It will not change original image)
        im1 = im.crop((left, top, right, bottom))

        im1.save(f"{PROJECT_DIR}/lemani.png")


    print("Le mani succeeded")
    return 0


def send_message(msg, attachments=None):
    #find_week_day()
    token = getenv("token")
    # Set up a WebClient with the Slack OAuth token
    client = WebClient(token=token)
    # print(client.conversations_list())
    meme_num = randint(0, 28)

    # Get the absolute path to the project directory
    #project_dir = Path(__file__).resolve().parent

    # Get random meme
    meme = f"{PROJECT_DIR}/memes/meme_{meme_num}.png"

    # Bot channel: C08CZLA7CE6

    # If image was successfully collected attach it, otherwise sent message without.
    # Add description to say it failed to collect image.

    if not attachments:
        files = [
            {
                "file": meme,
                "title": "Relevant meme"
            }
        ]
    elif len(attachments) == 1:
        file = attachments[0]
        files = [
            {
                "file": file,
                "title": file.split("/")[-1].removesuffix(".png")
            },

            {
                "file": meme,
                "title": "Relevant meme"
            }
        ]

    else:
        files = []
        for file_name in attachments:
            dict_obt = {
                "file": file_name,
                "title": "Relevant meme"
            }

            files.append(dict_obt)

    client.files_upload_v2(
        file_uploads=files,
        channel=getenv("channel"),
        initial_comment=msg #+ " meme dedicated to @NA" if meme_num == 4 else msg
    )


def main():
    global PROFILE_DIR
    #project_dir = Path(__file__).resolve().parent

    # Check if os is mac
    if platform == "darwin":
        # path for testing on mac
        PROFILE_DIR = "Users/william/Library/Application Support/Firefox/Profiles/zkr8w5jt.default-release"
    elif platform == "linux":
        # path for ubuntu server
        PROFILE_DIR = "/home/william/FoodScraperProject/zkr8w5jt.default-release"
    else:
        raise EnvironmentError("Provide path to profile")
    attachments = []

    lemani_code = scrape_lemani()
    print("Status:", lemani_code)

    if lemani_code == 0:
        attachments.append(f"{PROJECT_DIR}/lemani.png")

    # Bad temporary code
    # TODO fix proper error handling and error codes
    try:
        print("Trying finnut")
        finnut = scrape_finnut()
        print("Finnut fine")
    except Exception as e:
        finnut = "Ice cream (finnut) machine broke. Have a good day.:wetwig:\n"
        print("Finn ut died")
        print(e)
        meme = f"{PROJECT_DIR}/memes/finnut_broke.png"
        attachments.append(meme)

    try:
        print("Trying MoP")
        mop = scrape_mop()
        print("MoP fine")
    except Exception:
        mop = "Ice cream (mop) machine broke. Have a good day.:wetwig:\n"
        meme = f"{PROJECT_DIR}/memes/mop_broke.png"
        attachments.append(meme)
    try:
        print("Trying bryggan")
        bryggan = scrape_bryggan()
        print("Bryggan fine")
    except Exception:
        print("Bryggan no work")
        bryggan = ""

    if lemani_code == 0:  # successfully got le mani
        lemani = "*Le mani pasta för dagen:*"
    elif lemani_code == 1:  # failed to get le mani
        lemani = "*Kunde inte hämta Le mani, ingen story upplagd. Cry about it.*"
    else:
        raise ValueError("Unhandled code")

    title = f"*Luncherbjudanden {get_date()}:*"

    mop_title = "*Moroten och Piskan:*"
    finnut_title = "*Finn ut:*"
    bryggan_title = "*Bryggan:*"

    mop_part = f"{mop_title}\n{mop}"
    finnut_part = f"{finnut_title}\n{finnut}"
    bryggan_part = f"{bryggan_title}\n{bryggan}"

    if bryggan != "":
        msg = f"{title}\n\n{finnut_part}\n\n{mop_part}\n\n{bryggan_part}\n\n{lemani}"
    else:
        msg = f"{title}\n\n{finnut_part}\n\n{mop_part}\n\n{lemani}"

    # Send message with potential image attachment(s?)
    send_message(msg, attachments)


if __name__ == "__main__":
    main()
