# -*- coding: utf-8 -*-
import os
import sys
import threading
import time

os.environ['FLASK_ENV'] = 'exe'
os.environ['DATABASE_URL'] = ''

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    os.chdir(BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, '_MEIPASS', None):
    sys.path.insert(0, sys._MEIPASS)

from app import app
import webview

PORT = 5000

def run_flask():
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Lancer Flask dans un thread
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Attendre que Flask démarre
    time.sleep(1.5)

    # Ouvrir la fenêtre native
    webview.create_window(
    title='Farm Management TN',
    url=f'http://127.0.0.1:{PORT}',
    width=1920,
    height=1080,
    resizable=True,
    min_size=(1024, 600),
    fullscreen=False,
    confirm_close=True,
)
    webview.start()
