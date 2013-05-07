# coding: utf-8

import web
from web.webapi import context
import pickle
import base64
import datetime

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
            if SearchServer.first_req == 0:
                SearchServer.first_req = datetime.datetime.now()
            candidate = SearchServer.search.pop_candidate()
            if not candidate:
                print 'elapsed: %s'%(datetime.datetime.now() - SearchServer.first_req)
            return encode(candidate)

        def POST(self):
            candidates = decode(context.env['wsgi.input'].read())
            SearchServer.search.add_candiates(candidates)
            return ''

    class Processed:
        def POST(self):
            processed = decode(context.env['wsgi.input'].read())
            SearchServer.search.add_processed(processed)
            return ''

    @classmethod
    def run(cls, search):
        cls.search = search
        cls.first_req = 0
        app = web.application(SearchServer.urls, cls.__dict__, autoreload=True)
        app.run()


def main():
    import othello, search
    search = search.Search(dump=True)
    start = othello.OthelloCandidate(4, othello.Board(width=3, height=3))
    search.add_candiates(start.next_states())
    search.reset_best()
    search.start_dumper()

    SearchServer.run(search)


if __name__=='__main__':
    main()
