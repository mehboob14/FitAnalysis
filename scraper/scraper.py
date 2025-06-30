
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import time
import random


def get_dress_data(url):
    options = uc.ChromeOptions()
    options.headless = False  
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)

    try:
        driver.get(url)

        time.sleep(random.uniform(3, 5))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        wait = WebDriverWait(driver, 10)

        try:
            fit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Size & Fit')]")))
            fit_btn.click()
            time.sleep(1)
        except:
            print("[!] Could not click 'Size & Fit'")

        try:
            care_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Details & Care')]")))
            care_btn.click()
            time.sleep(1)
        except:
            print("[!] Could not click 'Details & Care'")

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        try:
            title = soup.find('h1').get_text(strip=True)
        except:
            title = 'N/A'

        try:
            description_block = soup.find('div', {'data-testid': 'pdp-description'})
            description = description_block.get_text(separator=' ', strip=True)
        except:
            description = 'N/A'

        try:
            size_fit = soup.find('div', {'data-testid': 'pdp-fit'}).get_text(separator=' ', strip=True)
        except:
            size_fit = 'N/A'

        try:
            details = soup.find('div', {'data-testid': 'pdp-details'}).get_text(separator=' ', strip=True)
        except:
            details = 'N/A'
 
        try:
            image_elements = soup.select('img[data-testid="media-image"]')
            images = [img['src'] for img in image_elements if img.get('src')]
        except:
            images = []

        return {
            'title': title,
            'description': description,
            'size_fit': size_fit,
            'details': details,
            'images': images
        }

    finally:
        driver.quit()
