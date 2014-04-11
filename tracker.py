import bencode
import hashlib
import urllib2

class Tracker(object):

	PEER_ID = '-BJ1000-0123456789ab'

	def __init__(self, torrentFileName):
        self.torrent = bencode.bdecode(open(torrentFileName,'rb').read())
        get_peer_list()


    def get_info_hash(self):
    	encodedInfo = bencode.bencode(self.torrent['info'])
    	hash = hashlib.sha1()
    	hash.update(encodedInfo)
    	return hash.digest()

    def get_tracker_url(self):
    	url = self.torrent['announce']
    	url += '?' + urllib2.urlencode({
    		'info_hash':self.get_info_hash(),
    		'peer_id':PEER_ID,
    		'left':self.torrent['info']['length']})

    def get_peer_list(self):
    	tracker_url = get_tracker_url()
    	# actually call the url and parse the response
