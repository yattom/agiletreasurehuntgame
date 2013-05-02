# coding: utf-8

import web

from search import Search

class SearchServer(object):
    urls = (
        '/candidates', 'Candidates',
        '/processed', 'Processed',
    )

    class Candidates:
        def GET(self):
            return SearchServer.search.pop_candidate()

    class Processed:
        def POST(self):
            print 'Index.GET'
            print SearchServer.search
            return 'hello'

    @classmethod
    def run(cls, search):
        cls.search = search
        app = web.application(SearchServer.urls, cls.__dict__)
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
