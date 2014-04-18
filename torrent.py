import bencode
import hashlib
import requests
import time
import sys
from peers import Peer
from pieces import Piece
from bitstring import BitArray

class Torrent(object):

    PEER_ID = '-BJ1000-012345678901'
    PORT_NO = 6881

    def __init__(self, torrentFileName):
        self.torrent_file = bencode.bdecode(open(torrentFileName,'rb').read())

        self.parse_pieces()

        encoded_info = bencode.bencode(self.torrent_file['info'])
        self.info_hash =  hashlib.sha1(encoded_info).digest()

        self.get_peer_list()

        self.connect_to_peers()
        while not self.have_all_pieces():
            if (len(self.peers) <= 0):
                print 'no peers left'
                return
            time.sleep(5)

    def get_peer_list(self):
        params = {
            'info_hash':self.info_hash,
            'peer_id':self.PEER_ID,
            'left':self.torrent_file['info']['piece length'],
            'port':self.PORT_NO,
            'uploaded':0,
            'downloaded':0,
            'compact':1
            }
        url = self.torrent_file['announce']
        url = url.replace('udp://', 'http://')
        tracker_response = requests.get(url, params=params)
        self.tracker = bencode.bdecode(tracker_response.content)
        self.peers = self.parse_peers(self.tracker['peers'])

    def parse_peers(self, list):
        peers = []
        while len(list) >= 6:
            peer_str = list[0:6] 
            list = list[6:]
            ip_addr = []
            for i in range(0,4):
                ip_addr.append(str(ord(peer_str[i])))
            ip_addr = '.'.join(ip_addr)
            port_no = 256*ord(peer_str[4])+ord(peer_str[5])
            print 'peer %s:%i' % (ip_addr, port_no)
            peers.append(Peer(ip_addr,port_no,self))
        return peers

    def parse_pieces(self):
        self.pieces = []
        piece_length = self.torrent_file['info']['piece length']
        length_left = self.torrent_file['info']['length']
        piece_hashes = self.torrent_file['info']['pieces']
        i = 0
        while length_left > 0:
            self.pieces.append(Piece(i, min(piece_length, length_left),piece_hashes[0:20]))
            piece_hashes = piece_hashes[20:]
            length_left -= piece_length
        self.bitfield = BitArray(int=0, length=len(self.pieces))
        print 'parsed %i pieces' % len(self.pieces)

    def have_all_pieces(self):
        for piece in self.pieces:
            if not piece.have:
                return False
        return True

    def connect_to_peers(self):
        print "connecting to %i peers" % len(self.peers)
        for peer in self.peers:
            print 'connecting to peer %s' % peer.ip
            time.sleep(1)
            peer.run()

    def finish_torrent(self):
        self.write_to_file()
        print 'finished torrent'
        sys.exit(0)

    def write_to_file(self):
        file_name = self.torrent_file['name']
        f = open('./' + file_name, 'w')
        data = combine_pieces()
        f.write(data)
        f.close()

    def combine_pieces(self):
        data = ''
        for i in range(0, len(self.pieces)):
            data += self.pieces[i].data
        return data

    def num_pieces_downloaded(self):
        i = 0
        for piece in self.pieces:
            if piece.have:
                i += 1
        return i

    def print_progress(self):
        total_pieces = len(self.pieces)
        pieces_downloaded = self.num_pieces_downloaded()
        pct = pieces_downloaded/float(total_pieces)
        progress = int(50*pct)
        string = '['+('='*progress)+(' '*(50-progress))+']'
        print string
        print '%f%% downloaded (%i/%i)' % ((pct*100),pieces_downloaded,total_pieces)




