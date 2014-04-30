==========
快速开始
==========

.. module:: werkzeug

文档的这部分内容将会向你展示如何使用 Werkzeug 最重要的部分。意在让开发者对
:pep:`333` (WSGI) 和 :rfc:`2616` (HTTP) 有一个基本的了解。

.. warning::

   确保在文档建议的地方导入所有对象。理论上从不同的地方导入对象是可行的，但是在
   这却是不被支持的。

   例如 :class:`MultiDict` 是一个 `werkzeug` 模块，但它在内部却不是 `Werkzeug`
   实现的。


WSGI 环境
================

WSGI 环境包含所有用户向应用发送信息。你可以通过它向 WSGI 发送信息，但是你也可以
使用 :func:`create_environ` 辅助函数创建一个 WSGI 环境字典:

>>> from werkzeug.test import create_environ
>>> environ = create_environ('/foo', 'http://localhost:8080/')

现在我们创造了一个环境:

>>> environ['PATH_INFO']
'/foo'
>>> environ['SCRIPT_NAME']
''
>>> environ['SERVER_NAME']
'localhost'

通常没人愿意直接使用 environ 因为它对字节串是有限制的，而且不提供访问表单数据的
方法除非手动解析数据。


Request
=============

:class:`Request` 对象访问请求数据是很有趣的。它封装 `environ` 并提供只读的方法访
问数据:

>>> from werkzeug.wrappers import Request
>>> request = Request(environ)

现在你可以访问重要的变量，Werkzeug 将会帮你解析并解码他们。默认的字符集是 `utf-8`
但是你可以通过 :class:`Request` 子类更改。

>>> request.path
u'/foo'
>>> request.script_root
u''
>>> request.host
'localhost:8080'
>>> request.url
'http://localhost:8080/foo'

我们也可以得到 HTTP 请求方法:

>>> request.method
'GET'

通过这个方法我们可以访问 URL 参数(查询的字符串) 和 POST/PUT 请求提交的数据。

为了测试，我们通过 :meth:`~BaseRequest.from_values` 方法得到的数据创建一个请求对象:

>>> from cStringIO import StringIO
>>> data = "name=this+is+encoded+form+data&another_key=another+one"
>>> request = Request.from_values(query_string='foo=bar&blah=blafasel',
...    content_length=len(data), input_stream=StringIO(data),
...    content_type='application/x-www-form-urlencoded',
...    method='POST')
...
>>> request.method
'POST'

我们可以很容易访问 URL 参数:

>>> request.args.keys()
['blah', 'foo']
>>> request.args['blah']
u'blafasel'

访问提交的数据也是一样的:

>>> request.form['name']
u'this is encoded form data'

处理上传文件不再困难正如下例::

    def store_file(request):
        file = request.files.get('my_file')
        if file:
            file.save('/where/to/store/the/file.txt')
        else:
            handle_the_error()

`files` 代表一个 :class:`FileStorage` 对象，提供一些常见的操作。

通过 :class:`~BaseRequest.headers` 的属性可以得到请求的 headers。

>>> request.headers['Content-Length']
'54'
>>> request.headers['Content-Type']
'application/x-www-form-urlencoded'

头信息的键不区分大小写。


解析 Headers
==============

这里还有更多 Werkzeug 提供的使用 HTTP headers 和其他请求数据的常用的方法。

让我们用典型的 web 浏览器发送数据来创建一个请求对象。以便于更真实的测试:

>>> environ = create_environ()
>>> environ.update(
...     HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; U; Mac OS X 10.5; en-US; ) Firefox/3.1',
...     HTTP_ACCEPT='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
...     HTTP_ACCEPT_LANGUAGE='de-at,en-us;q=0.8,en;q=0.5',
...     HTTP_ACCEPT_ENCODING='gzip,deflate',
...     HTTP_ACCEPT_CHARSET='ISO-8859-1,utf-8;q=0.7,*;q=0.7',
...     HTTP_IF_MODIFIED_SINCE='Fri, 20 Feb 2009 10:10:25 GMT',
...     HTTP_IF_NONE_MATCH='"e51c9-1e5d-46356dc86c640"',
...     HTTP_CACHE_CONTROL='max-age=0'
... )
...
>>> request = Request(environ)

让我们从最没有用(- -)的 headers 开始: the user agent:

>>> request.user_agent.browser
'firefox'
>>> request.user_agent.platform
'macos'
>>> request.user_agent.version
'3.1'
>>> request.user_agent.language
'en-US'

一个更有用的 headers 是 Accept header。这个 header 将会告诉 web 应用可以处理并怎么处理
MIME类型，所有 accept header 被严格分类，最重要的是第一条:

