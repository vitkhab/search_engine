from flask import Flask, request, g, render_template
from functools import reduce
import postgresql
import time
import os

app = Flask(__name__)
db = postgresql.open('pq://{0}:{1}@{2}:{3}/{4}'.format(
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_PASSWORD', 'postgres'),
    os.getenv('DB_HOST', 'postgres'),
    os.getenv('DB_PORT', '5432'),
    os.getenv('DB_NAME', 'postgres')
))

get_word_id = db.prepare('SELECT ID FROM tbl_Words WHERE Word = $1;')
get_pages_id = db.prepare('SELECT PageID FROM tbl_Words_Pages WHERE WordID = $1;')
get_page = db.prepare('SELECT Page FROM tbl_Pages WHERE ID = $1;')
get_page_score = db.prepare('SELECT COUNT(*) FROM tbl_Pages_Pages WHERE PageID = $1;')

def intersect(a, b):
    return list(set(a) & set(b))

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

@app.route('/')
def start():
    phrase = request.args.get('query', '').split()

    if not phrase:
        return render_template('index.html', gen_time=g.request_time())

    word_ids = []
    for word in phrase:
        word_id = get_word_id(word)
        if not word_id:
            return render_template('index.html', gen_time=g.request_time())
        word_ids.append(word_id[0][0])
    
    pages_ids = {}
    for word_id in word_ids:
        pages_ids[word_id] = get_pages_id(word_id)
    
    pages = reduce(intersect, [pages_ids[word_id] for word_id in pages_ids])
    
    res = []
    for id in pages:
        url = get_page(id[0])[0][0]
        score = get_page_score(id[0])[0][0]
        res.append((score, url))
    res.sort(reverse=True)

    return render_template('index.html', gen_time=g.request_time(), result=res) 
