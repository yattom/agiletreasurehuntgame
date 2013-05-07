# coding: utf-8

import web
from web.webapi import context
import pickle
import base64
import datetime
import threading

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
            SearchServer.search_lock.acquire()
            candidate = SearchServer.search.pop_candidate()
            SearchServer.search_lock.release()
            if not candidate:
                print 'elapsed: %s'%(datetime.datetime.now() - SearchServer.first_req)
            return encode(candidate)

        def POST(self):
            candidates = decode(context.env['wsgi.input'].read())
            SearchServer.search_lock.acquire()
            SearchServer.search.add_candiates(candidates)
            SearchServer.search_lock.release()
            return ''

    class Processed:
        def POST(self):
            processed = decode(context.env['wsgi.input'].read())
            SearchServer.search_lock.acquire()
            SearchServer.search.add_processed(processed)
            SearchServer.search_lock.release()
            return ''

    @classmethod
    def init_semaphore(cls, dummy=False):
        if dummy:
            class DummySemaphore:
                def acquire(self): pass
                def release(self): pass
            cls.search_lock = DummySemaphore()
        else:
            cls.search_lock = threading.Semaphore()

    @classmethod
    def run(cls, search):
        cls.init_semaphore(dummy=False)
        cls.search = search
        cls.first_req = 0
        app = web.application(SearchServer.urls, cls.__dict__, autoreload=True)
        app.run()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--depth', type=int, default=3)
    parser.add_argument('-s', '--size', type=int, default=3)
    args = parser.parse_args()

    import othello, search
    search = search.Search(dump=True)
    start = othello.OthelloCandidate(args.depth, othello.Board(width=args.size, height=args.size))
    search.add_candiates(start.next_states())
    search.reset_best()
    search.start_dumper()

    SearchServer.run(search)


if __name__=='__main__':
    main()
