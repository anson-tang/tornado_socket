#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

import signal

from tornado import ioloop, httpclient, gen
from tornado.gen import Task
from tornado.tcpserver import TCPServer
import pdb, time, logging
from tornado import stack_context
from tornado.escape import native_str


def signal_handler(signum, frame):
    ioloop.IOLoop.instance().stop()

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


class MyServer(TCPServer):
    def __init__(self, io_loop=None, **kwargs):
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        TCPConnection(stream, address, io_loop=self.io_loop)

class TCPConnection(object):
    def __init__(self, stream, address, io_loop):
        self.io_loop = io_loop
        self.stream = stream
        self.address = address
        self.address_family = stream.socket.family

        self.EOF = b' END'

        self._clear_request_state()

        self._message_callback = stack_context.wrap(self._on_message)

        self.stream.set_close_callback(self._on_connection_close)
        self.stream.read_until(self.EOF, self._message_callback)
        # 客户端在NAT之后，空闲TCP连接会被中间的路由断掉。
        # 常见的方法无非2种：
        # 1) 应用服务器协议里加上PING/PONG等类似心跳的机制。
        # 2) 采用TCP Socket的keepalive。
        #self.stream.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        #self.stream.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 60)
        #self.stream.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5)
        #self.stream.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 20)

    def _on_timeout(self):
        msg = "Hello client!"
        logging.info("Had Send: %s." % msg)
        self.write( msg + self.EOF)
        logging.info("After send....")

    def _on_message(self, data):
        try:
            timeout = 5
            data = native_str(data.decode('latin1'))
            logging.info("Received: %s", data)
            self.io_loop.add_timeout(self.io_loop.time() + timeout, self._on_timeout)
        except Exception, ex:
            logging.error("Exception: %s", str(ex))

    def _clear_request_state(self):
        """Clears the per-request state.
        """
        self._write_callback = None
        self._close_callback = None

    def set_close_callback(self, callback):
        """Sets a callback that will be run when the connection is closed.
        """
        self._close_callback = stack_context.wrap(callback)

    def _on_connection_close(self):
        if self._close_callback is not None:
            callback = self._close_callback
            self._close_callback = None
            callback()
        self._clear_request_state()

    def close(self):
        self.stream.close()
        # Remove this reference to self, which would otherwise cause a
        self._clear_request_state()

    def write(self, chunk, callback=None):
        """Writes a chunk of output to the stream."""
        if not self.stream.closed():
            self._write_callback = stack_context.wrap(callback)
            self.stream.write(chunk, self._on_write_complete)

    def _on_write_complete(self):
        if self._write_callback is not None:
            callback = self._write_callback
            self._write_callback = None
            callback()

def main():
    # receive SIGINT SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    init_logging()

    server = MyServer()
    server.listen(8001)
    logging.info("**********************server start ioloop******************")
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        print "Ocurred Exception: %s" % str(ex)
        quit()

