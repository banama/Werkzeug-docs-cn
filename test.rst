==============
单元测试
==============

.. module:: test

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


环境搭建
====================

.. versionadded:: 0.5

交互测试应用 最简单的方法是使用 :class:`EnvironBuilder` 类。它可以创建标准 WSGI 
环境和请求对象。

下面的例子创建了一个上传文件和文件表单的 WSGI 环境:

>>> from werkzeug.test import EnvironBuilder
>>> from StringIO import StringIO
>>> builder = EnvironBuilder(method='POST', data={'foo': 'this is some text',
...      'file': (StringIO('my file contents'), 'test.txt')})
>>> env = builder.get_environ()

返回的环境是一个新的 WSGI 环境，可用于进一步的处理:

>>> from werkzeug.wrappers import Request
>>> req = Request(env)
>>> req.form['foo']
u'this is some text'
>>> req.files['file']
<FileStorage: u'test.txt' ('text/plain')>
>>> req.files['file'].read()
'my file contents'

当你将一个字典传给构造函数数据， :class:`EnvironBuilder` 会自动自动找出内容类型。如
过你传的似乎一个字符串或者输入字符流，你不得不自己来做这些处理。

默认地它将会尝试使用 ``application/x-www-form-urlencoded`` ，如果文件被上传则只
使用 ``multipart/form-data`` :

>>> builder = EnvironBuilder(method='POST', data={'foo': 'bar'})
>>> builder.content_type
'application/x-www-form-urlencoded'
>>> builder.files['foo'] = StringIO('contents')
>>> builder.content_type
'multipart/form-data'

如果传入一个字符串(或一个输入流)，你必须自己指定内容的类型:

>>> builder = EnvironBuilder(method='POST', data='{"json": "this is"}')
>>> builder.content_type
>>> builder.content_type = 'application/json'


测试 API
===========

.. autoclass:: EnvironBuilder
   :members:

   .. attribute:: path

      应用的地址。(又叫 `PATH_INFO`)

   .. attribute:: charset

      编码 unicode 数据的字符集。

   .. attribute:: headers

      一个带着请求 headers的 :class:`Headers` 对象。

   .. attribute:: errors_stream

      用于 `wsgi.errors` 流的错误流。

   .. attribute:: multithread

      `wsgi.multithread` 的值。

   .. attribute:: multiprocess

      `wsgi.multiprocess` 的值。

   .. attribute:: environ_base

      新创建环境的基本字典。

   .. attribute:: environ_overrides

      用于覆盖生成环境的带值字典。

   .. attribute:: input_stream
    
      可选选项输入流。这个和 :attr:`form` / :attr:`files` 是相互独立的。同时如果
      请求方法不是 `POST` / `PUT` 或其他类似方法，不要提供输入流。

.. autoclass:: Client

   .. automethod:: open(options)

   .. automethod:: get(options)

   .. automethod:: post(options)

   .. automethod:: put(options)

   .. automethod:: delete(options)

   .. automethod:: head(options)

.. autofunction:: create_environ([options])

.. autofunction:: run_wsgi_app
