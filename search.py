from flask import Flask, request, g, render_template, logging, Response
from functools import reduce
from os import getenv
import uuid
from postgresql import open as pg_open
import time
import structlog
import traceback
import prometheus_client

CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
COUNTER_PAGES_SERVED = prometheus_client.Counter('web_pages_served', 'Number of pages served by frontend')
HISTOGRAM_PAGE_GEN_TIME = prometheus_client.Histogram('web_page_gen_time', 'Page generation time')

logg = logging.getLogger('werkzeug')
logg.disabled = True   # disable default logger

log = structlog.get_logger()
structlog.configure(processors=[
     structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
     structlog.stdlib.add_log_level,
     # to see indented logs in the terminal, uncomment the line below
     # structlog.processors.JSONRenderer(indent=2, sort_keys=True)
     # and comment out the one below
     structlog.processors.JSONRenderer(sort_keys=True)
 ])

db_creds = {
    "user": getenv('DB_USER', 'postgres'),
    "password": getenv('DB_PASSWORD', 'postgres'),
    "host": getenv('DB_HOST', 'postgres'),
    "port": getenv('DB_PORT', '5432'),
    "database": getenv('DB_NAME', 'postgres')
}

app = Flask(__name__)
try:
    db = pg_open('pq://{0}:{1}@{2}:{3}/{4}'.format(
        db_creds["user"],
        db_creds["password"],
        db_creds["host"],
        db_creds["port"],
        db_creds["database"]
    ))
except Exception as e:
    log.error('connect_db',
              service='web',
              message="Failed connect to Database",
              traceback=traceback.format_exc(e),
              db_creds=db_creds)
else:
    log.info('connect_to_db',
              service='web',
              message='Successfully connected to database',
              db_creds=db_creds
            )

get_word_id = db.prepare('SELECT ID FROM tbl_Words WHERE Word = $1;')
get_pages_id = db.prepare('SELECT PageID FROM tbl_Words_Pages WHERE WordID = $1;')
get_page = db.prepare('SELECT Page FROM tbl_Pages WHERE ID = $1;')
get_page_score = db.prepare('SELECT COUNT(*) FROM tbl_Pages_Pages WHERE PageID = $1;')

def intersect(a, b):
    return list(set(a) & set(b))

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: (time.time() - g.request_start_time)

@app.after_request
def after_request(response):
    HISTOGRAM_PAGE_GEN_TIME.observe(g.request_time())
    return response

# @app.route('/metrics')
# def metrics():
#     return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/metrics')
def metrics():
    return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/')
def start():
    phrase = request.args.get('query', '').split()
    COUNTER_PAGES_SERVED.inc()

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

@app.after_request
def after_request(response):
    request_id = request.headers['Request-Id'] \
        if 'Request-Id' in request.headers else uuid.uuid4()
    log.info('request',
             service='web',
             request_id=request_id,
             addr=request.remote_addr,
             path=request.path,
             args=request.args,
             method=request.method,
             response_status=response.status_code)
    return response

# Log Exceptions
@app.errorhandler(Exception)
def exceptions(e):
    request_id = request.headers['Request-Id'] \
        if 'Request-Id' in request.headers else None
    tb = traceback.format_exc()
    log.error('internal_error',
              service='web',
              request_id=request_id,
              addr=request.remote_addr,
              path=request.path,
              args=request.args,
              method=request.method,
              traceback=tb)
    return 'Internal Server Error', 500
