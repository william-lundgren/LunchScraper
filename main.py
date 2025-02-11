from sys import platform
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup as bs
import requests
from datetime import datetime
from slack_sdk import WebClient
from date import find_week_day
from PIL import Image
from os import getenv

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

    return f"*Moroten och Piskan*:\n{normal}\n{green}"

def test():
    import undetected_chromedriver as uc

    driver = uc.Chrome(headless=True)
    driver.get("https://instagram.com/stories/karsbergruben")
    driver.save_screenshot("test.png")
    print(driver.page_source)
    driver.quit()


def scrape_finnut(profile_dir):
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
                #print(f"Finn ut {weekday} {date}:\n{food_info}\n")
                found_date = True
                driver.quit()
                return f"*Luncherbjudanden {weekday} {date}:*\n\n*Finn ut:*\n{food_info}\n\n"

        # If date is not found, click the "next week" button to navigate forward
        if not found_date:
            next_week_button = driver.find_element(By.CSS_SELECTOR, "a i.fa.fa-chevron-circle-right")
            next_week_button.click()
            attempts += 1

    # Close the browser
    driver.quit()


def scrape_lemani(profile_dir):
    # LE MANI TIME
    url = "https://www.instagram.com/stories/lemanilund"

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
    driver.get(url)

    # In case cookies for some reason reset
    try:
        driver.find_element(By.XPATH, '//div[text()="Tillåt alla cookies"]').click()
    except NoSuchElementException:
        try:
            driver.find_element(By.XPATH, '//div[text()="Allow all cookies"]').click()
        except NoSuchElementException:
            pass

    time.sleep(1)

    try:
        driver.find_element(By.XPATH, '//div[text()="Visa händelse"]').click()
    except NoSuchElementException:
        try:
            driver.find_element(By.XPATH, '//div[text()="View story"]').click()
        except NoSuchElementException:
            print("not found")
            driver.quit()

            return 1

    time.sleep(1)
    driver.get_screenshot_as_file('lemani.png')
    driver.quit()

    with Image.open("lemani.png") as im:
        # Size of the image in pixels (size of original image)
        # (This is not mandatory)
        width, height = im.size

        # Setting the points for cropped image
        left = 450
        top = 0
        right = 817
        bottom = height

        # Cropped image of above dimension
        # (It will not change original image)
        im1 = im.crop((left, top, right, bottom))

        im1.save("lemani.png")
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


def send_message(msg, img=None):
    token = getenv("token")
    # Set up a WebClient with the Slack OAuth token
    client = WebClient(token=token)
    print(client.conversations_list())

    #Send message with attachment
    if img:
        client.files_upload_v2(
            channel="C1ZHAEJ8N",
            file=img,
            title="Le mani meny",
            initial_comment=msg,
            username="LunchTime"
        )
    else:
        client.files_upload_v2(
            channel="C1ZHAEJ8N",
            initial_comment=msg,
            username="LunchTime"
        )


def main():
    weekend = ("Saturday", "Sunday")

    # day of format YYYY-MM-DD
    day = datetime.today().strftime('%Y-%m-%d')

    # Dont post on weekends
    if find_week_day(day) in weekend:
        pass
        #return

    # Check if os is mac
    if platform == "darwin":
        # path for testing on mac
        profile_dir = "Users/william/Library/Application Support/Firefox/Profiles/zkr8w5jt.default-release"
    elif platform == "linux":
        # path for ubuntu server
        profile_dir = "/home/william/FoodScraperProject/zkr8w5jt.default-release"
    else:
        raise EnvironmentError("Provide path to profile")

    mop = scrape_mop()
    status = scrape_lemani(profile_dir)
    finnut = scrape_finnut(profile_dir)

    print(mop)
    print(status)
    print(finnut)

    img = "lemani.png"

    if status == 1:  # failed to get le mani
        msg = f"{finnut}\n{mop}"
        #send_message(msg)
        print(msg)
    elif status == 0:
        msg = f"{finnut}\n{mop}\n\n\n*Le mani pasta för dagen:*"
        #send_message(msg, img)
        print(msg)


if __name__ == "__main__":
    main()
