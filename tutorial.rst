=================
Werkzeug 教程
=================

.. module:: routing
.. module:: exceptions

欢迎来到 Werkzeug 教程，我们将会实现一个类似 `TinyURL`_ 的网站来储存 URLS。我们
将会使用的库有模板引擎 `Jinja`_ 2，数据层支持 `redis`_ ，当然还有 WSGI 协议层 Werkzeug。

你可以使用 `pip` 来安装依赖库::

    pip install Jinja2 redis

同时确定你的本地开启一个 redis 服务，如果你是OS X系统，你可以使用 `brew` 来安装 redis::

    brew install redis

如果你是用 Ubuntu 或 Debian, 你可以使用 apt-get::

    sudo apt-get install redis

Redis 专为 UNIX 系统开发，并没有考虑为 Windows 设计。但对于开发来说，非官方的版本已
经足够了，你可以从 `github <https://github.com/dmajkic/redis/downloads>`_ 得到它。

简短介绍
-------------------

在这个教程中，我们将一起用 Werkzeug 创建一个短网址服务。请注意，Werkzeug 并不是
一个框架，它是一个 WSGI 工具集的库，你可以通过它来创建你自己的框架或 Web 应用。
Werkzeug 是非常灵活的，这篇教程用到的一些方法只是 Werkzeug 的一部分。

在数据层，为了保持简单，我们使用 `redis`_ 来代替关系型数据库，而且 `redis`_ 也擅
长来做这些。

最终的结果将会看起来像这样:

.. image:: _static/shortly.png
   :alt: a screenshot of shortly

.. _TinyURL: http://tinyurl.com/
.. _Jinja: http://jinja.pocoo.org/
.. _redis: http://redis.io/

Step 0: WSGI 基础介绍
---------------------------------

Werkzeug 是一个 WSGI 工具包。WSGI 是一个 Web 应用和服务器通信的协议，Web 应用
可以通过 WSGI 一起工作。

一个基本的 “Hello World” WSGI 应用看起来是这样的::

    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['Hello World!'] 

用过 WSGI 应用可以和环境通信，他有一个可调用的 ``start_response`` 。环境包含了
所有进来的信息。 ``start_response`` 用来表明已经收到一个响应。通过 Werkzeug 你
可以不必直接处理请求或者响应这些底层的东西，它已经为你封装好了这些。

请求数据需要环境对象，Werkzeug 允许你以一个轻松的方式访问数据。响应对象是一个 WSGI
应用，提供了更好的方法来创建响应。

下面教你怎么用响应对象来写一个应用::

    from werkzeug.wrappers import Response
 
     def application(environ, start_response):
        response = Response('Hello World!', mimetype='text/plain')
        return response(environ, start_response)

这里有一个在 URL 中查询字符串的扩展版本(重点是 URL 中的 `name` 将会替代 
``World``)::

    from werkzeug.wrappers import Request, Response

    def applicatio n(environ, start_response):
        request = Request(environ)
        text = 'Hello %s!' % request.args.get('name', 'World')
        response = Response(text, mimetype='text/plain')
        return response(environ, start_response)

到此为止，你已经足够了解 WSGI 了。


Step 1: 创建目录 
----------------------------

在开始之前，首先为应用创建一个目录::

    /shortly
        /static
        /templates

这个简洁的目录不是一个python包，他用来存放我们的项目文件。我们的入口模块将会放在 ``/shortly``
目录的根目录下。 ``/static`` 目录用来放置CSS、Javascript等静态文件，用户可以通过
HTTP协议直接访问。 ``/templates`` 目录用来存放 Jinja2 模板文件，接下来你为项目创
建的模板文件将要放到这个文件夹内。

Step 2: 基本结构
--------------------------

