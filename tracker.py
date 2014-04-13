import bencode
import hashlib
import requests
from peers import Peer

class Tracker(object):

    PEER_ID = '-BJ1000-012345678901'
    PORT_NO = 6881

    def __init__(self, torrentFileName):
        self.torrent = bencode.bdecode(open(torrentFileName,'rb').read())
        print "self.torrent"
        print self.torrent

        self.get_peer_list()


    def get_info_hash(self):
        encoded_info = bencode.bencode(self.torrent['info'])
        return hashlib.sha1(encoded_info).digest()

    def get_peer_list(self):
        params = {
            'info_hash':self.get_info_hash(),
            'peer_id':self.PEER_ID,
            'left':self.torrent['info']['piece length'],
            'port':self.PORT_NO,
            'uploaded':0,
            'downloaded':0,
            'compact':1
            }
        tracker_response = requests.get(self.torrent['announce'], params=params)
        self.tracker = bencode.bdecode(tracker_response.content)
        self.peers = self.parse_peers(self.tracker['peers'])
        for peer in self.peers:
            peer.run()

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
            peers.append(Peer(ip_addr,port_no, self.get_info_hash(), self.PEER_ID))
        return peers






