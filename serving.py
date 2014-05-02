# -*- coding: utf-8 -*-
"""
    werkzeug.serving
    ~~~~~~~~~~~~~~~~

    There are many ways to serve a WSGI application.  While you're developing
    it you usually don't want a full blown webserver like Apache but a simple
    standalone one.  From Python 2.5 onwards there is the `wsgiref`_ server in
    the standard library.  If you're using older versions of Python you can
    download the package from the cheeseshop.

    However there are some caveats. Sourcecode won't reload itself when
    changed and each time you kill the server using ``^C`` you get an
    `KeyboardInterrupt` error.  While the latter is easy to solve the first
    one can be a pain in the ass in some situations.

    The easiest way is creating a small ``start-myproject.py`` that runs the
    application::

        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        from myproject import make_app
        from werkzeug.serving import run_simple

        app = make_app(...)
        run_simple('localhost', 8080, app, use_reloader=True)

    You can also pass it a `extra_files` keyword argument with a list of
    additional files (like configuration files) you want to observe.

    For bigger applications you should consider using `werkzeug.script`
    instead of a simple start file.


    :copyright: (c) 2014 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement

import os
import socket
import sys
import time
import signal
import subprocess

try:
    import thread
except ImportError:
    import _thread as thread

try:
    from SocketServer import ThreadingMixIn, ForkingMixIn
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from socketserver import ThreadingMixIn, ForkingMixIn
    from http.server import HTTPServer, BaseHTTPRequestHandler

import werkzeug
from werkzeug._internal import _log
from werkzeug._compat import iteritems, PY2, reraise, text_type, \
     wsgi_encoding_dance
from werkzeug.urls import url_parse, url_unquote
from werkzeug.exceptions import InternalServerError, BadRequest


class WSGIRequestHandler(BaseHTTPRequestHandler, object):
    """A request handler that implements WSGI dispatching."""

    @property
    def server_version(self):
        return 'Werkzeug/' + werkzeug.__version__

    def make_environ(self):
        request_url = url_parse(self.path)

        def shutdown_server():
            self.server.shutdown_signal = True

        url_scheme = self.server.ssl_context is None and 'http' or 'https'
        path_info = url_unquote(request_url.path)

        environ = {
            'wsgi.version':         (1, 0),
            'wsgi.url_scheme':      url_scheme,
            'wsgi.input':           self.rfile,
            'wsgi.errors':          sys.stderr,
            'wsgi.multithread':     self.server.multithread,
            'wsgi.multiprocess':    self.server.multiprocess,
            'wsgi.run_once':        False,
            'werkzeug.server.shutdown':
                                    shutdown_server,
            'SERVER_SOFTWARE':      self.server_version,
            'REQUEST_METHOD':       self.command,
            'SCRIPT_NAME':          '',
            'PATH_INFO':            wsgi_encoding_dance(path_info),
            'QUERY_STRING':         wsgi_encoding_dance(request_url.query),
            'CONTENT_TYPE':         self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH':       self.headers.get('Content-Length', ''),
            'REMOTE_ADDR':          self.client_address[0],
            'REMOTE_PORT':          self.client_address[1],
            'SERVER_NAME':          self.server.server_address[0],
            'SERVER_PORT':          str(self.server.server_address[1]),
            'SERVER_PROTOCOL':      self.request_version
        }

        for key, value in self.headers.items():
            key = 'HTTP_' + key.upper().replace('-', '_')
            if key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
                environ[key] = value

        if request_url.netloc:
            environ['HTTP_HOST'] = request_url.netloc

        return environ

    def run_wsgi(self):
        if self.headers.get('Expect', '').lower().strip() == '100-continue':
            self.wfile.write(b'HTTP/1.1 100 Continue\r\n\r\n')

        environ = self.make_environ()
        headers_set = []
        headers_sent = []

        def write(data):
            assert headers_set, 'write() before start_response'
            if not headers_sent:
                status, response_headers = headers_sent[:] = headers_set
                try:
                    code, msg = status.split(None, 1)
                except ValueError:
                    code, msg = status, ""
                self.send_response(int(code), msg)
                header_keys = set()
                for key, value in response_headers:
                    self.send_header(key, value)
                    key = key.lower()
                    header_keys.add(key)
                if 'content-length' not in header_keys:
                    self.close_connection = True
                    self.send_header('Connection', 'close')
                if 'server' not in header_keys:
                    self.send_header('Server', self.version_string())
                if 'date' not in header_keys:
                    self.send_header('Date', self.date_time_string())
                self.end_headers()

            assert type(data) is bytes, 'applications must write bytes'
            self.wfile.write(data)
            self.wfile.flush()

        def start_response(status, response_headers, exc_info=None):
            if exc_info:
                try:
                    if headers_sent:
                        reraise(*exc_info)
                finally:
                    exc_info = None
            elif headers_set:
                raise AssertionError('Headers already set')
            headers_set[:] = [status, response_headers]
            return write

        def execute(app):
            application_iter = app(environ, start_response)
            try:
                for data in application_iter:
                    write(data)
                if not headers_sent:
                    write(b'')
            finally:
                if hasattr(application_iter, 'close'):
                    application_iter.close()
                application_iter = None

        try:
            execute(self.server.app)
        except (socket.error, socket.timeout) as e:
            self.connection_dropped(e, environ)
        except Exception:
            if self.server.passthrough_errors:
                raise
            from werkzeug.debug.tbtools import get_current_traceback
            traceback = get_current_traceback(ignore_system_exceptions=True)
            try:
                # if we haven't yet sent the headers but they are set
                # we roll back to be able to set them again.
                if not headers_sent:
                    del headers_set[:]
                execute(InternalServerError())
            except Exception:
                pass
            self.server.log('error', 'Error on request:\n%s',
                            traceback.plaintext)

    def handle(self):
        """Handles a request ignoring dropped connections."""
        rv = None
        try:
            rv = BaseHTTPRequestHandler.handle(self)
        except (socket.error, socket.timeout) as e:
            self.connection_dropped(e)
        except Exception:
            if self.server.ssl_context is None or not is_ssl_error():
                raise
        if self.server.shutdown_signal:
            self.initiate_shutdown()
        return rv

    def initiate_shutdown(self):
        """A horrible, horrible way to kill the server for Python 2.6 and
        later.  It's the best we can do.
        """
        # Windows does not provide SIGKILL, go with SIGTERM then.
        sig = getattr(signal, 'SIGKILL', signal.SIGTERM)
        # reloader active
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            os.kill(os.getpid(), sig)
        # python 2.7
        self.server._BaseServer__shutdown_request = True
        # python 2.6
        self.server._BaseServer__serving = False

    def connection_dropped(self, error, environ=None):
        """Called if the connection was closed by the client.  By default
        nothing happens.
        """

    def handle_one_request(self):
        """Handle a single HTTP request."""
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
        elif self.parse_request():
            return self.run_wsgi()

    def send_response(self, code, message=None):
        """Send the response header and log the response code."""
        self.log_request(code)
        if message is None:
            message = code in self.responses and self.responses[code][0] or ''
        if self.request_version != 'HTTP/0.9':
            hdr = "%s %d %s\r\n" % (self.protocol_version, code, message)
            self.wfile.write(hdr.encode('ascii'))

    def version_string(self):
        return BaseHTTPRequestHandler.version_string(self).strip()

    def address_string(self):
        return self.client_address[0]

    def log_request(self, code='-', size='-'):
        self.log('info', '"%s" %s %s', self.requestline, code, size)

    def log_error(self, *args):
        self.log('error', *args)

    def log_message(self, format, *args):
        self.log('info', format, *args)

    def log(self, type, message, *args):
        _log(type, '%s - - [%s] %s\n' % (self.address_string(),
                                         self.log_date_time_string(),
                                         message % args))


#: backwards compatible name if someone is subclassing it
BaseRequestHandler = WSGIRequestHandler


def generate_adhoc_ssl_pair(cn=None):
    from random import random
    from OpenSSL import crypto

    # pretty damn sure that this is not actually accepted by anyone
    if cn is None:
        cn = '*'

    cert = crypto.X509()
    cert.set_serial_number(int(random() * sys.maxsize))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365)

    subject = cert.get_subject()
    subject.CN = cn
    subject.O = 'Dummy Certificate'

    issuer = cert.get_issuer()
    issuer.CN = 'Untrusted Authority'
    issuer.O = 'Self-Signed'

    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 768)
    cert.set_pubkey(pkey)
    cert.sign(pkey, 'md5')

    return cert, pkey


def make_ssl_devcert(base_path, host=None, cn=None):
    """创建一个 SSL 密钥。用于代替 ``'adhoc'`` 密钥将会在服务启动的时候创建一个
    新的证书。他接受一个存放密钥、证书和主机或 CN 的路径。如果主机拥有这个将会
    使用 CN ``*.host/CN=host``。

    更多信息请看 :func:`run_simple`。

    .. versionadded:: 0.9

    :param base_path: 证书和密钥的路径。扩展名是 ``.crt`` 的文件被添加到证书，扩
    展名为 ``.key`` 的文件被添加到密钥。
    :param host: 主机的名字。这个用于替代 `cn`。
    :param cn: 使用 `CN`。
    """
    from OpenSSL import crypto
    if host is not None:
        cn = '*.%s/CN=%s' % (host, host)
    cert, pkey = generate_adhoc_ssl_pair(cn=cn)

    cert_file = base_path + '.crt'
    pkey_file = base_path + '.key'

    with open(cert_file, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(pkey_file, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))

    return cert_file, pkey_file


def generate_adhoc_ssl_context():
    """Generates an adhoc SSL context for the development server."""
    from OpenSSL import SSL
    cert, pkey = generate_adhoc_ssl_pair()
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.use_privatekey(pkey)
    ctx.use_certificate(cert)
    return ctx


def load_ssl_context(cert_file, pkey_file):
    """Loads an SSL context from a certificate and private key file."""
    from OpenSSL import SSL
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.use_certificate_file(cert_file)
    ctx.use_privatekey_file(pkey_file)
    return ctx


def is_ssl_error(error=None):
    """Checks if the given error (or the current one) is an SSL error."""
    if error is None:
        error = sys.exc_info()[1]
    from OpenSSL import SSL
    return isinstance(error, SSL.Error)


class _SSLConnectionFix(object):
    """Wrapper around SSL connection to provide a working makefile()."""

    def __init__(self, con):
        self._con = con

    def makefile(self, mode, bufsize):
        return socket._fileobject(self._con, mode, bufsize)

    def __getattr__(self, attrib):
        return getattr(self._con, attrib)

    def shutdown(self, arg=None):
        try:
            self._con.shutdown()
        except Exception:
            pass


def select_ip_version(host, port):
    """Returns AF_INET4 or AF_INET6 depending on where to connect to."""
    # disabled due to problems with current ipv6 implementations
    # and various operating systems.  Probably this code also is
    # not supposed to work, but I can't come up with any other
    # ways to implement this.
    ##try:
    ##    info = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
    ##                              socket.SOCK_STREAM, 0,
    ##                              socket.AI_PASSIVE)
    ##    if info:
    ##        return info[0][0]
    ##except socket.gaierror:
    ##    pass
    if ':' in host and hasattr(socket, 'AF_INET6'):
        return socket.AF_INET6
    return socket.AF_INET


class BaseWSGIServer(HTTPServer, object):
    """Simple single-threaded, single-process WSGI server."""
    multithread = False
    multiprocess = False
    request_queue_size = 128

    def __init__(self, host, port, app, handler=None,
                 passthrough_errors=False, ssl_context=None):
        if handler is None:
            handler = WSGIRequestHandler
        self.address_family = select_ip_version(host, port)
        HTTPServer.__init__(self, (host, int(port)), handler)
        self.app = app
        self.passthrough_errors = passthrough_errors
        self.shutdown_signal = False

        if ssl_context is not None:
            try:
                from OpenSSL import tsafe
            except ImportError:
                raise TypeError('SSL is not available if the OpenSSL '
                                'library is not installed.')
            if isinstance(ssl_context, tuple):
                ssl_context = load_ssl_context(*ssl_context)
            if ssl_context == 'adhoc':
                ssl_context = generate_adhoc_ssl_context()
            self.socket = tsafe.Connection(ssl_context, self.socket)
            self.ssl_context = ssl_context
        else:
            self.ssl_context = None

    def log(self, type, message, *args):
        _log(type, message, *args)

    def serve_forever(self):
        self.shutdown_signal = False
        try:
            HTTPServer.serve_forever(self)
        except KeyboardInterrupt:
            pass

    def handle_error(self, request, client_address):
        if self.passthrough_errors:
            raise
        else:
            return HTTPServer.handle_error(self, request, client_address)

    def get_request(self):
        con, info = self.socket.accept()
        if self.ssl_context is not None:
            con = _SSLConnectionFix(con)
        return con, info


class ThreadedWSGIServer(ThreadingMixIn, BaseWSGIServer):
    """A WSGI server that does threading."""
    multithread = True


class ForkingWSGIServer(ForkingMixIn, BaseWSGIServer):
    """A WSGI server that does forking."""
    multiprocess = True

    def __init__(self, host, port, app, processes=40, handler=None,
                 passthrough_errors=False, ssl_context=None):
        BaseWSGIServer.__init__(self, host, port, app, handler,
                                passthrough_errors, ssl_context)
        self.max_children = processes


def make_server(host, port, app=None, threaded=False, processes=1,
                request_handler=None, passthrough_errors=False,
                ssl_context=None):
    """Create a new server instance that is either threaded, or forks
    or just processes one request after another.
    """
    if threaded and processes > 1:
        raise ValueError("cannot have a multithreaded and "
                         "multi process server.")
    elif threaded:
        return ThreadedWSGIServer(host, port, app, request_handler,
                                  passthrough_errors, ssl_context)
    elif processes > 1:
        return ForkingWSGIServer(host, port, app, processes, request_handler,
                                 passthrough_errors, ssl_context)
    else:
        return BaseWSGIServer(host, port, app, request_handler,
                              passthrough_errors, ssl_context)


def _iter_module_files():
    # The list call is necessary on Python 3 in case the module
    # dictionary modifies during iteration.
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            old = None
            while not os.path.isfile(filename):
                old = filename
                filename = os.path.dirname(filename)
                if filename == old:
                    break
            else:
                if filename[-4:] in ('.pyc', '.pyo'):
                    filename = filename[:-1]
                yield filename


def _reloader_stat_loop(extra_files=None, interval=1):
    """When this function is run from the main thread, it will force other
    threads to exit when any modules currently loaded change.

    Copyright notice.  This function is based on the autoreload.py from
    the CherryPy trac which originated from WSGIKit which is now dead.

    :param extra_files: a list of additional files it should watch.
    """
    from itertools import chain
    mtimes = {}
    while 1:
        for filename in chain(_iter_module_files(), extra_files or ()):
            try:
                mtime = os.stat(filename).st_mtime
            except OSError:
                continue

            old_time = mtimes.get(filename)
            if old_time is None:
                mtimes[filename] = mtime
                continue
            elif mtime > old_time:
                _log('info', ' * Detected change in %r, reloading' % filename)
                sys.exit(3)
        time.sleep(interval)


def _reloader_inotify(extra_files=None, interval=None):
    # Mutated by inotify loop when changes occur.
    changed = [False]

    # Setup inotify watches
    from pyinotify import WatchManager, Notifier

    # this API changed at one point, support both
    try:
        from pyinotify import EventsCodes as ec
        ec.IN_ATTRIB
    except (ImportError, AttributeError):
        import pyinotify as ec

    wm = WatchManager()
    mask = ec.IN_DELETE_SELF | ec.IN_MOVE_SELF | ec.IN_MODIFY | ec.IN_ATTRIB

    def signal_changed(event):
        if changed[0]:
            return
        _log('info', ' * Detected change in %r, reloading' % event.path)
        changed[:] = [True]

    for fname in extra_files or ():
        wm.add_watch(fname, mask, signal_changed)

    # ... And now we wait...
    notif = Notifier(wm)
    try:
        while not changed[0]:
            # always reiterate through sys.modules, adding them
            for fname in _iter_module_files():
                wm.add_watch(fname, mask, signal_changed)
            notif.process_events()
            if notif.check_events(timeout=interval):
                notif.read_events()
            # TODO Set timeout to something small and check parent liveliness
    finally:
        notif.stop()
    sys.exit(3)


# currently we always use the stat loop reloader for the simple reason
# that the inotify one does not respond to added files properly.  Also
# it's quite buggy and the API is a mess.
reloader_loop = _reloader_stat_loop


def restart_with_reloader():
    """Spawn a new Python interpreter with the same arguments as this one,
    but running the reloader thread.
    """
    while 1:
        _log('info', ' * Restarting with reloader')
        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        new_environ['WERKZEUG_RUN_MAIN'] = 'true'

        # a weird bug on windows. sometimes unicode strings end up in the
        # environment and subprocess.call does not like this, encode them
        # to latin1 and continue.
        if os.name == 'nt' and PY2:
            for key, value in iteritems(new_environ):
                if isinstance(value, text_type):
                    new_environ[key] = value.encode('iso-8859-1')

        exit_code = subprocess.call(args, env=new_environ)
        if exit_code != 3:
            return exit_code


def run_with_reloader(main_func, extra_files=None, interval=1):
    """Run the given function in an independent python interpreter."""
    import signal
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        thread.start_new_thread(main_func, ())
        try:
            reloader_loop(extra_files, interval)
        except KeyboardInterrupt:
            return
    try:
        sys.exit(restart_with_reloader())
    except KeyboardInterrupt:
        pass


def run_simple(hostname, port, application, use_reloader=False,
               use_debugger=False, use_evalex=True,
               extra_files=None, reloader_interval=1, threaded=False,
               processes=1, request_handler=None, static_files=None,
               passthrough_errors=False, ssl_context=None):
    """用 wsgiref 带可选参数 reloader 运行一个应用，通过包裹 `wsgiref` 来改正多线程 WSGI
    的默认的错误报告，添加可选的多线程，支持 fork。

    这个函数也有一个命令行接口::

        python -m werkzeug.serving --help

    .. versionadded:: 0.5
       通过添加 `static_files` 简单支持静态文件和 `passthrough_errors`。

    .. versionadded:: 0.6
       支持添加 SSL。

    .. versionadded:: 0.8
       添加支持从 certificate 自动加载 SSL 上下文和私钥。
       file and private key.

    .. versionadded:: 0.9
       添加命令行接口。

    :param hostname: 应用的服务器。例子: ``'localhost'``。
    :param port: 服务器接口。 例子: ``8080``
    :param application: 要执行的 WSGI 应用。
    :param use_reloader: 当模块更改是否自动重启 python 进程？
    :param use_debugger: 是否开启 werkzeug 调试?
    :param use_evalex: 是否开启异常诊断功能?
    :param extra_files: 模块可以加载的件列表。比如配置文件。
    :param reloader_interval: 加载的时间间隔。
    :param threaded: 每个请求是否被放在一个独立线程?
    :param processes: 请求处理线程的最大个数。
    :param request_handler: 用于替换默认的可选参数。你可以用一个不同的
                            :class:`~BaseHTTPServer.BaseHTTPRequestHandler`
                            子类替换它。
    :param static_files: 一个静态文件地址的字典。和 :class:`SharedDataMiddleware`
                        差不多。它实际上仅仅是在服务器运行前用中间件包裹一个应用。
    :param passthrough_errors: 设为 `True` 关闭错误捕获。这意味着服务可能会因错误而
                               崩溃，但是对于调试钩子很有用 (比如pdb)。
    :param ssl_context: 连接的 SSL 上下文。或者一个 OpenSSL 上下文，从
                    ``(cert_file, pkey_file)`` 得到的一个元组，服务是 ``'adhoc'`` 的
                    则会自动创建一个，如果是 `None` 则会关闭 SSL(这是默认的)。
    """
    if use_debugger:
        from werkzeug.debug import DebuggedApplication
        application = DebuggedApplication(application, use_evalex)
    if static_files:
        from werkzeug.wsgi import SharedDataMiddleware
        application = SharedDataMiddleware(application, static_files)

    def inner():
        make_server(hostname, port, application, threaded,
                    processes, request_handler,
                    passthrough_errors, ssl_context).serve_forever()

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        display_hostname = hostname != '*' and hostname or 'localhost'
        if ':' in display_hostname:
            display_hostname = '[%s]' % display_hostname
        quit_msg = '(Press CTRL+C to quit)'
        _log('info', ' * Running on %s://%s:%d/ %s', ssl_context is None
             and 'http' or 'https', display_hostname, port, quit_msg)
    if use_reloader:
        # Create and destroy a socket so that any exceptions are raised before
        # we spawn a separate Python interpreter and lose this ability.
        address_family = select_ip_version(hostname, port)
        test_socket = socket.socket(address_family, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((hostname, port))
        test_socket.close()
        run_with_reloader(inner, extra_files, reloader_interval)
    else:
        inner()

def main():
    '''A simple command-line interface for :py:func:`run_simple`.'''

    # in contrast to argparse, this works at least under Python < 2.7
    import optparse
    from werkzeug.utils import import_string

    parser = optparse.OptionParser(usage='Usage: %prog [options] app_module:app_object')
    parser.add_option('-b', '--bind', dest='address',
                      help='The hostname:port the app should listen on.')
    parser.add_option('-d', '--debug', dest='use_debugger',
                      action='store_true', default=False,
                      help='Use Werkzeug\'s debugger.')
    parser.add_option('-r', '--reload', dest='use_reloader',
                      action='store_true', default=False,
                      help='Reload Python process if modules change.')
    options, args = parser.parse_args()

    hostname, port = None, None
    if options.address:
        address = options.address.split(':')
        hostname = address[0]
        if len(address) > 1:
            port = address[1]

    if len(args) != 1:
        sys.stdout.write('No application supplied, or too much. See --help\n')
        sys.exit(1)
    app = import_string(args[0])

    run_simple(
        hostname=(hostname or '127.0.0.1'), port=int(port or 5000),
        application=app, use_reloader=options.use_reloader,
        use_debugger=options.use_debugger
    )

if __name__ == '__main__':
    main()
