import sys
import uuid
import glob
from cStringIO import StringIO
import rfeed
import random

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

import sqlite3
from datetime import datetime
from flask import Flask, send_from_directory
app = Flask(__name__)

db = sqlite3.connect('feed.sqlite3')
cur = db.cursor()
cur.execute('''
create table if not exists feed (id integer, d date, link text, desc text, uuid text)
''')
db.close()

def get_blurb():
    pdfs = glob.glob('/pdfs/*')
    if not pdfs:
        print >>sys.stderr, 'NO PDFS'
        return '', ''
    pdf = random.choice(pdfs)
    print >>sys.stderr, 'pdf:', pdf
    with open(pdf, 'rb') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        assert document.is_extractable
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = list(PDFPage.get_pages(f))
        pnum = random.randint(0, len(pages))
        interpreter.process_page(pages[pnum])
        txt = retstr.getvalue()
    return pdf.replace('pdfs', 'view') + '#page=' + str(pnum), txt[:100]

@app.route('/insert')
def insert():
    link, desc = get_blurb()
    print >>sys.stderr, 'link:', link
    db = sqlite3.connect('feed.sqlite3')
    cur = db.cursor()
    cur.execute('insert into feed (d, link, desc, uuid) values (?, ?, ?, ?)',
        (datetime.now(), link, desc, str(uuid.uuid4())))
    db.commit()
    db.close()
    return 'OK'

@app.route('/feed.rss')
def root():
    db = sqlite3.connect('feed.sqlite3')
    cur = db.cursor()
    items = []
    for d, link, desc, uuid in cur.execute('select d, link, desc, uuid from feed order by d asc'):
        item = rfeed.Item(title=desc[:30], link=link, description=desc, guid=rfeed.Guid(uuid))
        items.append(item)
    feed = rfeed.Feed(
        title='Docfeed',
        link='http://rje.li',
        description='Docfeed',
        items=items)
    return feed.rss()

@app.route('/view/<path:path>')
def view(path):
    return serve_pdf(path)

@app.route('/pdfs/<path:path>')
def serve_pdf(path):
    return send_from_directory('/pdfs', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
