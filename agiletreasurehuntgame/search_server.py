# coding: utf-8

import web
from web.webapi import context
import pickle
import base64

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
            return encode(SearchServer.search.pop_candidate())

        def POST(self):
            candidates = decode(context.env['wsgi.input'].read())
            SearchServer.search.add_candiates(candidates)
            return ''

    class Processed:
        def POST(self):
            peocessed = decode(context.env['wsgi.input'].read())
            SearchServer.search.add_processed(processed)
            return ''

    @classmethod
    def run(cls, search):
        cls.search = search
        app = web.application(SearchServer.urls, cls.__dict__, autoreload=True)
        app.run()

class SearchClient(object):
    def __init__(self):
        pass

    def search(self):
        for candidate in self.candidates():
            self.process_candidate(candidate)

    def process_candidate(self, candidate):
        self.dumper.cycle(candidate)
        if not candidate.is_final():
            self.add_candiates(candidate.next_states())
        self.add_processed(candidate)

def main():
    import othello, search
    search = search.Search(dump=True)
    start = othello.OthelloCandidate(4, othello.Board(width=3, height=3))
    search.add_candiates(start.next_states())

    SearchServer.run(search)


if __name__=='__main__':
    main()
