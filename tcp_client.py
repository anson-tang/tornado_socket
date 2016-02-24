#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 
import signal

from tornado import ioloop, httpclient, gen
from tornado.gen import Task
import pdb, time, logging
import tornado.ioloop
import tornado.iostream
import socket


def signal_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

#Init logging
def init_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()

    #formatter = logging.Formatter('%(asctime)s -%(module)s:%(filename)s-L%(lineno)d-%(levelname)s: %(message)s')
    formatter = logging.Formatter('[%(asctime)s %(filename)s-L%(lineno)d-%(levelname)s]: %(message)s')
    sh.setFormatter(formatter)

    logger.addHandler(sh)
    logging.info("Current log level is : %s", logging.getLevelName(logger.getEffectiveLevel()))


class TCPClient(object):
    def __init__(self, host, port, io_loop=None):
        self.host = host
        self.port = port
        self.io_loop = io_loop

        self.shutdown = False
        self.stream = None
        self.sock_fd = None

        self.EOF = b' END'


    def get_stream(self):
        self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = tornado.iostream.IOStream(self.sock_fd)
        self.stream.set_close_callback(self.on_close)

    def connect(self):
        self.get_stream()
        self.stream.connect((self.host, self.port), self.send_message)

    def on_receive(self, data):
        logging.info("Received: %s", data)
        self.stream.close()

    def on_close(self):
        if self.shutdown:
            self.io_loop.stop()

    def send_message(self):
        msg = b"Hello Server!"
        logging.info("Had Send: %s." % msg)
        self.stream.write(msg + self.EOF)
        self.stream.read_until(self.EOF, self.on_receive)
        logging.info("After send....")

    def set_shutdown(self):
        self.shutdown = True

def main():
    # receive SIGINT SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    init_logging()

    io_loop = tornado.ioloop.IOLoop.instance()
    c1 = TCPClient("127.0.0.1", 8001, io_loop)
    #c2 = TCPClient("127.0.0.1", 8001, io_loop)

    c1.connect()
    #c2.connect()

    c1.set_shutdown()

    logging.info("**********************client start ioloop******************")
    io_loop.start()

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        print "Ocurred Exception: %s" % str(ex)
        quit()
