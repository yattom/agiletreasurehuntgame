# coding: utf-8

import web
from web.webapi import context
import pickle
import base64
import urllib2

from search import Search

def encode(obj):
    '''
    >>> encoded = encode(range(100))
    >>> decode(encoded) == range(100)
    True
    '''
    return base64.encodestring(pickle.dumps(obj))

def decode(s):
    return pickle.loads(base64.decodestring(s))

class SearchServer(object):
    urls = (
        '/candidates', 'Candidates',
        '/processed', 'Processed',
    )

    class Candidates:
        def GET(self):
            print 'Candidates.GET'
            return encode(SearchServer.search.pop_candidate())

        def POST(self):
            print 'Candidates.POST'
            candidates = decode(context.env['wsgi.input'].read())
            print 'candidates=%s'%(candidates)
            SearchServer.search.add_candiates(candidates)
            return ''

    class Processed:
        def POST(self):
            print 'Processed.POST'
            processed = decode(context.env['wsgi.input'].read())
            print 'processed=%s'%(processed)
            SearchServer.search.add_processed(processed)
            return ''

    @classmethod
    def run(cls, search):
        cls.search = search
        app = web.application(SearchServer.urls, cls.__dict__, autoreload=True)
        app.run()

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
    import othello, search
    search = search.Search(dump=True)
    start = othello.OthelloCandidate(3, othello.Board(width=3, height=3))
    search.add_candiates(start.next_states())
    search.reset_best()
    search.start_dumper()

    SearchServer.run(search)


if __name__=='__main__':
    main()