>>> request.accept_mimetypes.best
'text/html'
>>> 'application/xhtml+xml' in request.accept_mimetypes
True
>>> print request.accept_mimetypes["application/json"]
0.8

可使用的语言也是一样:

>>> request.accept_languages.best
'de-at'
>>> request.accept_languages.values()
['de-at', 'en-us', 'en']

当然还有编码和字符集:

>>> 'gzip' in request.accept_encodings
True
>>> request.accept_charsets.best
'ISO-8859-1'
>>> 'utf-8' in request.accept_charsets
True

标准化是可行的，所以你可以安全的使用不同形式来执行控制检查:

>>> 'UTF8' in request.accept_charsets
True
>>> 'de_AT' in request.accept_languages
True

E-tags 和其他条件 header 也可以被解析:

>>> request.if_modified_since
datetime.datetime(2009, 2, 20, 10, 10, 25)
>>> request.if_none_match
<ETags '"e51c9-1e5d-46356dc86c640"'>
>>> request.cache_control
<RequestCacheControl 'max-age=0'>
>>> request.cache_control.max_age
0
>>> 'e51c9-1e5d-46356dc86c640' in request.if_none_match
True


响应
=========

Response 对象和请求对象相对。他常用于向客户端发送响应数据。实际上，在 WSGI 应用
中没有什么比 Response 对象更重要了。

那么你要做的不是从一个 WSGI 应用中返回 *returning* 响应对象，而是在 WSGI 应用内
部调用一个 WSGI 应用并返回调用的值。

想象一个标准的 "Hello World" WSGI 应用::

    def application(environ, start_res ponse):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['Hello World!']

带着一个响应对象的将会是这样的::

    from werkzeug.wrappers import Response

    def application(environ, s tart_response):
        response = Response('Hello World!')
        return response(environ, start_response)

同时,不同与请求对象，响应对象被设计为可修改的。所以你还可以进行如下操作:

>>> from werkzeug.wrappers import Response
>>> response = Response("Hello World!")
>>> response.headers['content-type']
'text/plain; charset=utf-8'
>>> response.data
'Hello World!'
>>> response.headers['content-length'] = len(response.data)

你可以用同样的方式修改响应状态，或者仅仅一个状态吗、一条信息:

>>> response.status
'200 OK'
>>> response.status = '404 Not Found'
>>> response.status_code
404
>>> response.status_code = 400
>>> response.status
'400 BAD REQUEST'

正如你看到的，状态属性是双向的,你可以同时看到 :attr:`~BaseResponse.status` 和 
:attr:`~BaseResponse.status_code` ，他们相互对应的。

同时常见的 headers 是公开的，可以作为属性访问或者用方法设置/获取他们:

>>> response.content_length
12
>>> from datetime import datetime
>>> response.date = datetime(2009, 2, 20, 17, 42, 51)
>>> response.headers['Date']
'Fri, 20 Feb 2009 17:42:51 GMT'

因为 etags 可以使 weak 或者 strong，所以这里有方法可以设置它:

>>> response.set_etag("12345-abcd")
>>> response.headers['etag']
'"12345-abcd"'
>>> response.get_etag()
('12345-abcd', False)
>>> response.set_etag("12345-abcd", weak=True)
>>> response.get_etag()
('12345-abcd', True)

一些有用的 headers 是可变的结构，比如 `Content-` header 是一个值的集合:

>>> response.content_language.add('en-us')
>>> response.content_language.add('en')
>>> response.headers['Content-Language']
'en-us, en'

下面的 header 值同样不是单一的:

>>> response.headers['Content-Language'] = 'de-AT, de'
>>> response.content_language
HeaderSet(['de-AT', 'de'])

认证 header 也可以这样设置:

>>> response.www_authenticate.set_basic("My protected resource")
>>> response.headers['www-authenticate']
'Basic realm="My protected resource"'

Cookie 同样可以被设置:

>>> response.set_cookie('name', 'value')
>>> response.headers['Set-Cookie']
'name=value; Path=/'
>>> response.set_cookie('name2', 'value2')

如果头出现多次，你可以使用 :meth:`~Headers.getlist` 方法来获取一个 header 的所有值:

>>> response.headers.getlist('Set-Cookie')
['name=value; Path=/', 'name2=value2; Path=/']

最后如果你已经设置了所有条件值，那么你可以根据一个请求作出响应。这意味着，如果
一个请求可以确定已经有了一个信息，只发送一个 header 是很节省流量的。尽管如此，你仍
然应该至少设置一个 etag (用于比较) 和可以被请求对象的 :class:`~BaseRequest.make_conditional`
处理的 header 。

因此，响应是被改进的 (比如状态码改变，移除响应主题，删除实体报头等)。
