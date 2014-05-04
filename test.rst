==============
单元测试s
==============

.. module:: werkzeug.test

也许你经常需要对你的的应用进行单元测试或者仅仅检查 Python session 的输出。理论上
讲这是很简单的，你可以伪造一个环境，通过一个假的 `start_response` 遍历应用，但是
这里还有一个更好的方法。


Diving In
=========

Werkzeug 提供了一个 `Client` 对象，可以传入一个 WSGI 应用(可选传入一个 response),
通过这个你可以向应用发出一个虚拟请求。

用三个参数调用一个 response: 应用迭代器、状态和一个 headers。默认 response 返回
一个元组。因为 response 对象有相同的签名，所以你可以像使用 response 一样使用他们
。通过这样一种方式进行测试功能是很理想的。

>>> from werkzeug.test import Client
>>> from werkzeug.testapp import test_app
>>> from werkzeug.wrappers import BaseResponse
>>> c = Client(test_app, BaseResponse)
>>> resp = c.get('/')
>>> resp.status_code
200
>>> resp.headers
Headers([('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', '8339')])
>>> resp.data.splitlines()[0]
'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"'

或默认没有 response:

>>> c = Client(test_app)
>>> app_iter, status, headers = c.get('/')
>>> status
'200 OK'
>>> headers
[('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', '8339')]
>>> ''.join(app_iter).splitlines()[0]
'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"'


Environment Building
====================

.. versionadded:: 0.5

The easiest way to interactively test applications is using the
:class:`EnvironBuilder`.  It can create both standard WSGI environments
and request objects.

The following example creates a WSGI environment with one uploaded file
and a form field:

>>> from werkzeug.test import EnvironBuilder
>>> from StringIO import StringIO
>>> builder = EnvironBuilder(method='POST', data={'foo': 'this is some text',
...      'file': (StringIO('my file contents'), 'test.txt')})
>>> env = builder.get_environ()

The resulting environment is a regular WSGI environment that can be used for
further processing:

>>> from werkzeug.wrappers import Request
>>> req = Request(env)
>>> req.form['foo']
u'this is some text'
>>> req.files['file']
<FileStorage: u'test.txt' ('text/plain')>
>>> req.files['file'].read()
'my file contents'

The :class:`EnvironBuilder` figures out the content type automatically if you
pass a dict to the constructor as `data`.  If you provide a string or an
input stream you have to do that yourself.

By default it will try to use ``application/x-www-form-urlencoded`` and only
use ``multipart/form-data`` if files are uploaded:

>>> builder = EnvironBuilder(method='POST', data={'foo': 'bar'})
>>> builder.content_type
'application/x-www-form-urlencoded'
>>> builder.files['foo'] = StringIO('contents')
>>> builder.content_type
'multipart/form-data'

If a string is provided as data (or an input stream) you have to specify
the content type yourself:

>>> builder = EnvironBuilder(method='POST', data='{"json": "this is"}')
>>> builder.content_type
>>> builder.content_type = 'application/json'


Testing API
===========

.. autoclass:: EnvironBuilder
   :members:

   .. attribute:: path

      The path of the application.  (aka `PATH_INFO`)

   .. attribute:: charset

      The charset used to encode unicode data.

   .. attribute:: headers

      A :class:`Headers` object with the request headers.

   .. attribute:: errors_stream

      The error stream used for the `wsgi.errors` stream.

   .. attribute:: multithread

      The value of `wsgi.multithread`

   .. attribute:: multiprocess

      The value of `wsgi.multiprocess`

   .. attribute:: environ_base

      The dict used as base for the newly create environ.

   .. attribute:: environ_overrides

      A dict with values that are used to override the generated environ.

   .. attribute:: input_stream
    
      The optional input stream.  This and :attr:`form` / :attr:`files`
      is mutually exclusive.  Also do not provide this stream if the
      request method is not `POST` / `PUT` or something comparable.

.. autoclass:: Client

   .. automethod:: open(options)

   .. automethod:: get(options)

   .. automethod:: post(options)

   .. automethod:: put(options)

   .. automethod:: delete(options)

   .. automethod:: head(options)

.. autofunction:: create_environ([options])

.. autofunction:: run_wsgi_app
