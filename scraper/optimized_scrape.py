import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import os
import aiohttp
import aiofiles

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/113.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.net-a-porter.com/",
    "Connection": "keep-alive"
}

async def download_image(session, url, path):
    try:
        async with session.get(url, timeout=30) as resp:
            if resp.status == 200:
                async with aiofiles.open(path, mode='wb') as f:
                    await f.write(await resp.read())
                print(f"[\u2713] Downloaded: {os.path.basename(path)}")
            else:
                print(f"[\u2717] Failed {url} with status {resp.status}")
    except Exception as e:
        print(f"[\u2717] Error downloading {url}: {e}")

async def download_images(image_links, save_dir="data/images/downloaded"):
    os.makedirs(save_dir, exist_ok=True)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = []
        for idx, url in enumerate(image_links):
            ext = url.split('.')[-1].split('?')[0]
            if len(ext) > 5 or '/' in ext:
                ext = "jpg"
            filename = f"image_{idx}.{ext}"
            path = os.path.join(save_dir, filename)
            tasks.append(download_image(session, url, path))
        await asyncio.gather(*tasks)

async def block_unwanted_requests(route, request):
    if any(x in request.url for x in ['.png', 'google', 'fonts', 'gtm.js', 'doubleclick']):
        await route.abort()
    else:
        await route.continue_()

async def scrape_product_page(url):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        await context.route("**/*", block_unwanted_requests)
        page = await context.new_page()

        await page.goto(url, wait_until='domcontentloaded')

        if await page.query_selector("label[for='Size & Fit-open']"):
            await page.click("label[for='Size & Fit-open']")

        if await page.query_selector('[data-testid="accordion-sizeguide-link"] a.SizeChartLink88__sizeGuideLink'):
            await page.click('[data-testid="accordion-sizeguide-link"] a.SizeChartLink88__sizeGuideLink')
            await page.wait_for_timeout(1200)

        full_html = await page.content()
        soup = BeautifulSoup(full_html, 'html.parser')

        result = {}
        editors_notes = soup.select_one('#EDITORS_NOTES .EditorialAccordion88__accordionContent--editors_notes')
        result["editors_notes"] = editors_notes.get_text(strip=True, separator="\n") if editors_notes else "Not found"

        size_fit_section = soup.select_one('#SIZE_AND_FIT .EditorialAccordion88__accordionContent--size_and_fit')
        size_fit_details, model_measurements = [], []
        if size_fit_section:
            for li in size_fit_section.find_all('li'):
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
                for row in table.select("tbody tr"):
                    cells = row.select("td")
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).capitalize()
                        values = [td.get_text(strip=True) for td in cells[1:]]
                        if len(values) == len(headers):
                            structured_popup[label] = dict(zip(headers, values))
            result["size_guide_popup"] = structured_popup
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
        await download_images(image_urls)

        await browser.close()
        return result

if __name__ == "__main__":
    url = "https://www.net-a-porter.com/en-us/shop/product/moncler/clothing/mini-dresses/cotton-blend-pique-mini-dress/1647597325563735"
    data = asyncio.run(scrape_product_page(url))

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

    print("\n\u2705 Data saved with optimized performance.")
