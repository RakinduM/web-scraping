import requests
from bs4 import BeautifulSoup
import json
import unicodedata
import html

def scrape_section_content(section_url, main_url):
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

def scrape_section(url, source, section_titles):
    """
    Scrape content and section URLs from a webpage, and organize into a specific JSON structure.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    page_data = []

    for title in section_titles:
        # Locate the anchor tag using the title attribute
        anchor = soup.find('a', title=lambda t: t and title.lower() in t.lower())
        section_url = url  # Default to the main URL
        if anchor and anchor.get('href'):
            # Construct the full URL if href is relative
            section_url = requests.compat.urljoin(url, anchor['href'])

        # Scrape content from the section URL
        section_content = scrape_section_content(section_url, url)

        # Add the section data in the required format
        section_data = {
            "title": title,
            "url": section_url,  # Specific section URL
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
        "Define Lambda function handler in Java",
        "Example apps",
        "Building with TypeScript",
        "Integrating other services"
    ]


    # Combine all scraped data
    all_data = react_data

    # Save to JSON
    with open('documentation_output.json', 'w', encoding='utf-8') as file:
        json.dump(all_data, file, indent=2, ensure_ascii=False)

    print("Scraping completed. Data saved to documentation_output.json")

if  __name__ == "__main__":
    main()
