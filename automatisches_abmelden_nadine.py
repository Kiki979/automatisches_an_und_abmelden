from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import http.client
import urllib
import time
import re
from datetime import datetime
import os
from dotenv import load_dotenv

# .env-Datei laden
load_dotenv()

def send_push_notification(message, logout_time=None):
    full_message = f"{message} {logout_time}"

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    data = urllib.parse.urlencode({
        "token": os.getenv('TOKEN'), 
        "user": os.getenv('USER'),  
        "title": "Abmeldung",
        "message": full_message,
        "priority": "1",  
        "sound": "magic"  
    })
    headers = { "Content-type": "application/x-www-form-urlencoded" }
    
    conn.request("POST", "/1/messages.json", data, headers)
    response = conn.getresponse()

    if response.status == 200:
        print("Push-Nachricht erfolgreich gesendet!")
    else:
        print(f"Fehler beim Senden der Push-Nachricht: {response.status}")
        print("Antwort:", response.read().decode())

# Automatische Verwaltung von ChromeDriver
chrome_options = Options()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Öffne die Webseite
    driver.get(os.getenv('PLATTFORM'))

    # Warte, bis die Seite geladen ist
    time.sleep(2)

    username_field = driver.find_element(By.ID, 'username')
    username_field.send_keys(os.getenv('USERMAIL'))

    password_field = driver.find_element(By.ID, 'password')
    password_field.send_keys(os.getenv('PASSWORD'))

    # Login-Button klicken
    login_button = driver.find_element(By.ID, 'loginbtn')
    login_button.click()

    # Warte
    time.sleep(2)

    # Versuche, das "Blockleiste öffnen" Button zu klicken
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Blockleiste öffnen']/parent::button"))
        )
        button.click()
        print("Button 'Blockleiste öffnen' erfolgreich geklickt.")
    except TimeoutException:
        print("Button 'Blockleiste öffnen' nicht gefunden oder nicht klickbar.")

    try:
        # Überprüfen, ob "Beenden" vorhanden ist
        beenden_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@class='btn btn-primary' and text()='Beenden']"))
        )

        if beenden_button.is_enabled():
            beenden_button.click()
            print("Beenden button clicked.")
        else:
            print("Beenden button is present but not clickable.")

    except:
        print("Beenden button not found or not clickable.")

    # Warte
    time.sleep(5)

    # Logout-Zeit auslesen
    try:
        card_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "card-text"))
        )
        text_content = card_text.text
        print("Inhalt des card-text-Elements:", text_content)

        # Regex zur Extraktion der Endzeit (Logout-Zeit)
        match = re.search(r"Endzeit\s*:\s*(\d{2}:\d{2})", text_content)
        
        if match:
            logout_time = match.group(1)
            print(f"Logout-Zeit gefunden: {logout_time}")

            # Push-Nachricht mit Logout-Zeit senden
            send_push_notification("Erfolgreich um:", logout_time)          
        else:
            print("Keine Logout-Zeit gefunden.")
            send_push_notification("Erfolgreich abgemeldet, aber keine Zeit gefunden")          

    except TimeoutException:
        print("Fehler: Logout-Zeit nicht gefunden.")
        send_push_notification("Fehler: Logout-Zeit konnte nicht ermittelt werden")

finally:
    # Browser nach kurzer Wartezeit schließen
    time.sleep(1)
    driver.quit()
