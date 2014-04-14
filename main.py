#! /usr/bin/env python

import sys

from tracker import Tracker

def main():
    torrentFile = sys.argv[1]
    tracker = Tracker(torrentFile)

    
    
if __name__ == "__main__":
    main()