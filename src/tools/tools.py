from langchain.tools import tool

import requests
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from rich import print
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re

# Load environment variables from .env
load_dotenv()

# Initialize Tavily client
tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# 1. Web Search Tool
@tool
def web_search(query: str) -> str:
    """Search the web using the Tavily Search API.

    Args:
        query: The search query.

    Returns:
        Search results containing titles, URLs, and content.
    """
    try:
        response = tavily.search(
            query=query,
            max_results=5,
        )

        out = []

        for i in response["results"]:
            out.append(
                f"Title: {i['title']}\n"
                f"URL: {i['url']}\n"
                f"Content: {i['content'][:300]}\n"
                f"-----------------------\n"
            )

        result = "\n-----\n".join(out)

        print(result)

        return result

    except Exception as e:
        return f"Web search failed: {str(e)}"


# 2. Web Scraping Tool
@tool
def scrape_url(url: str) -> str:
    """Extract the main readable text from a webpage.

    Args:
        url: The URL of the webpage to scrape.

    Returns:
        The extracted webpage text.
    """
    try:
        # Step 1: Download the webpage
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        html = response.text

        # Step 2: Extract the main content using Trafilatura
        text_content = trafilatura.extract(html)

        # Step 3: If Trafilatura fails, try Readability
        if not text_content:
            document = Document(html)
            main_html = document.summary()

            soup = BeautifulSoup(main_html, "html.parser")
            text_content = soup.get_text(
                separator="\n",
                strip=True
            )

        # Step 4: If necessary, extract text directly with BeautifulSoup
        if not text_content:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unnecessary page elements
            for element in soup(
                ["script", "style", "nav", "footer", "header"]
            ):
                element.decompose()

            text_content = soup.get_text(
                separator="\n",
                strip=True
            )

        # Step 5: Clean extra spaces and blank lines
        text_content = re.sub(
            r"\n\s*\n+",
            "\n\n",
            text_content
        )

        text_content = re.sub(
            r"[ \t]+",
            " ",
            text_content
        ).strip()

        # Step 6: Check whether content was extracted
        if not text_content:
            return "No readable text could be extracted from this URL."

        # Step 7: Print and return the extracted content
        print(text_content[:5000])

        return text_content[:15000]

    except requests.exceptions.Timeout:
        return "Error: The webpage request timed out."

    except requests.exceptions.HTTPError as e:
        return f"HTTP error while accessing webpage: {str(e)}"

    except requests.exceptions.RequestException as e:
        return f"Error while accessing webpage: {str(e)}"

    except Exception as e:
        return f"Web scraping failed: {str(e)}"
