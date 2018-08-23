#!/usr/bin/python

from flask import Flask, render_template, request, jsonify, redirect
from flask_socketio import SocketIO, emit
from bomara.vendors import apc
from bomara.tools import clear_output

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

app.config.update(
    TEMPLATE_AUTO_RELOAD=True,
    DEBUG=True,
    TESTING=True
)

socketio = SocketIO(app)
    
crawl_settings = {
    'write': True,
    'template': '../templates/base.html',
}


@app.route('/')
def index():
    return render_template('interface.html')


def run_crawler(link):
    # Remove anchor from link
    link = link.split('#')[0]

    #if 'vertivco.com' in link:
    #    scraper = bomara.crawler.VertivCrawler()
    if 'apc.com' in link:
        crawler = apc.crawler
        crawler.reset()
    else:
        socketio.emit('payload', '[Error] Not a valid vendor/URL')
        return None

    socketio.emit('payload', 'Loading <a href="' +
                  link+'" target="_blank">'+link+'</a>')

    try:
        crawler.connect(link)
    except Exception:
        socketio.emit('payload', '[Error] Not a valid URL')
        return None

    if crawler.parser_warning:
        socketio.emit('payload', '[Warning] {}'.format(crawler.parser_warning))

    socketio.emit('payload', 'Applying template')
    try:
        part_num = crawler.apply(write=crawl_settings['write'])
    except Exception as e:
        socketio.emit(
            'payload', '[Error] Could not render template: {}'.format(e))
        return None

    socketio.emit('payload', '[Complete] '+part_num)


@socketio.on('set')
def change_settings(settings):
    # Wrapper for changing crawler settings
    crawl_settings[settings[0]] = settings[1]


@socketio.on('run_crawler')
def handle_run(form):
    form = form['data'][0]['value']
    map(lambda link: run_crawler(link), form.splitlines())


@app.route('/clear', methods=['POST', 'GET'])
def handle_clear():
    if request.method == 'POST':
        clear_output()
        socketio.emit('payload', '[Complete] Cleared output folder')
        return jsonify('Cleared output')
    # Accessing /clear directly
    return redirect('/')


@app.route('/logs')
def handle_log():
    with open('crawler.log', 'r+') as logs:
        log = reversed(logs.readlines())
        logs.close()
    return render_template('logs.html', log=log)


def run():
    socketio.run(app)
