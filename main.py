from sys import platform
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup as bs
import requests
from datetime import datetime
from slack_sdk import WebClient
from date import find_week_day
from PIL import Image
from os import getenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint
from pathlib import Path

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
    # print("foodlist:")
    # for i in food_list:
    #     print(i.text)
    i, j = 1, 1
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


def scrape_finnut(profile_dir):
    chosen_date = get_date()
    print(chosen_date)

    # URL to scrape
    url = "https://www.finnut.se/"

    options = webdriver.FirefoxOptions()
    options.add_argument("-profile")

    options.add_argument(profile_dir)
    options.add_argument("--headless")
    # Open the URL

    driver = webdriver.Firefox(options=options)
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


def scrape_lemani(profile_dir):
    # LE MANI TIME
    url = "https://www.instagram.com/stories/lemanilund"
    print("Trying Le mani")

    options = webdriver.FirefoxOptions()
    options.add_argument("-profile")
    options.add_argument(profile_dir)
    options.add_argument("--headless")
    options.add_argument("--enable-javascript")
    options.add_argument("--incognito")
    options.add_argument("--nogpu")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1280")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Firefox(options=options)
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
    driver.get_screenshot_as_file('lemani.png')

    driver.quit()

    with Image.open("lemani.png") as im:
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

        im1.save("lemani.png")

    print("Le mani succeeded")
    return 0


def scrape_bryggan():
    # Start the WebDriver and open the webpage
    driver = webdriver.Firefox()
    driver.get("https://mersmak.me/vara-stallen/bryggan/")

    # Get today's weekday in Swedish with capitalized translations
    weekday_translation = {
        "monday": "Måndag",
        "tuesday": "Tisdag",
        "wednesday": "Onsdag",
        "thursday": "Torsdag",
        "friday": "Fredag",
        "saturday": "Lördag",
        "sunday": "Söndag"
    }
    current_weekday = datetime.now().strftime("%A").lower()  # e.g., "monday"
    swedish_weekday = weekday_translation[current_weekday]

    # Wait for page elements to load
    time.sleep(3)

    # Locate and extract the menu for the current day
    try:
        # Find the element that contains today's weekday in Swedish
        day_container = driver.find_element(By.XPATH, f"//*[contains(text(), '{swedish_weekday}')]")

        # Locate the specific food information element for the current weekday
        food_info = day_container.find_element(By.XPATH, "following-sibling::div[1]").text

        print(f"Menu for {swedish_weekday}:\n{food_info}")
    except Exception as e:
        print(f"Could not find menu for {swedish_weekday}: {e}")
        food_info = "No menu found."

    # Close the WebDriver
    driver.quit()

    return food_info


def bryggan_bs4():
    # Fetch the webpage content
    url = "https://mersmak.me/vara-stallen/bryggan/"
    response = requests.get(url)
    soup = bs(response.content, 'html.parser')

    # Get today's weekday in Swedish with capitalized translations
    weekday_translation = {
        "monday": "Måndag",
        "tuesday": "Tisdag",
        "wednesday": "Onsdag",
        "thursday": "Torsdag",
        "friday": "Fredag",
        "saturday": "Lördag",
        "sunday": "Söndag"
    }
    current_weekday = datetime.now().strftime("%A").lower()  # e.g., "monday"
    swedish_weekday = weekday_translation[current_weekday]

    # Find today's menu based on the Swedish weekday
    try:
        # Locate the element containing today's weekday name
        day_container = soup.find(lambda tag: tag.name == "div" and swedish_weekday in tag.get_text())

        # If we find the weekday container, get its parent's next sibling containing the menu
        if day_container and day_container.parent:
            # Locate the sibling that should contain the food information
            food_info = day_container.find_next_sibling("div").get_text(strip=True)
            print(f"Menu for {swedish_weekday}:\n{food_info}")
        else:
            print(f"Could not find menu for {swedish_weekday}.")
    except Exception as e:
        print(f"An error occurred: {e}")


def send_message(msg, attachments=None):
    #find_week_day()
    token = getenv("token")
    # Set up a WebClient with the Slack OAuth token
    client = WebClient(token=token)
    # print(client.conversations_list())
    meme_num = randint(0, 28)

    # Get the absolute path to the project directory
    project_dir = Path(__file__).resolve().parent

    # Get random meme
    meme = f"{project_dir}/memes/meme_{meme_num}.png"

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
    project_dir = Path(__file__).resolve().parent

    # Check if os is mac
    if platform == "darwin":
        # path for testing on mac
        profile_dir = "Users/william/Library/Application Support/Firefox/Profiles/zkr8w5jt.default-release"
    elif platform == "linux":
        # path for ubuntu server
        profile_dir = "/home/william/FoodScraperProject/zkr8w5jt.default-release"
    else:
        raise EnvironmentError("Provide path to profile")
    attachments = []

    lemani_code = scrape_lemani(profile_dir)
    print("Status:",lemani_code)
    if lemani_code == 0:
        attachments.append(f"{project_dir}/lemani.png")

    try:
        print("Trying finnut")
        finnut = scrape_finnut(profile_dir)
    except Exception as e:
        finnut = "Ice cream (finnut) machine broke. Have a good day.:wetwig:\n"
        print("Finn ut died")
        print(e)
        meme = f"{project_dir}/memes/finnut_broke.png"
        attachments.append(meme)
    try:
        mop = scrape_mop()
    except Exception:
        mop = "Ice cream (mop) machine broke. Have a good day.:wetwig:\n"
        meme = f"{project_dir}/memes/mop_broke.png"
        attachments.append(meme)

    # print(mop)
    # print(status)
    # print(finnut)

    if lemani_code == 0:  # successfully got le mani
        lemani = "*Le mani pasta för dagen:*"
    elif lemani_code == 1:  # failed to get le mani
        lemani = "*Kunde inte hämta Le mani, ingen story upplagd. Cry about it.*"
    else:
        raise ValueError("Unhandled code")

    title = f"*Luncherbjudanden {get_date()}:*"

    mop_title = "*Moroten och Piskan:*"
    finnut_title = "*Finn ut:*"

    mop_part = f"{mop_title}\n{mop}"
    finnut_part = f"{finnut_title}\n{finnut}"

    msg = f"{title}\n\n{finnut_part}\n\n{mop_part}\n\n\n{lemani}"

    # Send message with potential image attachment(s?)
    send_message(msg, attachments)


if __name__ == "__main__":
    main()
