import bencode
import hashlib
import requests
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
        tracker_response = requests.get(self.torrent_file['announce'], params=params)
        self.tracker = bencode.bdecode(tracker_response.content)
        self.peers = self.parse_peers(self.tracker['peers'])
        print "found %i peers" % len(self.peers)

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


    def connect_to_peers(self):
        for peer in self.peers:
            peer.run()



