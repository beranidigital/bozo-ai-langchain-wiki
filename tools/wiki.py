import random
from urllib.parse import urlencode

import regex
from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup
import markdownify


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
def get_wiki_shelves(url: str = "https://wiki.beranidigital.id/shelves"):
    """
    Get list of shelves from the wiki.
    Starting URL: https://wiki.beranidigital.id/shelves
    :param url: Must start with https://wiki.beranidigital.id/shelves
    """
    if not url.startswith("https://wiki.beranidigital.id/shelves"):
        return "Invalid URL"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    shelves = soup.find_all('a', {'class': ['grid-card']})
    data = dict()
    for shelf in shelves:
        header = shelf.find('h2').text
        description = shelf.find('div', {'class': ['grid-card-content']}).text.strip()
        href = shelf['href']
        data[header] = {
            'header': header,
            'description': description,
            'href': href,
        }
    return data

@tool
def list_books(url: str):
    """
    get list of books from a shelf.
    :param url: must start with https://wiki.beranidigital.id/books/
    """
    if not url.startswith("https://wiki.beranidigital.id/books/"):
        return "Invalid URL, must start with https://wiki.beranidigital.id/books/"

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    items = soup.find_all('a', {'class': ['page']})
    data = []
    for item in items:
        text = item.find('h4').text
        link = item['href']
        description = item.find('p').text.strip()
        data.append({
            'text': text,
            'description': description,
            'link': link
        })
    return data


def list_shelves():
    """
    Get the list of shelves.
    Use this to list all the shelves in the Berani Digital ID wiki.
    :return dict: A dictionary of shelves and list of items (books) link.
    """
    top_shelves = get_wiki_shelves("https://wiki.beranidigital.id/shelves")
    shelves = dict()
    for top_shelf, top_value in top_shelves.items():
        for key, value in get_wiki_shelves(top_shelves[top_shelf]['href']).items():
            shelves[key] = value
            shelves[key]['items'] = []
            shelves[key]['category'] = top_shelf

    for shelf_key in shelves:
        href = shelves[shelf_key]['href']
        shelves[shelf_key]['items'] = list_books(href)
    return shelves

@tool
def read_book(url: str):
    """
    Read a book from the wiki.
    :param url: must be this pattern https://wiki.beranidigital.id/books/*/page/*
    """
    if not regex.match(r"https://wiki.beranidigital.id/books/.*/page/.*", url):
        return "Invalid URL, must be this pattern https://wiki.beranidigital.id/books/*/page/*"

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    content = soup.find('main', {'class': ['content-wrap', 'card']})
    content = markdownify.markdownify(str(content), heading_style="ATX")
    return content

if __name__ == '__main__':
    import json
    shelve_listed = list_shelves()
    jsoned_shelves = json.dumps(shelve_listed)
    print("Length: ", len(jsoned_shelves))
    for shelf in shelve_listed:
        print(shelf)
        print(shelve_listed[shelf]['description'])
        for item in shelve_listed[shelf]['items']:
            print(item['text'])
            print(item['description'])
            print(item['link'])
            print()
    random_shelves = list(shelve_listed.keys())
    random_shelf = random.choice(random_shelves)
    random_item = random.choice(shelve_listed[random_shelf]['items'])
    read_book_result = read_book(random_item['link'])
    print(read_book_result)
    results = search_wiki("Berani Digital ID")
    for result in results:
        print(result['header'])
        print(result['description'])
        print(result['breadcrumbs'])
        print(result['link'])
        print()
    print(read_book(results[0]['link']))
    print("URL: ", results[0]['link'])
