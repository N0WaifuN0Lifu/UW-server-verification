#!/usr/bin/env python3

from multiprocessing import Process, connection, set_start_method

from gevent.pywsgi import WSGIServer

import bot
import server


def start_bot():
    bot.main()


def start_server():
    http_server = WSGIServer(('', 5000), server.app)
    http_server.serve_forever()


if __name__ == "__main__":
    set_start_method('fork')  # needed for cx_Freeze

    p = Process(target=start_bot)
    p.start()

    start_server()
    p.join()
