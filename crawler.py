from bs4 import BeautifulSoup
from requests import get
from argparse import ArgumentParser
from re import findall
from functools import lru_cache
from time import time
from postgresql import open as pg_open
from pika import BlockingConnection, ConnectionParameters

CHECK_INTERVAL = 86400

db = pg_open('pq://postgres:postgres@postgres:5432/postgres')
get_word_id = db.prepare('SELECT ID FROM tbl_Words WHERE Word = $1;')
new_word = db.prepare('INSERT INTO tbl_Words (Word) VALUES ($1)')
new_word_page = db.prepare('INSERT INTO tbl_Words_Pages VALUES ($1, $2)')
get_word_page = db.prepare('SELECT * FROM tbl_Words_Pages WHERE WordID = $1 AND PageID = $2')
get_page = db.prepare('SELECT (ID, Checked) FROM tbl_Pages WHERE Page = $1;')
get_page_id = db.prepare('SELECT ID FROM tbl_Pages WHERE Page = $1;')
new_page = db.prepare('INSERT INTO tbl_Pages (Page) VALUES ($1)')
check_page = db.prepare('UPDATE tbl_Pages SET Checked = $2 WHERE ID = $1;')
new_page_page = db.prepare('INSERT INTO tbl_Pages_Pages VALUES ($1, $2)')
get_page_page = db.prepare('SELECT * FROM tbl_Pages_Pages WHERE PageID = $1 AND ReferenceID = $2')

rabbit = BlockingConnection(ConnectionParameters(host='rabbit'))
channel = rabbit.channel()
channel.queue_declare(queue='urls')

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

@lru_cache(maxsize=2**32)
def getsert_page_id(page):
    page_id = get_page_id(page)
    if not page_id:
        new_page(page)
        page_id = get_page_id(page)
    return page_id[0][0]

@lru_cache(maxsize=2**32)
def getsert_page(page):
    page_attrs = get_page(page)
    if not page_attrs:
        new_page(page)
        page_attrs = get_page(page)
    return (page_attrs[0][0][0], page_attrs[0][0][1])

@lru_cache(maxsize=2**32)
def getsert_word_id(word):
    word_id = get_word_id(word)
    if not word_id:
        new_word(word)
        word_id = get_word_id(word)
    return word_id[0][0]

def prepare_url(new_url, url):
    if new_url.startswith('http'):
        pass
    elif new_url.startswith('//'):
        new_url = 'http:' + new_url
    elif new_url.startswith('/'):
        new_url = '/'.join(url.split('/')[0:3]) + new_url
    else:
        new_url = url.strip('/') + '/' + new_url
    return new_url

def callback(ch, method, properties, body):
    url = body.decode('utf-8')
    print("Parsing %r" % url)

    (page_id, checked) = getsert_page(url)
    if not checked or time() - checked > CHECK_INTERVAL:
        (words, urls) = parse_page(url)
        for word in words:
            word_id = getsert_word_id(word)
            if not get_word_page(word_id, page_id):
                new_word_page(word_id, page_id)

        for new_url in urls:
            new_url = prepare_url(new_url, url)
            channel.basic_publish(exchange='',
                        routing_key='urls',
                        body=new_url)

            new_page_id = getsert_page_id(new_url)
            if not get_page_page(new_page_id, page_id):
                new_page_page(new_page_id, page_id)

    channel.basic_ack(method.delivery_tag)
    check_page(page_id, int(time()))

if __name__ == "__main__":
    parser = ArgumentParser(description='Simple web crawler')
    parser.add_argument('url', help='URL to start')
    args = parser.parse_args()

    channel.basic_publish(exchange='',
            routing_key='urls',
            body=args.url)
    channel.basic_consume(callback,
                      queue='urls')
    channel.start_consuming()
