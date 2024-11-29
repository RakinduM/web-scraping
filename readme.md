# Web Scraper for Documentation

This project is a Python-based web scraper designed to fetch and parse content from documentation pages, such as React and AWS Lambda. It extracts relevant sections and their content and saves the results in a structured JSON format.

---

## Features

- **Dynamic scraping**: Uses Selenium for dynamically loaded pages and Requests for static pages.
- **Content parsing**: Extracts topics, subtopics, and their details.
- **Configurable scraping**: Easily add new section titles or pages to scrape.
- **Data output**: Saves scraped data in a structured JSON format.

---

## Requirements

Ensure you have the following installed:

- Python 3.8+
- Required Python libraries:
  - `requests`
  - `beautifulsoup4`
  - `selenium`

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/documentation-scraper.git
   cd documentation-scraper
