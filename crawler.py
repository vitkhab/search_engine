from bs4 import BeautifulSoup
from requests import get
from argparse import ArgumentParser
from re import findall
import postgresql

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

    with postgresql.open('pq://postgres:postgres@postgres:5432/postgres') as db:

        get_word_id = db.prepare('SELECT ID FROM tbl_Words WHERE Word = $1;')
        new_word = db.prepare('INSERT INTO tbl_Words (Word) VALUES ($1)')
        new_word_page = db.prepare('INSERT INTO tbl_Words_Pages VALUES ($1, $2)')
        get_page_id = db.prepare('SELECT ID FROM tbl_Pages WHERE Page = $1;')
        new_page = db.prepare('INSERT INTO tbl_Pages (Page) VALUES ($1)')
        new_page_page = db.prepare('INSERT INTO tbl_Pages_Pages VALUES ($1, $2)')

        while to_parse:
            url = to_parse.pop()
            (words, urls) = parse_page(url)
            print(url, words)
            parsed.append(url)

            page_id = get_page_id(url)
            if not page_id:
                new_page(url)
                page_id = get_page_id(url)
            page_id = page_id[0][0]

            for word in words:
                word_id = get_word_id(word)
                if not word_id:
                    new_word(word)
                    word_id = get_word_id(word)
                word_id = word_id[0][0]
                new_word_page(word_id, page_id)

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
