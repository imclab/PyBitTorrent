import socket
import struct

def bytes_to_number(bytestring):  
    '''bytestring assumed to be 4 bytes long and represents 1 number'''
    number = 0
    i = 3
    for byte in bytestring:
        try:
            number += ord(byte) * 256**i
        except(TypeError):
            number += byte * 256**i
        i -= 1
    return number

class Peer(object):

    def __init__(self, ip, port, info_hash, peer_id):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.peer_id = peer_id


    def run(self):
        try:
            print '-------------'
            print '\n'
            self.connect()
            print 'successfully connected'
            self.handshake()
            print 'handshake done'
            msg = self.socket.recv(100000)
            msg = bytearray(msg)
            length = bytes_to_number(msg[0:4])
            print 'length %s' % length
            if (length > 0):
                msg_id = msg[4]
            else: 
                msg_id = 0
            print 'msg_id %s' % msg_id
            print msg_id
        except socket.error as err:
            print err


    def connect(self):
        print self.ip
        print self.port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.ip, self.port))

    def handshake(self):
        msg = self.get_handshake_msg()
        self.socket.send(msg)
        received_handshake = self.socket.recv(2000)
        print received_handshake
        received_info_hash = received_handshake[28:48]


    def get_handshake_msg(self):
        pstrlen = '\x13'
        pstr = 'BitTorrent protocol'
        reserved = '\x00\x00\x00\x00\x00\x00\x00\x00'
       
        handshake = pstrlen+pstr+reserved+self.info_hash+self.peer_id

        return handshake

