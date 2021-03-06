# coding: utf-8

import urllib2
import socket

from search_server import encode, decode

class SearchClient(object):
    def __init__(self, url, batchsize):
        self.url = url
        self.batchsize = batchsize

    def search(self):
        for candidates in self.candidate_lists():
            self.process_candidate(candidates)

    def process_candidate(self, candidates):
        new_candidates = []
        processed = []
        for candidate in candidates:
            if not candidate.is_final():
                new_candidates += list(candidate.next_states())
            processed.append(candidate)

        self.add_candiates(new_candidates)
        self.add_processed(processed)

    def candidate_lists(self):
        while True:
            try:
                f = urllib2.urlopen(self.url + '/candidates?batch=%s'%(self.batchsize))
                candidates = decode(f.read())
                f.close()
                if not candidates: raise StopIteration
                yield candidates
            except socket.error:
                pass


    def add_processed(self, processed):
        try:
            f = urllib2.urlopen(self.url + '/processed', data=encode(processed))
            f.close()
        except socket.error:
            pass

    def add_candiates(self, next_candidates):
        data = encode(next_candidates)
        try:
            f = urllib2.urlopen(self.url + '/candidates', data=data)
            f.close()
        except socket.error:
            pass


def parse_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--batchsize', type=int, default=2)
    return parser.parse_args()

def main():
    args = parse_args()
    client = SearchClient('http://127.0.0.1:8080', batchsize=args.batchsize)
    client.search()
    print 'client search finished'

if __name__=='__main__':
    main()
