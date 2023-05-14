import logging
import os
import subprocess
import time
from platform import system

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# Settings applicable to an individual
CITIZENSHIP_COUNTRY_TEXT = "Kanada"
PERSON_COUNT_TEXT = "eine Person"
NOT_WITH_FAMILY_TEXT = "nein"
EXTEND_RESIDENCE_PERMIT_BUTTON_XPATH = '//*[@id="xi-div-30"]/div[2]/label/p'
FAMILY_GROUNDS_ACCORDION_XPATH = '//*[@id="inner-348-0-2"]/div/div[5]/label/p'
FAMILY_OF_SKILLED_WORKER_RADIO_BUTTON_XPATH = (
    '//*[@id="inner-348-0-2"]/div/div[6]/div/div[1]/label'
)

# General configuration
START_PAGE_URL = "https://otv.verwalt-berlin.de/ams/TerminBuchen"
WEBSITE_ERROR_RESPONSE = (
    """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""
)
WAV_FILE_PLAYER = "/usr/bin/aplay"
SOUND_FILE_NAME = "alarm.wav"
SOUND_FILE_LENGTH = 15  # in seconds
INNER_RETRY_ATTEMPTS = 2
LOGGING_FORMAT = '%(asctime)s\t%(levelname)s\t%(message)s'

# Driver setup options
USER_AGENT_SETTINGS = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) ' 
    'Chrome/83.0.4103.53 Safari/537.36'
)
DISABLE_BLINK_OPTION = '--disable-blink-features=AutomationControlled'
SET_WEBDRIVER_UNDEFINED_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)

# Wait times used - all in seconds
TERMS_AGREEMENT_WAIT_TIME = 1
POST_BUTTON_CLICK_WAIT_TIME = 2
POST_RADIO_BUTTON_CLICK_WAIT_TIME = 4
PAGE_LOAD_WAIT_TIME = 5
FORM_SUBMISSION_WAIT_TIME = 10
WAIT_TIME_BETWEEN_ATTEMPTS = 20
IMPLICIT_WAIT_TIME = 20

# DOM elements needed for clicking
BOOK_APPT_BUTTON_XPATH = (
    '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a'
)
TERMS_AGREEMENT_CHECKBOX_XPATH = '//*[@id="xi-div-1"]/div[4]/label[2]/p'
CITIZENSHIP_DROPDOWN_ID = 'xi-sel-400'
PERSON_COUNT_DROPDOWN_ID = 'xi-sel-422'
WITH_FAMILY_DROPDOWN_ID = 'xi-sel-427'
PROCEED_BUTTON_ID = 'applicationForm:managedForm:proceed'

system = system()

logging.basicConfig(
    format=LOGGING_FORMAT,
    level=logging.INFO,
)


def run_loop():
    while True:
        logging.info("Start appointment arrangement attempt")
        run_once()
        time.sleep(WAIT_TIME_BETWEEN_ATTEMPTS)


def run_once():
    with WebDriver() as driver:
        enter_start_page(driver)
        accept_terms(driver)
        enter_form(driver)
        # retry submit
        for _ in range(INNER_RETRY_ATTEMPTS):
            if not WEBSITE_ERROR_RESPONSE in driver.page_source:
                alert_user()
            logging.info("Retry submitting form")
            driver.find_element(By.ID, PROCEED_BUTTON_ID).click()
            time.sleep(WAIT_TIME_BETWEEN_ATTEMPTS)


def enter_start_page(driver: webdriver.Chrome):
    logging.info("Visit start page")
    driver.get(START_PAGE_URL)
    driver.find_element(By.XPATH, BOOK_APPT_BUTTON_XPATH).click()
    time.sleep(PAGE_LOAD_WAIT_TIME)


def accept_terms(driver: webdriver.Chrome):
    logging.info("Tick off agreement")
    driver.find_element(By.XPATH, TERMS_AGREEMENT_CHECKBOX_XPATH).click()
    time.sleep(TERMS_AGREEMENT_WAIT_TIME)
    driver.find_element(By.ID, PROCEED_BUTTON_ID).click()
    time.sleep(PAGE_LOAD_WAIT_TIME)


def enter_form(driver: webdriver.Chrome):
    logging.info("Fill out form")
    s = Select(driver.find_element(By.ID, CITIZENSHIP_DROPDOWN_ID))
    s.select_by_visible_text(CITIZENSHIP_COUNTRY_TEXT)
    s = Select(driver.find_element(By.ID, PERSON_COUNT_DROPDOWN_ID))
    s.select_by_visible_text(PERSON_COUNT_TEXT)
    s = Select(driver.find_element(By.ID, WITH_FAMILY_DROPDOWN_ID))
    s.select_by_visible_text(NOT_WITH_FAMILY_TEXT)
    time.sleep(PAGE_LOAD_WAIT_TIME)
    driver.find_element(By.XPATH, EXTEND_RESIDENCE_PERMIT_BUTTON_XPATH).click()
    time.sleep(POST_BUTTON_CLICK_WAIT_TIME)
    driver.find_element(By.XPATH, FAMILY_GROUNDS_ACCORDION_XPATH).click()
    time.sleep(POST_BUTTON_CLICK_WAIT_TIME)
    driver.find_element(By.XPATH, FAMILY_OF_SKILLED_WORKER_RADIO_BUTTON_XPATH).click()
    time.sleep(POST_RADIO_BUTTON_CLICK_WAIT_TIME)
    driver.find_element(By.ID, PROCEED_BUTTON_ID).click()
    time.sleep(FORM_SUBMISSION_WAIT_TIME)


def alert_user():
    logging.info("!!!SUCCESS - do not close the window!!!!")
    sound_file_path = os.path.join(os.getcwd(), SOUND_FILE_NAME)
    while True:
        subprocess.run([WAV_FILE_PLAYER, sound_file_path])
        time.sleep(SOUND_FILE_LENGTH)


class WebDriver:

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions()
        options.add_argument(DISABLE_BLINK_OPTION)
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(IMPLICIT_WAIT_TIME)
        self._driver.execute_script(SET_WEBDRIVER_UNDEFINED_SCRIPT)
        self._driver.execute_cdp_cmd(
            'Network.setUserAgentOverride',
            {"userAgent": USER_AGENT_SETTINGS})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()


if __name__ == "__main__":
    run_loop()