现在我们正式开始为我们的项目创建模块。在 `shortly` 目录创建 `shortly.py` 文件。首先
来导入一些东西。为了防止混淆，我把所有的入口放在这，即使他们不会立即使用::

    import os
    import redis
    import urlparse
    from werkzeug.wrappers import Request, Response
    from werkzeug.routing import Map, Rule
    from werkzeug.exceptions import HTTPException, NotFound
    from werkzeug.wsgi import SharedDataMiddleware
    from werkzeug.utils import redirect
    from jinja2 import Environment, FileSystemLoader

接下来我们来为我们的应用创建基本的结构，并通过一个函数来创建应用实例，通过 WSGI 
中间件输出 `static` 目录的文件::
 
     class Shortly(object):

        def __init__(self, config):
            self.redis = redis.Redis(config['redis_host'], config['redis_port'])

        def dispatch_request(self, request):
            return Response('Hello World!')

        def wsgi_app(self, environ, start_response):
            request = Request(environ)
            response = self.dispatch_request(request)
            return response(environ, start_response) 

        def __call__(self, environ, start_response):
            return self. wsgi_app(environ, start_response)


    def create_app(redis_host='localhost', redis_port=6379, with_static=True):
        app = Shortly({
            'redis_host':       redis_host,
            'redis_port':       redis_port
        })
        if with_static:
            app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
                '/static':  os.path.join(os.path.dirname(__file__), 'static')
            })
        return app

最后我们添加一部分代码来开启一个本地服务器，自动加载代码并开启调试器::

    if __name__ == '__main__':
        from werkzeug.serving import run_simple
        app = create_app()
        run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)

思路很简单，我们的 ``Shortly`` 是一个实际的 WSGI 应用。 ``__call__`` 方法直接调
用 ``wsgi_app`` 。这样做我们可以装饰 ``wsgi_app`` 调用中间件，就像我们在 ``create_app``
函数中做的一样。 ``wsgi_app`` 实际上创建了一个 :class:`Request` 对象,之后通过 
``dispatch_request`` 调用 :class:`Request` 对象然后给 WSGI 应用返回一个 `Response`
对象。正如你看到的：无论是创建 ``Shortly`` 类，还是还是创建 Werkzeug Request 对
象来执行 WSGI 接口。最终结果只是从 ``dispatch_request`` 方法返回另一个 WSGI 应用。

``create_app`` 可以被用于创建一个新的应用实例。他不仅可以通过参数配置应用，还可
以选择性的添加中间件来输出静态文件。通过这种方法我们甚至可以不配置服务器就能访问
静态文件，这对开发是很有帮助的。

插曲: 运行应用程序
-----------------------------------

现在你应该可以通过 `python` 执行这个文件了，看看你本机的服务::

    $ python shortly.py 
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader: stat() polling

它告诉你自动加载已经开启，他会通过各种各样的技术来判断硬盘上的文件是否改变来自动
重启。

在浏览器输入这个URL，你将会看到 “Hello World!”。

Step 3: 环境
-----------------------

现在我们已经有了一个应用的基本类，可以通过构造函数来实现一些功能。通过构造函数我
们可以渲染模板、连接redis。现在让我们扩展这个类::

    def __init__(self, config):
        self.redis = redis.Redis(config['redis_host'], config['redis_port'])
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

Step 4: 路由
-------------------

下一步是路由。我们可以通过路由来匹配和解析URL。Werkzeug 提供了一个灵活的集成路由。
你需要创建一个 :class:`~werkzeug.routing.Map` 实例并添加一系列 :class:`~werkzeug.routing.Rule` 
对象。每个 rule 将会匹配 URL 并添加一个 “endpoint”。endpoint 通常是一个用于标记 
URL 的字符串。此外我们还可以使用它来翻转 URL，但这不是这篇教程我们要做的。

把下列代码放入构造函数::

    self.url_map = Map([
        Rule('/', endpoint='new_url'),
        Rule('/<short_id>', endpoint='follow_short_link'),
        Rule('/<short_id>+', endpoint='short_link_details')
    ])

