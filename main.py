#! /usr/bin/env python

import sys

from torrent import Torrent

def main():
    torrentFile = sys.argv[1]
    torrent = Torrent(torrentFile)
    
if __name__ == "__main__":
    main()