

class Piece(object):
    
    def __init__(self, index, size, piece_hash):
        self.index = index
        self.size = size
        self.hash = piece_hash


class Block(object):

    def __init__(self, size, offset):
        self.size = size
        self.offset = offset
        
        
