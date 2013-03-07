from errno import EAGAIN, EWOULDBLOCK
import sys
import time
import subprocess

from gevent.socket import gethostbyname
from gevent.socket import error
from gevent.socket import wait_read
from gevent import sleep


class ImportStringError(ImportError):
    """Provides information about a failed :func:`import_string` attempt."""

    #: String in dotted notation that failed to be imported.
    import_name = None
    #: Wrapped exception.
    exception = None

    def __init__(self, import_name, exception):
        self.import_name = import_name
        self.exception = exception

        msg = (
            'import_string() failed for %r. Possible reasons are:\n\n'
            '- missing __init__.py in a package;\n'
            '- package or module path not included in sys.path;\n'
            '- duplicated package or module name taking precedence in '
            'sys.path;\n'
            '- missing module, class, function or variable;\n\n'
            'Debugged import:\n\n%s\n\n'
            'Original exception:\n\n%s: %s')

        name = ''
        tracked = []
        for part in import_name.replace(':', '.').split('.'):
            name += (name and '.') + part
            imported = import_string(name, silent=True)
            if imported:
                tracked.append((name, getattr(imported, '__file__', None)))
            else:
                track = ['- %r found in %r.' % (n, i) for n, i in tracked]
                track.append('- %r not found.' % name)
                msg = msg % (import_name, '\n'.join(track),
                             exception.__class__.__name__, str(exception))
                break

        ImportError.__init__(self, msg)

    def __repr__(self):
        return '<%s(%r, %r)>' % (self.__class__.__name__, self.import_name,
                                 self.exception)


def import_string(import_name, silent=False):
    """Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).

    If `silent` is True the return value will be `None` if the import fails.

    For better debugging we recommend the new :func:`import_module`
    function to be used instead.

    :param import_name: the dotted name for the object to import.
    :param silent: if set to `True` import errors are ignored and
                   `None` is returned instead.
    :return: imported object
    """
    # force the import name to automatically convert to strings
    if isinstance(import_name, unicode):
        import_name = str(import_name)
    try:
        if ':' in import_name:
            module, obj = import_name.split(':', 1)
        elif '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
        else:
            return __import__(import_name)
            # __import__ is not able to handle unicode strings in the fromlist
        # if the module is a package
        if isinstance(obj, unicode):
            obj = obj.encode('utf-8')
        try:
            return getattr(__import__(module, None, None, [obj]), obj)
        except (ImportError, AttributeError):
            # support importing modules not yet set up by the parent module
            # (or package for that matter)
            modname = module + '.' + obj
            __import__(modname)
            return sys.modules[modname]
    except ImportError, e:
        if not silent:
            raise ImportStringError(import_name, e), None, sys.exc_info()[2]


def parse_address(address):
    try:
        hostname, port = address.rsplit(':', 1)
        port = int(port)
    except ValueError:
        sys.exit('Expected HOST:PORT: %r' % address)
    return gethostbyname(hostname), port


def get_prefixed_sections(settings, prefix, logger=None):
    """Return a dict containing all the behaviors that are defined in the
    settings, in addition to all the behaviors of vaurien
    """
    behaviors = {}
    if logger is None:
        from vaurien import logger

    for section in settings.sections():
        if section.startswith('%s.' % prefix):
            prefixed_name = section[len('%s.' % prefix):]

            # have a look if we have a section named behavior:{behavior}
            settings = settings.getsection('%s.%s' % (prefix, prefixed_name))
            prefixed_location = settings.get('callable', None)
            if not prefixed_location:
                logger.warning('callable not found for %s' % prefixed_name)
                continue
            behavior = import_string(prefixed_location)
            behaviors[prefixed_name] = behavior
    return behaviors


_PROXIES = {}


def start_proxy(proxy_host='localhost', proxy_port=8000,
                backend_host='localhost', backend_port=8888,
                protocol='tcp',
                http=True, warmup=2,
                http_host='localhost', http_port=8080, options=None,
                log_level='info', log_output='-'):
    """Starts a proxy
    """
    proxy = '%s:%d' % (proxy_host, proxy_port)
    backend = '%s:%d' % (backend_host, backend_port)

    cmd = [sys.executable, '-m', 'vaurien.run', '--backend', backend,
           '--proxy', proxy, '--log-level', log_level, '--log-output',
           log_output, '--protocol', protocol]

    if http:
        cmd.extend(['--http', '--http-host', http_host,
                    '--http-port', str(http_port)])

    if options is not None:
        cmd.extend(options)

    proc = subprocess.Popen(cmd)
    time.sleep(warmup)
    if proc.poll():
        raise ValueError("Could not start the proxy")

    _PROXIES[proc.pid] = proc
    return proc.pid


def stop_proxy(pid):
    if pid not in _PROXIES:
        raise ValueError("Not found")
    proc = _PROXIES.pop(pid)
    proc.terminate()
    proc.wait()


def chunked(total, chunk):
    if total <= chunk:
        yield total
    else:
        data = total
        while True:
            if data > chunk:
                yield chunk
                data -= chunk
            else:
                yield data
                break


def get_data(sock, buffer=1024):
    while True:
        try:
            return sock.recv(buffer)
        except error, e:
            if e.args[0] not in (EWOULDBLOCK, EAGAIN):
                raise
            timeout = sock.gettimeout()
            if timeout == 0:
                # we are in async mode here so we just need to switch
                sleep(0)
            else:
                wait_read(sock.fileno(), timeout=timeout)


def extract_settings(args, prefix, name):
    settings = {}
    prefix = '%s_%s_' % (prefix, name)

    for arg in dir(args):
        if not arg.startswith(prefix):
            continue
        settings[arg[len(prefix):]] = getattr(args, arg)

    return settings
