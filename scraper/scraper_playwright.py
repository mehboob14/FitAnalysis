import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import json
import os
import requests

async def scrape_product_page(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        await page.wait_for_timeout(3000)

        try:
            await page.wait_for_selector("label[for='Size & Fit-open']", timeout=3000)
            await page.click("label[for='Size & Fit-open']")
            await page.wait_for_timeout(1500)
        except:
            print("Could not expand Size & Fit via label")

        try:
            await page.wait_for_selector('[data-testid="accordion-sizeguide-link"] a.SizeChartLink88__sizeGuideLink', timeout=3000)
            await page.click('[data-testid="accordion-sizeguide-link"] a.SizeChartLink88__sizeGuideLink')
            await page.wait_for_timeout(2000)
        except:
            print("View size guide button NOT found or couldn't be clicked")

        full_html = await page.content()
        soup = BeautifulSoup(full_html, 'html.parser')

        result = {}

        
        editors_notes = soup.select_one('#EDITORS_NOTES .EditorialAccordion88__accordionContent--editors_notes')
        result["editors_notes"] = editors_notes.get_text(strip=True, separator="\n") if editors_notes else "Not found"

       
        size_fit_section = soup.select_one('#SIZE_AND_FIT .EditorialAccordion88__accordionContent--size_and_fit')
        size_fit_details = []
        model_measurements = []

        if size_fit_section:
            all_lis = size_fit_section.find_all('li')
            for li in all_lis:
                text = li.get_text(strip=True)
                if "model is" in text.lower():
                    model_measurements.append(text)
                else:
                    size_fit_details.append(text)
        result["size_fit"] = size_fit_details
        result["model_measurements"] = model_measurements

       
        details_care_section = soup.select_one('#DETAILS_AND_CARE .EditorialAccordion88__accordionContent--details_and_care')
        result["details_care"] = [li.get_text(strip=True) for li in details_care_section.find_all('li')] if details_care_section else []

        
        try:
            overlay_html = await page.inner_html(".Overlay9.SizeChart88__sizeGuide")
            overlay_soup = BeautifulSoup(overlay_html, "html.parser")

            structured_popup = {}
            table = overlay_soup.select_one(".SizeTable88__table")
            if table:
                headers = [th.get_text(strip=True).lower() for th in table.select("thead th")[1:]]
                rows = table.select("tbody tr")
                for row in rows:
                    cells = row.select("td")
                    if not cells or len(cells) < 2:
                        continue
                    label = cells[0].get_text(strip=True).capitalize()
                    values = [td.get_text(strip=True) for td in cells[1:]]
                    if len(values) == len(headers):
                        structured_popup[label] = dict(zip(headers, values))
                    else:
                        print(f"[!] Skipped row '{label}' due to mismatch: {len(values)} values vs {len(headers)} headers")
                result["size_guide_popup"] = structured_popup
            else:
                result["size_guide_popup"] = "Table not found"
        except Exception as e:
            print("Popup scraping failed:", str(e))
            result["size_guide_popup"] = "Popup not loaded"

        image_urls = []
        carousel_track = soup.select_one('ul.ImageCarousel88__track')
        noscripts = carousel_track.select('noscript img') if carousel_track else []

        for img in noscripts:
            srcset = img.get('srcset')
            if srcset:
                urls = [u.strip().split()[0] for u in srcset.split(',')]
                preferred = next((url for url in urls if '/w920_q60' in url or '/w2000_q60' in url), None)
                if preferred:
                    if preferred.startswith('//'):
                        preferred = 'https:' + preferred
                    image_urls.append(preferred)

        image_urls = list(dict.fromkeys(image_urls)) 
        os.makedirs("data/images", exist_ok=True)
        file_path = os.path.join("data/images", "image_urls.txt")
        with open(file_path, "w", encoding="utf-8") as f:
         f.write("image urls:\n")
         for url in image_urls:
            f.write(url + "\n")
        
        await browser.close()
        return result


if __name__ == "__main__":
    turtleneck_dress = "https://www.net-a-porter.com/en-us/shop/product/moncler/clothing/midi-dresses/ribbed-wool-turleneck-midi-dress/1647597338909782"
    data = asyncio.run(scrape_product_page(turtleneck_dress))

    os.makedirs("data", exist_ok=True)

    with open("data/dress_details.txt", "w", encoding="utf-8") as f:
        f.write("EDITOR'S NOTES:\n" + data["editors_notes"] + "\n\n")
        f.write("SIZE & FIT:\n")
        for detail in data["size_fit"]:
            f.write("- " + detail + "\n")
        f.write("\nMODEL MEASUREMENTS:\n")
        for measurement in data["model_measurements"]:
            f.write("- " + measurement + "\n")
        f.write("\nDETAILS & CARE:\n")
        for item in data["details_care"]:
            f.write("- " + item + "\n")

  
    with open("data/Size_guide.json", "w", encoding="utf-8") as f:
        json.dump(data["size_guide_popup"], f, ensure_ascii=False, indent=2)

    print("\n Data saved: dress_details.txt, Size_guide.json, and all product images.")








# next feature need to add as i already have data folde4r and it puting data as expected into the files as expected now i want more than that
# instead of specifying the names of files both for dress_detailes and size_guide i want it decides these names
# on their own like based the title of the dress it decides name both for .txt and .json files respectively. so, next time i just give the url of the and everything nonstop without rewrite existing contents.
# next task is as i already i have working code for extracting images so, what your task is inject that code into this 
#  this code and for imageas output have to create another file dress_title.txt and urls of returend images will be stored
#  stored there.