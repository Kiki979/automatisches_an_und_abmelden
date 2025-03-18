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

def send_push_notification(message, login_time):
    """Sendet eine Push-Nachricht mit der Login-Zeit."""
    full_message = f"{message} {login_time}"

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    data = urllib.parse.urlencode({
        "token": os.getenv('TOKEN'), 
        "user": os.getenv('USER'),  
        "title": "Anmeldung",
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
    time.sleep(2)

    # Login
    username_field = driver.find_element(By.ID, 'username')
    username_field.send_keys(os.getenv('USERMAIL'))

    password_field = driver.find_element(By.ID, 'password')
    password_field.send_keys(os.getenv('PASSWORD'))

    login_button = driver.find_element(By.ID, 'loginbtn')
    login_button.click()

    # Warte
    time.sleep(2)

    # Alert schließen (falls vorhanden)
    try:
        alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        print("Alert wurde akzeptiert.")
    except TimeoutException:
        print("Kein Alert vorhanden.")

    # "Blockleiste öffnen" Button klicken
    try:
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Blockleiste öffnen']/parent::button"))
        )
        button.click()
        print("Button 'Blockleiste öffnen' wurde geklickt.")
    except TimeoutException:
        print("Button 'Blockleiste öffnen' nicht klickbar oder nicht vorhanden.")

    # "Homeoffice" Radio-Button aktivieren
    try:
        homeoffice_radio_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "flexRadioDefault1"))
        )
        if not homeoffice_radio_button.is_selected():
            homeoffice_radio_button.click()
            print("Radio-Button 'Homeoffice' wurde aktiviert.")
        else:
            print("Radio-Button 'Homeoffice' war bereits aktiviert.")
    except TimeoutException:
        print("Radio-Button 'Homeoffice' nicht gefunden.")

    # Überprüfen, ob "Beenden" vorhanden ist
    try:
        beenden_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Beenden' and contains(@class, 'btn btn-primary')]"))
        )
        print("Button 'Beenden' ist sichtbar, 'Starten' wird nicht geklickt.")
    except TimeoutException:
        print("Button 'Beenden' nicht gefunden, versuche 'Starten' zu klicken.")
        
        # Falls "Beenden" nicht vorhanden ist -> "Starten" klicken
        try:
            submit_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"][value="Starten"]'))
            )
            submit_button.click()
            print("Button 'Starten' wurde geklickt.")
            time.sleep(1)
        except TimeoutException:
            print("Fehler: 'Starten' Button nicht gefunden oder nicht klickbar.")
        except Exception as e:
            print(f"Fehler beim Klicken von 'Starten': {e}")
            print("Vermutlich bereits angemeldet.")

    # Warte
    time.sleep(5)

    # Login-Zeit auslesen
    try:
        card_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "card-text"))
        )
        text_content = card_text.text

        # Regex zur Extraktion der Startzeit (Login-Zeit)
        match = re.search(r"Startzeit\s*:\s*(\d{2}:\d{2})", text_content)

        if match:
            login_time = match.group(1)
            print(f"Login-Zeit gefunden: {login_time}")

            # Beispielaufruf der Funktion mit einer Nachricht
            send_push_notification("Erfolgreich um: ", login_time)
        else:
            print("Keine Login-Zeit gefunden.")
            send_push_notification("Erfolgreich angemeldet, aber keine Zeit gefunden")          


    except TimeoutException:
        print("Fehler: Login-Zeit nicht gefunden.")

except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

finally:
    # Browser nach kurzer Wartezeit schließen
    time.sleep(1)
    driver.quit()