现在我们创造了一个包含三个 URL 规则的字典。第一个规则， ``/`` 是根 URL 空间，我
们可以调用一个逻辑函数来创建一个新 URL；第二个规则，根据规则指向一个目标URL；最
后一个规则，和第二个有相同的规则，但是它在最后添加一个(``+``)来显示链接链接详细
信息。

那么 endpoint 是怎么指向一个函数的？这是需要你解决的。本篇教程中是通过类中 ``on_``
+ endpoint 方法。具体如下::

     def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e

我们将 RUL 绑定到目前的环境返回一个 :class:`~werkzeug.routing.URLAdapter` 。适配器
可以用于匹配请求也可以翻转 URLS。匹配方法将会返回 endpoint 和一个 URL 值字典。这个
``follow_short_link`` 路由实例有一个变量 ``short_id`` 。当我们在浏览器输入 ``http://localhost:5000/foo``
我们将会得到如下的值::

    endpoint = 'follow_short_link'
    values = {'short_id': u'foo'}

我们没有匹配到任何东西，他将会抛出一个 :exc:`~werkzeug.exceptions.NotFound` 异常，
实质是一个 :exc:`~werkzeug.exceptions.HTTPException` 异常。所有的 HTTP 异常将会跳
转 WSGI 应用渲染的默认错误页面。所以我们只需要捕获并返回他们。

如果一切顺利，我们用 request 作为参数,所有的 URL 参数做作为关键字参数调用 ``on_``
+ endpoint 函数可以返回响应对象。

Step 5: 第一个视图
----------------------

让我们开始第一个视图: new URLs 视图::

    def on_new_url(self, request):
        error = None
        url = ''
        if request.method == 'POST':
            url = request.form['url']
            if not is_valid_url(url):
                error = 'Please enter a valid URL'
            else:
                short_id = self.insert_url(url)
                return redirect('/%s+' % short_id)
        return self.render_template('new_url.html', error=error, url=url)

思想不难理解。首先我们检查请求方法是不是 POST，然后验证得到的 URL 并插入到数据库
中，然后跳转到一个详细页面。要实现这个，意味着我们需要在写一个函数和一个辅助方法
下面是 URL 验证函数::

    def is_valid_url(url):
        parts = urlparse.urlparse(url)
        return parts.scheme in ('http', 'https')

为了向数据库插入 URL，我们只需要在类中添加以下方法::

    def insert_url(self, url):
        short_id = self.redis.get('reverse-url:' + url)
        if short_id is not None:
            return short_id
        url_num = self.redis.incr('last-url-id')
        short_id = base36_encode(url_num)
        self.redis.set('url-target:' + short_id, url)
        self.redis.set('reverse-url:' + url, short_id)
        return short_id

``reverse-url:`` + URL 将会存放储存ID。如果 URL 已经被提交过那么只需要返回存储ID
值，否则我们增加 ``last-url-id`` 键值并转化为 base36，接下来我们将存储连接和转换
连接存储到 redis。下面就是转化为 base 36 的函数::

    def base36_encode(number):
        assert number >= 0, 'positive integer required'
        if number == 0:
            return '0'
        base36 = []
        while number != 0:
            number, i = divmod(number, 36)
            base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
        return ''.join(reversed(base36))

然而我们还没有视图的模板，不急，我们过一会就来写模板。不过在这之前，我们先来完成
另一个视图。

Step 6: 重定向视图
---------------------

重定向视图很简单，它只需要从 redis 找到连接并重定向跳转到它。另外我们还想添加一个
计数器以便于统计连接被点击频率::

    def on_follow_short_link(self, request, short_id):
        link_target = self.redis.get('url-target:' + short_id)
        if link_target is None:
            raise NotFound()
        self.redis.incr('click-count:' + short_id)
        return redirect(link_ta rget)

