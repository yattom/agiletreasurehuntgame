import random

def dice(n=1):
    return sum([random.randint(1, 6) for i in range(n)])

class Hex(object):
    def __init__(self, coord):
        self.coord = coord
        self.color = None
        self.fertility = 0
        self.remaining_users = 0

    def release(self):
        if self.remaining_users == 0:
            d = dice(self.fertility)
            self.remaining_users = d
            return d
        else:
            d = dice(self.fertility)
            if d > self.remaining_users:
                d = self.remaining_users
            self.remaining_users -= d
            return d


class Market(object):
    '''
    You can setup market by population each hexes.
    >>> m = Market()
    >>> m.hex(4, 3).color = Market.RED
    >>> m.hex(4, 3).fertility = 1

    Releasing on a hex yields 1d6 users
    >>> users = m.hex(4, 3).release()
    >>> users > 0
    True

    Releasing first on a hex (when no users remain), 
    populates the hex with the same number of users to yield later.
    >>> remain = m.hex(4, 3).remaining_users
    >>> users == remain
    True

    Releasing on a hex yields 1d6 users until any users remain.
    >>> users2 = m.hex(4, 3).release()
    >>> users2 > 0
    True
    >>> remain - users2 == m.hex(0, 1).remaining_users
    True

    '''

    BLUE = 'blue'
    RED = 'red'
    GREEN = 'green'
    YELLOW = 'yellow'

    def __init__(self):
        self.hexes = {}
        coords = [
                        (0, 0), (1, 0), (2, 0), (3, 0),
                    (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
                (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),
            (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
                (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
                    (0, 5), (1, 5), (2, 5), (3, 5), (4, 5),
                        (0, 6), (1, 6), (2, 6), (3, 6),
        ]
        for c in coords:
            self.hexes[c] = Hex(coord = c)

    def hex(self, row, col):
        return self.hexes[(row, col)]
