#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket


class Socket:
    """
    wrap the socket() class
    """

    def __init__(self, ip, port):
        self.ip = str(ip)
        self.port = int(port)
        self.is_connected = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connection = None

    def connect(self):
        """
        Connect to the given host at the specified port
        If already connected, disconnect first to ensure there's no port-hogging(might be wrong)
        """
        if self.is_connected:
            self.disconnect()

        self._socket.connect((self.ip, self.port))
        try:
            self._connection = self._socket.makefile('rwb', 0) # read and write, no internal buffer
            self.is_connected = True
            return self.is_connected
        except:
            self.is_connected = False
            return self.is_connected

    def disconnect(self):
        """
        Close the connection, delete the variables(not pythonic)
        """
        self._connection.close()
        self._socket.close()
        del self._connection
        del self._socket
        self.is_connected = False
        return self.is_connected

    def write(self, data):
        """
        write to the socket -- the socket must be opened
        """
        if self.is_connected:
            self._connection.write(data)

    def read(self, size=-1):
        """
        read from the socket; warning -- it blocks on reading!
        """
        if self.is_connected:
            if size < 0:
                return self._connection.read()
            else:
                return self._connection.read(size)


class Check():

    def __init__(self, ip, port):
        """
        Check if Netstation is available for connection(not sure if this works yet)
        :param ip:  ip string
        :param port: port int
        :return: True = connected, False = No connection
        """
        self.ip = str(ip)
        self.port = int(port)

    def try_it(self):
        try:
            socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket2.connect((self.ip, self.port))
            connection2 = socket2.makefile('rwb', 0)
            connection2.close()
            socket2.close()
            del connection2
            del socket2
            return True
        except:
            print 'No netstation connected'
            return False