import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import unicodedata
import html


def fetch_html(url, use_selenium=False, wait_selector=None):
    """
    Fetch the HTML content of a URL using Requests or Selenium.
    """
    if use_selenium:
        driver = webdriver.Chrome()  # Replace with the path to your ChromeDriver if needed
        try:
            driver.get(url)
            if wait_selector:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, wait_selector))
                )
            html_content = driver.page_source
        finally:
            driver.quit()
        return html_content
    else:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return None
        return response.text
    pass


def parse_section_content(soup, main_url, is_aws=False):
    """
    Parse section content from the HTML soup.
    """
    content = []
    if is_aws:
        main_body = soup.find('div', id='main-col-body')
        if main_body:
            current_section = None
            for element in main_body.find_all(['h1', 'h2', 'h3', 'p']):
                if element.name == 'h1':
                    # Append the current section before starting a new one
                    if current_section:
                        content.append(current_section)
                    current_section = {
                        "Topic": element.get_text(strip=True),
                        "texts": []
                    }
                elif element.name in ['h2', 'h3']:
                    # Append the current section before starting a new sub-topic
                    if current_section:
                        content.append(current_section)
                    current_section = {
                        "Sub-topic": element.get_text(strip=True),
                        "texts": []
                    }
                elif current_section and element.name == 'p':
                    # Add paragraphs to the current section
                    text = element.get_text(strip=True)
                    if text:
                        current_section["texts"].append(text)
            if current_section:
                content.append(current_section)
    else:
        # Parse React-like content from <article>
        for article in soup.find_all("article"):
            article_data = {}
            first_paragraph = article.find("p")
            if first_paragraph:
                text = first_paragraph.get_text(strip=True)
                cleaned_text = unicodedata.normalize("NFKD", html.unescape(text))
                article_data['Info'] = cleaned_text

            # Collect all <a> tags from lists within the article
            links = []
            for ul in article.find_all(["ul", "ol"]):
                for li in ul.find_all("li"):
                    for a in li.find_all("a", href=True):
                        sub_url = requests.compat.urljoin(main_url, a['href'])
                        links.append({
                            'Sub-Topic': a.get_text(strip=True),
                            'link': sub_url
                        })
            if links:
                article_data['links'] = links
            if article_data:
                content.append(article_data)
    return content
    pass


def scrape_aws_section_urls(main_url, section_titles):
    """
    Scrape specific section URLs dynamically from the AWS Lambda documentation page using Selenium.
    """
    html_content = fetch_html(main_url, use_selenium=True, wait_selector='awsui_list-container_l0dv0_1k6s2_221')
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    container = soup.find('div', class_=lambda value: value and 'awsui_list-container' in value)
    if not container:
        print("Failed to locate the AWS section container.")
        return []

    # Extract and match section URLs by titles
    section_urls = []
    for a_tag in container.find_all('a', href=True):
        link_text = a_tag.get_text(strip=True)
        if link_text in section_titles:
            section_urls.append({
                'title': link_text,
                'url': requests.compat.urljoin(main_url, a_tag['href'])
            })
    return section_urls
    pass


def scrape_section(url, source, section_titles=None):
    """
    Scrape content and section URLs from a webpage, and organize into a specific JSON structure.
    """
    if source == "aws_lambda":
        sections = scrape_aws_section_urls(url, section_titles)
    else:
        # React uses pre-defined section titles
        html_content = fetch_html(url)
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = []
        for title in section_titles:
            anchor = soup.find('a', title=lambda t: t and title.lower() in t.lower())
            if anchor and anchor.get('href'):
                sections.append({
                    'title': title,
                    'url': requests.compat.urljoin(url, anchor['href'])
                })

    # Fetch and parse section content
    page_data = []
    for section in sections:
        section_url = section['url']
        html_content = fetch_html(section_url)
        if not html_content:
            continue
        soup = BeautifulSoup(html_content, 'html.parser')
        section_content = parse_section_content(soup, url, is_aws=(source == "aws_lambda"))
        page_data.append({
            "title": section['title'],
            "url": section_url,
            "source": source,
            "sections": [{"content": section_content}]
        })
    return page_data
    pass
