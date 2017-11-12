from bs4 import BeautifulSoup
from requests import get

def parse_page(url):
    page = get(url)
    contents = page.content

    soup = BeautifulSoup(contents, 'html.parser')

    for script in soup(["script", "style"]):
        script.extract()

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return (url, text, [link.get('href').strip() for link in soup.find_all('a')])