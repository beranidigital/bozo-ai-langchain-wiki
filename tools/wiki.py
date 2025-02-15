import json
import random
from urllib.parse import urlencode

import aiohttp
import markdownify
import regex
from bs4 import BeautifulSoup
from langchain_core.tools import tool


async def reroute_to_correct_tools(url: str):
    """
    Reroute to the correct tools for the wiki.
    :param url: The URL to reroute.
    :return: The correct tool to use.
    """
    result = None
    used_tools = None
    if regex.match(r"https://wiki.beranidigital.id/books/.*/page/.*", url):
        result = await read_book(url)
        used_tools = "read_book"
    elif regex.match(r"https://wiki.beranidigital.id/books/.*", url):
        result = await list_books_from_shelves(url)
        used_tools = "list_books_from_shelves"
    elif regex.match(r"https://wiki.beranidigital.id/shelves", url):
        result = await get_wiki_shelves(url)
        used_tools = "get_wiki_shelves"
    else:
        return None
    if result is not None:
        return {
            "message": f"Rerouted to correct tool: {used_tools}",
            'result': result,
        }


@tool
async def open_wiki(url: str):
    """
    Explore the Berani Digital ID wiki.
    Try start with root URL: https://wiki.beranidigital.id/shelves
    :param url: The URL to open.
    :return: The content of the page may include URL.
    """
    result = await reroute_to_correct_tools(url)
    if result is not None:
        return result['result']
    return "Invalid URL, try start with https://wiki.beranidigital.id/shelves"


@tool
async def search_wiki(query: str):
    """
    Search the Built-in Berani Digital ID wiki for a query.
    Example: search_wiki("Berani Digital ID")
    """
    url = "https://wiki.beranidigital.id/search"
    # Encode the query
    query = urlencode({'term': query})
    url = f"{url}?{query}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page_content = await response.text()
            # Parse the page
            soup = BeautifulSoup(page_content, 'html.parser')
            # Get page entity-list-item
            results = soup.find_all('a', {'class': 'entity-list-item'})
            list_result = []
            max_results = 5
            for result in results:
                header = result.find('h4').text
                description = result.find('p').text
                href = result['href']
                breadcrumbs_result = result.find_all('span')
                breadcrumbs = []
                for breadcrumb in breadcrumbs_result:
                    text = breadcrumb.text
                    text = text.strip()
                    if len(text) == 0:
                        continue
                    breadcrumbs.append(text)

                list_result.append({
                    'header': header,
                    'description': description,
                    'breadcrumbs': breadcrumbs,
                    'href': href
                })
                if len(list_result) >= max_results:
                    break
            return list_result


async def get_wiki_shelves(url: str = "https://wiki.beranidigital.id/shelves"):
    """
    Starting point to get information
    Get list of shelves from the wiki.
    URL must start with https://wiki.beranidigital.id/shelves
    if returned URL have /shelves/ it means it is a top shelf, keep using this tool until you get hrefs that have /books/
    """
    if not url.startswith("https://wiki.beranidigital.id/shelves"):
        result = await reroute_to_correct_tools(url)
        if result is not None:
            return result
        return "Invalid URL, must start with https://wiki.beranidigital.id/shelves"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')

            shelves = soup.find_all('a', {'class': ['grid-card']})
            data = dict()
            for shelf in shelves:
                header = shelf.find('h2').text
                description = shelf.find('div', {'class': ['grid-card-content']}).text.strip()
                href = shelf['href']
                is_book = href.startswith("https://wiki.beranidigital.id/books/")
                data[header] = {
                    'header': header,
                    'description': description,
                    'href': href,
                    'is_book': is_book
                }
            return data


async def list_books_from_shelves(url: str):
    """
    Get list of books from a shelf.
    Get the shelf URL from get_wiki_shelves.
    URL must start with https://wiki.beranidigital.id/books/
    """
    if not url.startswith("https://wiki.beranidigital.id/books/"):
        result = await reroute_to_correct_tools(url)
        if result is not None:
            return result
        return "Invalid URL, must start with https://wiki.beranidigital.id/books/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')
            items = soup.find_all('a', {'class': ['page']})
            data = []
            for item in items:
                text = item.find('h4').text
                href = item['href']
                description = item.find('p').text.strip()
                data.append({
                    'text': text,
                    'description': description,
                    'href': href
                })
            return data


async def list_shelves():
    """
    Get the list of shelves.
    Use this to list all the shelves in the Berani Digital ID wiki.
    :return dict: A dictionary of shelves and list of items (books) href.
    """
    top_shelves = await get_wiki_shelves("https://wiki.beranidigital.id/shelves")
    shelves = dict()
    for top_shelf, top_value in top_shelves.items():
        for key, value in (await get_wiki_shelves(top_shelves[top_shelf]['href'])).items():
            shelves[key] = value
            shelves[key]['items'] = []
            shelves[key]['category'] = top_shelf

    for shelf_key in shelves:
        href = shelves[shelf_key]['href']
        shelves[shelf_key]['items'] = await list_books_from_shelves(href)
    return shelves


async def read_book(url: str):
    """
    Read a book from the wiki.
    Get the book URL from list_books_from_shelves.
    Don't translate the URL, it must be the exact URL.
    URL must be this pattern https://wiki.beranidigital.id/books/*/page/*
    """
    if not regex.match(r"https://wiki.beranidigital.id/books/.*/page/.*", url):
        result = await reroute_to_correct_tools(url)
        if result is not None:
            return result
        return "Invalid URL, must be this pattern https://wiki.beranidigital.id/books/*/page/*"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                if response.status == 404:
                    return "Wrong URL. Page not found."
                return "Page not found."
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')
            content = soup.find('div', {'class': 'page-content'})
            content = markdownify.markdownify(str(content), heading_style="ATX")
            return content


async def main():
    shelve_listed = await list_shelves()
    jsoned_shelves = json.dumps(shelve_listed)
    print("Length: ", len(jsoned_shelves))
    for shelf in shelve_listed:
        print(shelf)
        print(shelve_listed[shelf]['description'])
        for item in shelve_listed[shelf]['items']:
            print(item['text'])
            print(item['description'])
            print(item['href'])
            print()
    random_shelves = list(shelve_listed.keys())
    random_shelf = random.choice(random_shelves)
    random_item = random.choice(shelve_listed[random_shelf]['items'])
    read_book_result = await read_book(random_item['href'])
    print(read_book_result)
    results = await search_wiki.arun(
        {
            "query": "Berani Digital ID"
        },
    )
    for result in results:
        print(result['header'])
        print(result['description'])
        print(result['breadcrumbs'])
        print(result['href'])
        print()
    print(await read_book(results[0]['href']))
    print("URL: ", results[0]['href'])


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
