from tempfile import mkstemp
from copy import copy
from unittest import TestCase
import sys
import os
import StringIO

from vaurien import proxy, run
from vaurien.run import main


_CONF = """\
[vaurien]
backend = 0.0.0.0:33

"""


class FakeProxy(object):

    args = kwargs = None

    def __init__(self, *args, **kwargs):
        FakeProxy.args = args
        FakeProxy.kwargs = kwargs

    def serve_forever(self):
        pass


class TestConfig(TestCase):
    def setUp(self):
        self.old = proxy.RandomProxy
        run.RandomProxy = proxy.RandomProxy = FakeProxy
        fd, self.config = mkstemp()
        os.close(fd)
        with open(self.config, 'w') as f:
            f.write(_CONF)

    def tearDown(self):
        run.RandomProxy = proxy.RandomProxy = self.old
        os.remove(self.config)

    def test_config(self):

        # make sure the config is taken into account
        old_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        old = copy(sys.argv)
        try:
            sys.argv = ['vaurien', '--config', self.config]
            main()
        finally:
            sys.argv[:] = old
            sys.stdout = old_stderr

        self.assertEqual(FakeProxy.kwargs['backend'], '0.0.0.0:33')
