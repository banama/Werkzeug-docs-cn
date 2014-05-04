=========================
在服务器运行 WSGI 应用
=========================

.. module:: serving

这里有一些在服务器运行 WSGI 应用的方式。当你正在开发一个应用，你往往不想在一个成
熟服务器上部署和运行，取而代之的是一个轻量服务器。 Werkzeug 就内置了这样一个轻量
的服务器。

在一个服务器上运行 ``start-myproject.py`` 最简单的方法如下示例::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    from werkzeug.serving import run_simple
    from myproject import make_app

    app = make_app(...)
    run_simple('localhost', 8080, app, use_reloader=True)

你可以添加一个 `extra_files` 关键字参数，一个你想要添加的文件(比如配置文件)列表。


.. autofunction:: run_simple

.. autofunction:: make_ssl_devcert

.. admonition:: Information

   开发服务器不是为了生产环境，它的出现是为了开发方便，在高负载情况下效率是很低
   的。生产环境部署一个应用请看 :ref:`deployment` 页面。

虚拟主机
-------------

一些应用有多个子域名，你需要模拟本地。幸运的是 `hosts file`_ 文件可以给本机分配
多个名字。

这允许你使用 `yourapplication.local` 和 `api.yourapplication.local` (或者其他)代
替 `localhost` 访问本机。

你可以从下面的地方找到 hosts 文件:

    =============== ==============================================
    Windows         ``%SystemRoot%\system32\drivers\etc\hosts``
    Linux / OS X    ``/etc/hosts``
    =============== ==============================================

你可以用你喜欢的文本编辑器打开 hosts 文件，在 `localhost` 后面加上::

    127.0.0.1       localhost yourapplication.local api.yourapplication.local

保存之后你应该就可以通过你添加的主机名字访问开发服务器了。你可以使用
:ref:`routing` 系统调度"两个"主机或自己解析 :attr:`request.host` 。

关闭服务
------------------------

.. versionadded:: 0.7

从 Werkzeug 0.7 版本开始，开发服务器允许在一个请求后关闭服务。目前要求你的Python
版本在 2.6 以上，同时也只能在开发服务器启用。通过在 WSGI 环境调用
``'erkzeug.server.shutdown'`` 来开启 shutdown::

    def shutdown_server(environ):
        if not 'werkzeug.server.shutdown' in environ:
            raise RuntimeError('Not running the development server')
        environ['werkzeug.server.shutdown']()

故障排除
---------------

在一些支持并配置 ipv6 的操作系统，比如 Linux, OS X 10.4 或更高 和 Windows Vista
一些浏览器有时候访问本地服务器很慢，原因有可能是本机被设置为同时支持 ipv4 和
ipv6 套接字，一些浏览器会首先尝试 ipv6 协议。

而目前集成的服务器不能同时支持两种协议。为了更好的可移植性，将会默认支持 ipv4
协议。

注意到解决这个问题有两种方法。如果你不需要ipv6 支持，你可以移除 `hosts file`_ 
文件中的下面一行::

    ::1             localhost

另外你也可以关闭浏览器的 ipv6 支持。比如，在火狐浏览器中你可以进入
``about:config`` 关闭 `network.dns.disableIPv6` 。然后，在 werkzeug 0.6.1中不推
荐这种做法。

从 Werkzeug 0.6.1 开始服务器将不再根据操作系统的配置来转换协议。这意味着如果你的
浏览器关闭 ipv6 支持，而你的操作系统更倾向于 ipv6，你将连接不上服务器。这种情况
下，你可以移除本机 hosts 文件的 ``::1`` 或者明确的用一个 ipv4 协议地址
(`127.0.0.1`)绑定主机名。

.. _hosts file: http://en.wikipedia.org/wiki/Hosts_file

SSL
---

.. versionadded:: 0.6

内置服务器支持测试目的的 SSL，如果提供一个 SSL上下文，他将会被使用，这意味着服
务器可以在 HTTP 或 HTTPS 模式下运行，但不可同时在两种模式下运行。这个功能需要
Python OpenSSL 库。

快速开始
``````````

在werkzeug开发过程中使用 SSL 最简单的方法就是通过 werkzeug 生成一个 SSL 证书和
私钥存起来。对于证书你需要提供生成证书的服务器名或一个 `CN`.

1.  生成一个 SSL 密钥并存放在某个地方:

    >>> from werkzeug.serving import make_ssl_devcert
    >>> make_ssl_devcert('/path/to/the/key', host='localhost')
    ('/path/to/the/key.crt', '/path/to/the/key.key')

2.  现在这个元组会当作 ``ssl_context`` 传入 :func:`run_simple` 方法:

    run_simple('localhost', 4000, application,
               ssl_context=('/path/to/the/key.crt',
                            '/path/to/the/key.key'))

现在当你通过浏览器访问 web 应用的时候将需要验证证书。

手动加载上下文
````````````````````````

你也可以通过代码创建一个上下文代替使用 ``ssl_context`` 元组。这个方法是更好控
制的::


    from OpenSSL import SSL
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.use_privatekey_file('ssl.key')
    ctx.use_certificate_file('ssl.cert')
    run_simple('localhost', 4000, application, ssl_context=ctx)

生成证书
```````````````````````

使用 openssl 工具代替 :func:`make_ssl_devcert` 预先创建一个证书。这要求你的系
统安装 `openssl` 命令行工具::

    $ openssl genrsa 1024 > ssl.key
    $ openssl req -new -x509 -nodes -sha1 -days 365 -key ssl.key > ssl.cert

Adhoc 证书
``````````````````

开启 SSL 最简单的方法就是用 adhoc 模式运行服务。在这个例子中 Werkzeug 将会为你
创建一个证书::

    run_simple('localhost', 4000, application,
               ssl_context='adhoc')

当然这种方法也有缺点，那就是每次重载服务你都需要验证证书。不推荐 Adhoc 证书因
为现在的浏览器因为安全原因对他们支持并不好。
