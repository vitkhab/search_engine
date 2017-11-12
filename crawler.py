from bs4 import BeautifulSoup
from requests import get
from argparse import ArgumentParser
from re import findall

def get_page_content(url):
    page = get(url)
    return page.content

def prepare_links(soup):
    links = []
    for link in soup.find_all('a'):
        url = link.get('href')
        if url:
            links.append(url.strip())
    return links

def prepare_text(contents):
    soup = BeautifulSoup(contents, 'html.parser')

    for script in soup(["script", "style"]):
        script.extract()

    return (findall(r"[\w']+", soup.get_text()), prepare_links(soup))


def parse_page(url):
    contents = get_page_content(url)

    return prepare_text(contents)

if __name__ == "__main__":
    parser = ArgumentParser(description='Simple web crawler')
    parser.add_argument('url', help='URL to start')
    args = parser.parse_args()

    to_parse = [args.url]
    parsed = []

    while to_parse:
        url = to_parse.pop()
        (words, urls) = parse_page(url)
        parsed.append(url)

        for new_url in urls:
            if new_url.startswith('http'):
                pass
            elif new_url.startswith('//'):
                new_url = 'http:' + new_url
            elif new_url.startswith('/'):
                new_url = '/'.join(url.split('/')[0:3]) + new_url
            else:
                new_url = url.strip('/') + '/' + new_url
            if new_url not in parsed:
                to_parse.append(new_url)
