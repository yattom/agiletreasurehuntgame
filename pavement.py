from paver.easy import *
from paver.setuputils import setup

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

@task
def server():
    sh('python -m agiletreasurehuntgame.search_server')

@task
def client():
    sh('python -m agiletreasurehuntgame.search_client')
