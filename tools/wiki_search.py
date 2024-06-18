from urllib.parse import urlencode

from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup


@tool
def search_wiki(query: str):
    """
    Search the Berani Digital ID wiki for a query.
    Example: search_wiki("Berani Digital ID")
    """
    url = "https://wiki.beranidigital.id/search"
    # Encode the query
    query = urlencode({'term': query})
    url = f"{url}?{query}"
    # Get the page
    page = requests.get(url)
    # Parse the page
    soup = BeautifulSoup(page.content, 'html.parser')
    # Get page   entity-list-item
    results = soup.find_all('a', {'class': 'entity-list-item'})
    list_result = []
    for result in results:
        header = result.find('h4').text
        description = result.find('p').text
        link = result['href']
        breadcrumbs_result = result.find_all('span')
        breadcrumbs = []
        for breadcrumb in breadcrumbs_result:
            text = breadcrumb.text
            text = text.strip()
            if len(text) == 0: continue
            breadcrumbs.append(text)

        list_result.append({
            'header': header,
            'description': description,
            'breadcrumbs': breadcrumbs,
            'link': link
        })
    return list_result

@tool
def detailed_wiki(url: str) -> str:
    """
    Get detailed information from a wiki page from the URL.
    Get the URL from the search_wiki tool.
    """

    if not url.startswith("https://wiki.beranidigital.id/"):
        return "Invalid URL"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    # page-content clearfix
    content = soup.find('div', {'class': 'page-content'})
    return content.text


if __name__ == '__main__':
    results = search_wiki("Berani Digital ID")
    for result in results:
        print(result['header'])
        print(result['description'])
        print(result['breadcrumbs'])
        print(result['link'])
        print()
    print(detailed_wiki(results[0]['link']))
    print("URL: ", results[0]['link'])
