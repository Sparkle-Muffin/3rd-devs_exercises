import requests
from markdownify import markdownify as md


def download_website_as_markdown(url: str) -> str:
    html = requests.get(url).text
    markdown = md(html)
    return markdown