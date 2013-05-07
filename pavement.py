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
@cmdopts(RUNNING_OPTS)
def server(options):
    depth = options.server.depth if 'depth' in options.server else 3
    size = options.server.size if 'size' in options.server else 3
    sh('python -m agiletreasurehuntgame.search_server -d %s -s %s'%(depth, size))

@task
@cmdopts([
    ('concurrency=', 'c', 'how many client process to start')
])
def client(options):
    concurrency = int(options.client.concurrency) if 'concurrency' in options.client else 4

    def run_client():
        if os.name == 'nt':
            os.system('python -m agiletreasurehuntgame.search_client')
        else:
            sh('python -m agiletreasurehuntgame.search_clien')
    import threading
    for i in range(concurrency):
        threading.Thread(target=run_client).start()

@task
@cmdopts(RUNNING_OPTS)
def run():
    depth = options.run.depth if 'depth' in options.run else 3
    size = options.run.size if 'size' in options.run else 3
    sh('python -m agiletreasurehuntgame.othello -d %s -s %s'%(depth, size))
