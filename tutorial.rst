=================
Werkzeug 教程
=================

.. module:: werkzeug

欢迎来到 Werkzeug 教程，我们将会实现一个类似 `TinyURL`_ 的网站来储存 URLS。我们
将会使用的库有模板引擎 `Jinja`_ 2，数据层支持 `redis`_ ，当然还有 WSGI 协议层Werkzeug。

你可以使用 `pip` 来安装依赖库::

    pip install Jinja2 redis

同时确定你的本地有一个 redis 服务，如果你是OS X系统，你可以使用 `brew` 来安装它::

    brew install redis

如果你是用 Ubuntu 或 Debian, 你可以使用 apt-get::

    sudo apt-get install redis

Redis 为 UNIX 系统开发，并没有考虑为 Windows 设计。对于开发来说，非官方的版本已
经足够了，你可以从 `github <https://github.com/dmajkic/redis/downloads>`_ 得到它。

简短介绍
-------------------

在这个教程中，我们将一起用 Werkzeug 创建一个短网址服务。请注意，Werkzeug 并不是
一个框架，它是一个带着一些工具集的库，你可以通过它来创建你自己的框架或 Web 应用
。Werkzeug 是非常灵活的，这篇教程用到的一些方法只是 Werkzeug 的一部分。

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
可以不必直接处理请求或者响应这些底层的东西，它已经封装好了这些。

请求数据需要环境对象，他允许你以一个轻松的方式访问数据。响应对象是一个 WSGI 应
用，提供了更好的方法来创建响应。

下面教你怎么用响应对象来写一个应用::

    from werkzeug.wrappers import Response
 
     def application(environ, start_response):
        response = Response('Hello World!', mimetype='text/plain')
        return response(environ, start_response)

这里有一个好象是在 URL 中查询字符串的扩展版本(重点是 URL 中的 `name` 将会替代 
``World``)::

    from werkzeug.wrappers import Request, Response

    def application(environ, start_response):
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

Step 3: The Environment
-----------------------

Now that we have the basic application class, we can make the constructor
do something useful and provide a few helpers on there that can come in
handy.  We will need to be able to render templates and connect to redis,
so let's extend the class a bit::

    def __init__(self, config):
        self.redis = redis.Redis(config['redis_host'], config['redis_port'])
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

Step 4: The Routing
-------------------

Next up is routing.  Routing is the process of matching and parsing the URL to
something we can use.  Werkzeug provides a flexible integrated routing
system which we can use for that.  The way it works is that you create a
:class:`~werkzeug.routing.Map` instance and add a bunch of
:class:`~werkzeug.routing.Rule` objects.  Each rule has a pattern it will
try to match the URL against and an “endpoint”.  The endpoint is typically
a string and can be used to uniquely identify the URL.  We could also use
this to automatically reverse the URL, but that's not what we will do in this
tutorial.

Just put this into the constructor::

    self.url_map = Map([
        Rule('/', endpoint='new_url'),
        Rule('/<short_id>', endpoint='follow_short_link'),
        Rule('/<short_id>+', endpoint='short_link_details')
    ])

Here we create a URL map with three rules.  ``/`` for the root of the URL
space where we will just dispatch to a function that implements the logic
to create a new URL.  And then one that follows the short link to the
target URL and another one with the same rule but a plus (``+``) at the
end to show the link details.

So how do we find our way from the endpoint to a function?  That's up to you.
The way we will do it in this tutorial is by calling the method ``on_``
+ endpoint on the class itself.  Here is how this works::

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e

We bind the URL map to the current environment and get back a
:class:`~werkzeug.routing.URLAdapter`.  The adapter can be used to match
the request but also to reverse URLs.  The match method will return the
endpoint and a dictionary of values in the URL.  For instance the rule for
``follow_short_link`` has a variable part called ``short_id``.  When we go
to ``http://localhost:5000/foo`` we will get the following values back::

    endpoint = 'follow_short_link'
    values = {'short_id': u'foo'}

If it does not match anything, it will raise a
:exc:`~werkzeug.exceptions.NotFound` exception, which is an
:exc:`~werkzeug.exceptions.HTTPException`.  All HTTP exceptions are also
WSGI applications by themselves which render a default error page.  So we
just catch all of them down and return the error itself.

If all works well, we call the function ``on_`` + endpoint and pass it the
request as argument as well as all the URL arguments as keyword arguments
and return the response object that method returns.

Step 5: The First View
----------------------

Let's start with the first view: the one for new URLs::

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

This logic should be easy to understand.  Basically we are checking that
the request method is POST, in which case we validate the URL and add a
new entry to the database, then redirect to the detail page.  This means
we need to write a function and a helper method.  For URL validation this
is good enough::

    def is_valid_url(url):
        parts = urlparse.urlparse(url)
        return parts.scheme in ('http', 'https')

For inserting the URL, all we need is this little method on our class::

    def insert_url(self, url):
        short_id = self.redis.get('reverse-url:' + url)
        if short_id is not None:
            return short_id
        url_num = self.redis.incr('last-url-id')
        short_id = base36_encode(url_num)
        self.redis.set('url-target:' + short_id, url)
        self.redis.set('reverse-url:' + url, short_id)
        return short_id

``reverse-url:`` + the URL will store the short id.  If the URL was
already submitted this won't be None and we can just return that value
which will be the short ID.  Otherwise we increment the ``last-url-id``
key and convert it to base36.  Then we store the link and the reverse
entry in redis.  And here the function to convert to base 36::

    def base36_encode(number):
        assert number >= 0, 'positive integer required'
        if number == 0:
            return '0'
        base36 = []
        while number != 0:
            number, i = divmod(number, 36)
            base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
        return ''.join(reversed(base36))

So what is missing for this view to work is the template.  We will create
this later, let's first also write the other views and then do the
templates in one go.

Step 6: Redirect View
---------------------

The redirect view is easy.  All it has to do is to look for the link in
redis and redirect to it.  Additionally we will also increment a counter
so that we know how often a link was clicked::

    def on_follow_short_link(self, request, short_id):
        link_target = self.redis.get('url-target:' + short_id)
        if link_target is None:
            raise NotFound()
        self.redis.incr('click-count:' + short_id)
        return redirect(link_target)

In this case we will raise a :exc:`~werkzeug.exceptions.NotFound` exception
by hand if the URL does not exist, which will bubble up to the
``dispatch_request`` function and be converted into a default 404
response.

Step 7: Detail View
-------------------

The link detail view is very similar, we just render a template
again.  In addition to looking up the target, we also ask redis for the
number of times the link was clicked and let it default to zero if such
a key does not yet exist::

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

Please be aware that redis always works with strings, so you have to convert
the click count to :class:`int` by hand.

Step 8: Templates
-----------------

And here are all the templates.  Just drop them into the `templates`
folder.  Jinja2 supports template inheritance, so the first thing we will
do is create a layout template with blocks that act as placeholders.  We
also set up Jinja2 so that it automatically escapes strings with HTML
rules, so we don't have to spend time on that ourselves.  This prevents
XSS attacks and rendering errors.

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

Step 9: The Style
-----------------

For this to look better than ugly black and white, here a simple
stylesheet that goes along:

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

Bonus: Refinements
------------------

Look at the implementation in the example dictionary in the Werkzeug
repository to see a version of this tutorial with some small refinements
such as a custom 404 page.

-   `shortly in the example folder <https://github.com/mitsuhiko/werkzeug/blob/master/examples/shortly>`_
