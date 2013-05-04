# coding: utf-8

import urllib2

from search_server import encode, decode

class SearchClient(object):
    def __init__(self, url):
        self.url = url

    def search(self):
        for candidate in self.candidates():
            self.process_candidate(candidate)

    def process_candidate(self, candidate):
        if not candidate.is_final():
            self.add_candiates(candidate.next_states())
        self.add_processed(candidate)

    def candidates(self):
        while True:
            f = urllib2.urlopen(self.url + '/candidates')
            candidate = decode(f.read())
            print candidate
            if not candidate: raise StopIteration
            yield candidate

    def add_processed(self, processed):
        f = urllib2.urlopen(self.url + '/processed', data=encode(processed))
        f.close()

    def add_candiates(self, next_candidates):
        data = encode(list(next_candidates))
        f = urllib2.urlopen(self.url + '/candidates', data=data)
        f.close()


def main():
    client = SearchClient('http://localhost:8080')
    client.search()

if __name__=='__main__':
    main()
