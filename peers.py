import socket
import struct
import random
from bitstring import BitArray
from threading import Thread

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

    def __init__(self, ip, port, torrent):
        self.ip = ip
        self.port = port
        self.torrent = torrent
        self.bitfield = BitArray(int=0, length=len(self.torrent.pieces))
        self.handshake_done = False
        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False


    def run(self):
        self.thread = PeerThread(self)
        self.thread.start()

    def handle_keep_alive_msg(self, payload):
        pass

    def handle_choke_msg(self, payload):
        print 'choke'
        self.peer_choking = True


    def handle_unchoke_msg(self, payload):
        print 'unchoke'
        self.peer_choking = False
        self.send_request()


    def handle_interested_msg(self, payload):
        print 'interested'
        self.peer_interested = True


    def handle_not_interested_msg(self, payload):
        print 'not_interested'
        self.peer_interested = False


    def handle_have_msg(self, payload):
        print 'have'
        index = bytes_to_number(payload[0:4])
        self.bitfield[index] = True
        self.bitfield_updated()


    def handle_bitfield_msg(self, payload):
        print 'bitfield'
        self.bitfield = BitArray(bytes=payload, length=len(self.torrent.pieces))
        self.bitfield_updated()

    def handle_request_msg(self, payload):
        print 'request'
        pass

    def handle_piece_msg(self, payload):
        print 'piece'
        index = bytes_to_number(payload[0:4])
        offset = bytes_to_number(payload[4:8])
        print 'received piece %i/%i at offset %i' % (index, len(self.torrent.pieces), offset)
        data = payload[8:]
        self.torrent.pieces[index].downloaded_block(offset, data)
        if self.torrent.have_all_pieces():
            self.torrent.finish_torrent()
        else:
            self.send_request()

    def handle_cancel_msg(self, payload):
        print 'cancel'
        pass

    def handle_port_msg(self, payload):
        print 'port'
        pass

    def bitfield_updated(self):
        if (not self.am_interested):
             # if there is a piece that they have and we don't, send an interested message
            for i in range(0, len(self.bitfield)):
                if (self.bitfield[i] and not self.torrent.bitfield[i]):
                    self.send_interested();
                    return

    def send_interested(self):
        print 'sending interested'
        self.am_interested = True
        self.socket.send('\x00\x00\x00\x01\x02')

    def find_next_piece(self):
        # find the next piece to download. first look for pieces that we are downloading or no one else is downloading.
        for i in range(0, len(self.torrent.pieces)):
            if(self.torrent.pieces[i].have == False and self.bitfield[i] == True and (self.torrent.pieces[i].downloading_peer == None or self.torrent.pieces[i].downloading_peer == self.ip)):
                return i
        # then look for any piece
        for i in range(0, len(self.torrent.pieces)):
            if(self.torrent.pieces[i].have == False and self.bitfield[i] == True):
                return i
        return None

    def send_request(self):
        i = self.find_next_piece()
        if i == None:
            return
        self.torrent.pieces[i].downloading_peer = self.ip

        next_block = self.torrent.pieces[i].find_next_block()
        header = struct.pack('>I', 13)
        id = '\x06'
        piece_index = struct.pack('>I', i)
        block_offset = struct.pack('>I', next_block.offset)
        block_size = struct.pack('>I', next_block.size)
        req = header + id + piece_index + block_offset + block_size
        print '---------------'
        print 'peer %s' % self.ip
        print 'requesting piece %i at offset %i' % (i, next_block.offset)
        self.torrent.print_progress()
        self.socket.send(req)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(2)
        self.socket.connect((self.ip, self.port))

    def send_handshake(self):
        msg = self.get_handshake_msg()
        self.socket.send(msg)

    def get_handshake_msg(self):
        pstrlen = '\x13'
        pstr = 'BitTorrent protocol'
        reserved = '\x00\x00\x00\x00\x00\x00\x00\x00'
       
        handshake = pstrlen+pstr+reserved+self.torrent.info_hash+self.torrent.PEER_ID

        return handshake

    def remove_from_peers(self):
        self.socket.close()
        for peer in self.torrent.peers:
            if peer.ip == self.ip:
                self.torrent.peers.remove(peer)
        print '---------------'
        print 'peer %s' % self.ip
        print 'removed'
        print '%i peers left' % len(self.torrent.peers)

class PeerThread(Thread):

    def __init__(self, peer):
        super(PeerThread, self).__init__()
        self.peer = peer
        self.daemon = True

    def run(self):
        try:
            print '---------------'
            print 'peer %s' % self.peer.ip
            print 'connecting'
            self.peer.connect()
            print '---------------'
            print 'peer %s' % self.peer.ip
            print 'connected'
            self.peer.send_handshake()
        except socket.error as err:
            # if we get an error remove the peer
            self.peer.remove_from_peers()
            print "connect error: %s" % err
            return

        self.peer.socket.settimeout(120)
        num_errors = 0
        num_success = 0
        while True:
            try:
                msg = self.peer.socket.recv(100000)
                if self.peer.handshake_done == False:
                    received_info_hash = msg[28:48]
                    if received_info_hash == self.peer.torrent.info_hash:
                        self.peer.handshake_done = True
                        print '---------------'
                        print 'peer %s' % self.peer.ip
                        print 'received handshake'
                        continue
                    else:
                        self.peer.remove_from_peers()
                        print 'bad handshake'
                        return
                length = bytes_to_number(bytearray(msg)[0:4])
                if (length == 0):
                    continue
                while length > len(msg):
                    next_msg = self.peer.socket.recv(100000)
                    msg = msg + next_msg
                msg = bytearray(msg)
                msg_id = msg[4]
                num_errors = 0
                print '---------------'
                print 'peer %s' % self.peer.ip
                payload = msg[5:]
                print 'length %s' % length
                print 'msg_id %s' % msg_id
                handlers = {
                    0:self.peer.handle_choke_msg,
                    1:self.peer.handle_unchoke_msg,
                    2:self.peer.handle_interested_msg,
                    3:self.peer.handle_not_interested_msg,
                    4:self.peer.handle_have_msg,
                    5:self.peer.handle_bitfield_msg,
                    6:self.peer.handle_request_msg,
                    7:self.peer.handle_piece_msg,
                    8:self.peer.handle_cancel_msg,
                    9:self.peer.handle_port_msg
                    }
                try:
                    handler = handlers[msg_id]
                except KeyError:
                    self.peer.remove_from_peers()
                    print 'invalid msg id'
                    return
                handler(payload)
            except socket.error as err:
                num_errors = num_errors + 1
                print '---------------'
                print 'peer %s' % self.peer.ip
                print "error number %i" % num_errors
                # if we have three errors in a row, remove the peer
                if (num_errors >= 3):
                    self.peer.remove_from_peers()
                    return
