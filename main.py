import json
from scraper import scrape_section  # Import functions from the original file

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
    aws_data = scrape_section(aws_url, aws_source, aws_section_titles)

    # Combine all scraped data
    all_data = react_data + aws_data

    # Save to JSON
    with open('documentation_scraped.json', 'w', encoding='utf-8') as file:
        json.dump(all_data, file, indent=2, ensure_ascii=False)

    print("Scraping completed. Data saved to documentation_scraped.json")


if __name__ == "__main__":
    main()
