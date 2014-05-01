.. _python3:

==============
Python 3 Notes
==============

这部分文档特别要求使用 Werkzeug 和 WSGI 的环境为 Python 3。

.. warning::

   Werkzeug 的 Python 3 支持目前只是实验性的。所以有问题欢迎反馈以帮助我们来
   改善它。


WSGI 环境
================

Python 3 的 WSGI 环境和 Python 2 有一点不同。如果你使用高级的 API，Werkzeug
会帮你隐藏这些区别的大部分。Python 2 和 Pyhton 3 最主要的区别是 Python 2 的
WSGI 环境包含字节，而 Python 3 包含一系列不同的编码字符串。

在 Python 3 有两种不同类型的 WSGI 环境:

-   unicode 字符串限制到 latin1 值。他们经常用于 HTTP headers 信息和其他一些
    地方。
-   unicode 字符串携带二进制数据，通过 latin1 值来回传递。这在 Werkzeug 通常
    被成为 “WSGI encoding dance” 。

Werkzeug 给你提供一些函数自动解决这些问题。所以你不需要关心内部的实现。下面 
的函数和类可以用来读取 WSGI 环境信息:

-   :func:`~werkzeug.wsgi.get_current_url`
-   :func:`~werkzeug.wsgi.get_host`
-   :func:`~werkzeug.wsgi.get_script_name`
-   :func:`~werkzeug.wsgi.get_path_info`
-   :func:`~werkzeug.wsgi.get_query_string`
-   :func:`~werkzeug.datastructures.EnvironHeaders`

不推荐在 Python 3 中创造和修改 WSGI 环境除非确保能够正确解码。在 Werkzeug 中
所有高级 API 接口能正确实现编码和解码。

URLs
====

在 Python 3 中 Werkzeug 的 URL 为 unicode 字符串。所有的解析函数一般会提供操
作字节码功能。在某些情况，URLs 处理函数允许字符集不改变返回一个字节对象。在
内部 Werkzeug 正尽可能统一 URIs 和 IRIs。

清理 Request
===============

Python 3 和 PyPy 在上传文件时，需要确保关闭 Request 对象。这要妥善关闭由多重
解析创建的临时文件。你可以使用 ``close()`` 方法。

除了请求对象还有上下文管理需要关闭，但是上下文管理可以自动关闭。
