import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import unicodedata
import html

def scrape_section_content(section_url, main_url, is_aws=False):
    """
    Scrape the content from a specific section URL.
    """
    response = requests.get(section_url)
    if response.status_code != 200:
        print(f"Failed to fetch {section_url}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract data
    content = []
    if is_aws:
        # For AWS, scrape data from the div with id="main-col-body"
        main_body = soup.find('div', id='main-col-body')
        if main_body:
            current_section = None
            for element in main_body.find_all(['h1', 'h2', 'h3', 'p']):
                if element.name in ['h1', 'h2', 'h3']:
                    # Start a new section for each heading
                    if current_section:
                        content.append(current_section)
                    current_section = {
                        "heading": element.get_text(strip=True),
                        "texts": []
                    }
                elif current_section and element.name == 'p':
                    # Add paragraphs to the current section
                    text = element.get_text(strip=True)
                    if text:
                        current_section["texts"].append(text)

            # Append the last section after the loop ends
            if current_section:
                content.append(current_section)
    else:
        # For React or other, scrape from articles
        for article in soup.find_all("article"):
            article_data = {}

            # Get the first <p> tag inside the article
            first_paragraph = article.find("p")
            if first_paragraph:
                text = first_paragraph.get_text(strip=True)
                cleaned_text = unicodedata.normalize("NFKD", html.unescape(text))
                final_text = cleaned_text.encode("utf-8").decode("utf-8")
                article_data['Info'] = final_text

            # Get all <a> tags within unordered <ul> or ordered <ol> lists
            links = []
            for ul in article.find_all(["ul", "ol"]):  # Find both unordered and ordered lists
                for li in ul.find_all("li"):  # Look for list items
                    for a in li.find_all("a", href=True):  # Extract <a> tags with href attributes
                        sub_url = requests.compat.urljoin(main_url, a['href'])
                        links.append({
                            'Sub-Topic': a.get_text(strip=True),
                            'link': sub_url
                        })

            if links:
                article_data['links'] = links

            # Only add article data if it contains valid content
            if article_data:
                content.append(article_data)

    return content

def scrape_aws_section_urls_with_selenium(main_url, section_titles):
    """
    Scrape specific section URLs dynamically from the AWS Lambda documentation page using Selenium.
    """
    # Set up the Selenium WebDriver (using Chrome)
    driver = webdriver.Chrome()  # Replace with the path to your chromedriver

    try:
        # Load the page
        driver.get(main_url)

        # Wait for the side navigation menu to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'awsui_list-container_l0dv0_1k6s2_221'))
        )

        # Get the page source after JavaScript has rendered the content
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Locate the container with section links
        container = soup.find('div', class_=lambda value: value and 'awsui_list-container' in value)
        if not container:
            print("Failed to locate the AWS section container.")
            return []

        # Extract relevant <a> tags based on matching section titles
        section_urls = []
        for a_tag in container.find_all('a', href=True):
            link_text = a_tag.get_text(strip=True)
            if link_text in section_titles:  # Match the link text with predefined section titles
                link_url = requests.compat.urljoin(main_url, a_tag['href'])
                section_urls.append({'title': link_text, 'url': link_url})

        return section_urls

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        # Close the browser
        driver.quit()

def scrape_section(url, source, section_titles=None):
    """
    Scrape content and section URLs from a webpage, and organize into a specific JSON structure.
    """
    if source == "aws_lambda":
        # Scrape AWS section URLs dynamically, matching only specific titles
        sections = scrape_aws_section_urls_with_selenium(url, section_titles)
    else:
        # React uses pre-defined section titles
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        sections = []
        for title in section_titles:
            anchor = soup.find('a', title=lambda t: t and title.lower() in t.lower())
            if anchor and anchor.get('href'):
                section_url = requests.compat.urljoin(url, anchor['href'])
                sections.append({'title': title, 'url': section_url})

    # Fetch and organize content for each section
    page_data = []
    for section in sections:
        title = section['title']
        section_url = section['url']

        # Scrape content from the section URL
        is_aws = source == "aws_lambda"
        section_content = scrape_section_content(section_url, url, is_aws=is_aws)

        # Add the section data in the required format
        section_data = {
            "title": title,
            "url": section_url,
            "source": source,
            "sections": [
                {
                    "content": section_content  # Relevant content scraped from the section URL
                }
            ]
        }
        page_data.append(section_data)

    return page_data

def main():
    # React documentation scraping
    react_url = "https://react.dev/learn"
    react_source = "react"
    react_section_titles = [
        "Installation",
        "Describing the UI",
        "Adding Interactivity",
        "Managing State",
        "Escape Hatches"
    ]
    react_data = scrape_section(react_url, react_source, react_section_titles)

    # AWS Lambda documentation scraping
    aws_url = "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"
    aws_source = "aws_lambda"
    aws_section_titles = [
        "What is AWS Lambda?",
        "Example apps",
        "Building with TypeScript",
        "Integrating other services",
        "Code examples"
    ]
    aws_data = scrape_section(url=aws_url, source=aws_source, section_titles=aws_section_titles)

    # Combine all scraped data
    all_data = react_data + aws_data

    # Save to JSON
    with open('documentation_AWS.json', 'w', encoding='utf-8') as file:
        json.dump(all_data, file, indent=2, ensure_ascii=False)

    print("Scraping completed. Data saved to documentation_output.json")

if __name__ == "__main__":
    main()
