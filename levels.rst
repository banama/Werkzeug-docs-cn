==========
API 标准
==========

.. module:: werkzeug

Werkzeug 的设计意图是一个实用的工具集而不是一个框架。得益于从低级API 中分离出来
的面向用户友好的 API，Werkzeug 可以很简单的扩展另一个系统。

:class:`Request` 和 :class:`Response` 对象(又名"wrappers") 提供的函数也可以来实
现一个小的功能。

例子
=======

这个例子实现一个小的 `Hello World` 应用。显示用户输入的名字::

    from werkzeug.utils import escape
    from werkzeug.wrappers import Request, Response

    @Request.application
    def hello_world(request):
        result = ['<title>Greeter</title>']
        if request.method == 'POST':
            result.append('<h1>Hello %s!</h1>' % escape(request.form['name']))
        result.append('''
            <form action="" method="post">
                <p>Name: <input type="text" name="name" size="20">
                <input type="submit" value="Greet me">
            </form>
        ''')
        return Response(''.join(result), mimet ype='text/html')

另外不用 request 和 response 对象也可以实现这个功能，那就是借助 werkzeug 提供的
解析函数::

    from werkzeug.formparser import parse_form_data
    from werkzeug.utils import escape

    def hello_world(environ, start_response): 
        result = ['<title>Greeter</title>']
        if environ['REQUEST_METHOD'] == 'POST':
            form = parse_form_data(environ)[1]
            result.append('<h1>Hello %s!</h1>' % escape(form['name']))
        result.append('''
            <form action="" method="post">
                <p>Name: <input type="text" name="name" size="20">
                <input type="submit" value="Greet me">
            </form>
        ''')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return [''.join(result)]

高还是低?
============

通常我们更倾向于使用高级的 API(request 和 response 对象)。但是也有些情况你可能更
想使用低级功能。

例如你想在不破坏 Django 或者其他框架的代码的情况下解析 HTTP 头信息。这时你可以利
用 Werkzeug 调用低级 API 来解析 HTTP 头部。

再比如，如果你想写一个 web 框架，或者做单元测试，或者 用 WSGI 中间件将一个老的
CGI/mod_python 应用改成 WSGI 应用，并保证开销。那么你可能更希望使用较低级的 API。