在这种情况下，如果 URL 不存在，我们将会抛出一个 :exc:`~werkzeug.exceptions.NotFound`
异常，通过 ``dispatch_request`` 函数返回一个 404 响应

Step 7: 描述视图
-------------------

链接描述视图也是非常相似的，我们仅仅需要再渲染一个模板。除了目标 URL，我们还需要
从 redis 查询被点击次数，如果在 redis 中没有记录，我们把它设为 0::

    def on_short_link_details(self, request, short_id):
        link_target = self.redis.get('url-target:' + short_id)
        if link_target is None:
            raise NotFound()
        click_count = int(self.redis.get('click-count:' + short_id) or 0)
        return self.render_template('short_link_details.html',
            link_target=link_target,
            short_id=short_id,
            click_count=click_count
        )

要知道 redis 存的是字符串，所以你需要手动点击次数转化为 :`int` 。

Step 8: 模板
-----------------

这里就是全部的模板，仅仅把它们放到 `templates` 文件夹就可以了。jinja2支持模板继
承，所以我们首先要创建一个 layout 模板，并用 blocks 占位。接下来设置jinja2以便于
自动用html规则转化字符串，我们不必自己花时间来做这些。同时它可以也防止 XSS 攻击和
渲染错误页面。

*layout.html*:

.. sourcecode:: html+jinja

    <!doctype html>
    <title>{% block title %}{% endblock %} | shortly</title>
    <link rel=stylesheet href=/static/style.css type=text/css>
    <div class=box>
      <h1><a href=/>shortly</a></h1>
      <p class=tagline>Shortly is a URL shortener written with Werkzeug
      {% block body %}{% endblock %}
    </div>

*new_url.html*:

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block title %}Create New Short URL{% endblock %}
    {% block body %}
      <h2>Submit URL</h2>
      <form action="" method=post>
        {% if error %}
          <p class=error><strong>Error:</strong> {{ error }}
        {% endif %}
        <p>URL:
          <input type=text name=url value="{{ url }}" class=urlinput>
          <input type=submit value="Shorten">
      </form>
    {% endblock %}

*short_link_details.html*:

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block title %}Details about /{{ short_id }}{% endblock %}
    {% block body %}
      <h2><a href="/{{ short_id }}">/{{ short_id }}</a></h2>
      <dl>
        <dt>Full link
        <dd class=link><div>{{ link_target }}</div>
        <dt>Click count:
        <dd>{{ click_count }}
      </dl>
    {% endblock %}

Step 9: 样式
-----------------

添加样式可以使页面比丑陋的黑色和白色看起来好一些。下面是一个简单的样式表:

.. sourcecode:: css

    body        { background: #E8EFF0; margin: 0; padding: 0; }
    body, input { font-family: 'Helvetica Neue', Arial,
                  sans-serif; font-weight: 300; font-size: 18px; }
    .box        { width: 500px; margin: 60px auto; padding: 20px;
                  background: white; box-shadow: 0 1px 4px #BED1D4;
                  border-radius: 2px; }
    a           { color: #11557C; }
    h1, h2      { margin: 0; color: #11557C; }
    h1 a        { text-decoration: none; }
    h2          { font-weight: normal; font-size: 24px; }
    .tagline    { color: #888; font-style: italic; margin: 0 0 20px 0; }
    .link div   { overflow: auto; font-size: 0.8em; white-space: pre;
                  padding: 4px 10px; margin: 5px 0; background: #E5EAF1; }
    dt          { font-weight: normal; }
    .error      { background: #E8EFF0; padding: 3px 8px; color: #11557C;
                  font-size: 0.9em; border-radius: 2px; }
    .urlinput   { width: 300px; }

Bonus: 改进 
------------------

查看 Werkzeug 仓库的 example 目录可以找到这篇教程代码，那里的版本可能有一些改进，
比如一个定制的 404 页面。

-   `shortly in the example folder <https://github.com/mitsuhiko/werkzeug/blob/master/examples/shortly>`_
