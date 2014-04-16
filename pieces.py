

class Piece(object):

    BLOCK_SIZE = 2**14
    
    def __init__(self, index, size, piece_hash):
        self.index = index
        self.size = size
        self.hash = piece_hash
        self.have = False
        self.data = None

        self.split_into_blocks()

    def split_into_blocks(self):
        i = 0
        self.blocks = []
        while i < self.size:
            this_block_size = min(self.size-i,self.BLOCK_SIZE)
            self.blocks.append(Block(i, this_block_size))
            i = i + this_block_size

    def find_next_block(self):
        for i, block in enumerate(self.blocks):
            if not block.have:
                return i
        self.have = True
        return None

    def downloaded_block(self, offset, data):
        i = offset / self.BLOCK_SIZE
        self.blocks[i].data = data
        self.blocks[i].have = True
        if self.find_next_block() == None:
            self.combine_blocks()

    def combine_blocks(self):
        data = ''
        for block in self.blocks:
            data += block.data
        data_hash = hashlib.sha1(data).digest()
        if data_hash == self.hash:
            self.data = data
            self.have = True
        else:
            self.data = None
            self.have = False
            self.split_into_blocks()


class Block(object):

    def __init__(self, offset, size):
        self.size = size
        self.offset = offset
        self.have = False
        self.data = None
        
        
