from flask import Flask, request
import postgresql
app = Flask(__name__)
db = postgresql.open('pq://postgres:postgres@postgres:5432/postgres')

get_word_id = db.prepare('SELECT ID FROM tbl_Words WHERE Word = $1;')
get_pages_id = db.prepare('SELECT PageID FROM tbl_Words_Pages WHERE WordID = $1;')
get_page = db.prepare('SELECT Page FROM tbl_Pages WHERE ID = $1;')
get_page_score = db.prepare('SELECT COUNT(*) FROM tbl_Pages_Pages WHERE ReferenceID = $1;')

@app.route('/')
def start():
    search_query = '''
    <form action="/" method="get">
    <input name="query">
    <input type="submit">
    </form>
    '''
    word = request.args.get('query', '')
    if word:
        word_id = get_word_id(word)
        if not word_id:
            return search_query + 'Not found'
        word_id = word_id[0][0]
        pages = []
        for id in get_pages_id(word_id):
            url = get_page(id[0])[0][0]
            score = get_page_score(id[0])[0][0]
            pages.append((score, url))
        pages.sort(reverse=True)
        search_query += '<br>'.join(['{} links to <a href="{}">{}</a>'.format(s, u, u) for (s, u) in pages])


    return search_query