from paver.easy import *
from paver.setuputils import setup

import os
import re

setup(
    name='agiletreasurehuntgame',
    version='0.0',
    description='agiletreasurehuntgame simulation',
    author='Yattom',
    author_email='tsutomu.yasui@gmail.com',
    packages=['agiletreasurehuntgame'],
    py_modules=['setup'],
    data_files=[],
    requires=[re.sub('^([^=<>]*)([<>=]+[0-9\.]+)\n', '\\1(\\2)', n) for n in open('requirements.txt').readlines()]
)

@task
@cmdopts([
    ('format=', 'f', 'output format [silent, verbose, xunit]'),
    ('verbose', 'v', 'verbose and stdout (nosetests -v -s)')
])
def test(options):
    format = options.test.format if 'format' in options.test else 'silent'
    opts = ['--with-doctest']
    if format == 'verbose': opts.append('--verbose')
    if format == 'xunit': opts.append('--with-xunit')

    if 'verbose' in options.test:
        opts.append('-v -s')

    files = path('agiletreasurehuntgame').walk('*.py')
    sh('nosetests %s %s'%(' '.join(opts), ' '.join(files)))

RUNNING_OPTS = [
    ('depth=', 'd', 'how many pieces to search'),
    ('size=', 's', 'length of a side of the board'),
]

@task
@cmdopts(RUNNING_OPTS + [
    ('concurrency=', 'c', 'how many client process to start'),
    ('batchsize=', 'b', 'specified number of candidates are passed in single request'),
])
def server(options):
    depth = options.server.depth if 'depth' in options.server else 3
    size = options.server.size if 'size' in options.server else 3
    concurrency = int(options.server.concurrency) if 'concurrency' in options.server else 4
    batchsize = int(options.server.batchsize) if 'batchsize' in options.server else 2

    def run_client():
        import time
        time.sleep(2)
        if os.name == 'nt':
            os.system('python -m agiletreasurehuntgame.search_client -b %s'%(batchsize))
        else:
            sh('python -m agiletreasurehuntgame.search_clien -b %s'%(batchsize))
    import threading
    for i in range(concurrency):
        threading.Thread(target=run_client).start()
    sh('python -m agiletreasurehuntgame.othello -m http -d %s -s %s -b %s -c %s'%(depth, size, batchsize, concurrency))

@task
@cmdopts(RUNNING_OPTS)
def run():
    depth = options.run.depth if 'depth' in options.run else 3
    size = options.run.size if 'size' in options.run else 3
    sh('python -m agiletreasurehuntgame.othello -d %s -s %s'%(depth, size))

@task
@cmdopts(RUNNING_OPTS + [
    ('concurrency=', 'c', 'how many process to start'),
])
def multi():
    depth = options.multi.depth if 'depth' in options.multi else 3
    size = options.multi.size if 'size' in options.multi else 3
    concurrency = int(options.multi.concurrency) if 'concurrency' in options.multi else 4
    sh('python -m agiletreasurehuntgame.othello -d %s -s %s -m multiprocessing -c %s'%(depth, size, concurrency))
