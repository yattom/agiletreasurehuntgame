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
            batch = int(web.webapi.input().batch) if 'batch' in web.webapi.input() else 10
            SearchServer.search_lock.acquire()
            candidates = []
            for i in range(batch):
                c = SearchServer.search.pop_candidate()
                if not c: break
                candidates.append(c)
            SearchServer.search_lock.release()
            if not candidates:
                print 'elapsed: %s'%(datetime.datetime.now() - SearchServer.first_req)
            return encode(candidates)

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
            for p in processed:
                SearchServer.search.add_processed(p)
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
    import othello, search
    args = othello.parse_args()
    import sys
    sys.argv[1] = '' # bypass ip arg in web/wsgi.py
    search = search.Search(dump=True)
    search.reset_best()
    search.start_dumper()

    start = othello.OthelloCandidate(args.depth, othello.Board(width=args.width, height=args.height))
    search.add_candiates(start.next_states())
    for candidate in search.candidates():
        search.process_candidate(candidate)
        if len(search.candidates_list) > args.concurrency * args.batchsize: break

    SearchServer.run(search)


if __name__=='__main__':
    main()
