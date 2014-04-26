=========
安装
=========

Werkzeug 要求 Python 2.6 以上版本。如果你需要支持 Pyhthon <2.6 版本可以下载老
版本的 Werkzeug (强烈推荐 Pyhton 2.6 以上版本)。Werkzeug目前已经支持 Python 3
。更多信息请看 :ref:`python3`.


安装一个发行版
=================

安装一个egg包 (通过 easy_install 或 pip)
------------------------------------------

你可以安装最新的 Werkzeug 版本通过 `easy_install`_::

    easy_install Werkzeug

另外你也可以使用pip::

    pip install Werkzeug

我们强烈推荐结合 :ref:`virtualenv` 使用这些工具。

这将会在 `site-packages` 目录安装一个 Werkzeug egg 包。

从压缩包安装
-------------------------

1.  从 `download page`_ 下载最新的压缩包。
2.  解压压缩包。
3.  执行 ``python setup.py install`` 命令。

注意如果你没有安装 `setuptools`_  执行最后一条命令将会自动下载和安装。这需要联
网。

以上命令会将 Werkzeug 安装到 `site-packages` 文件夹。


安装开发版
==================================

1.  安装 `Git`_
2.  ``git clone git://github.com/mitsuhiko/werkzeug.git``
3.  ``cd werkzeug``
4.  ``pip install --editable``

.. _virtualenv:

virtualenv
===============

Virtualenv 大概会是你想在开发环境下使用的软件。如果你有shell权限访问生产环境，
你可能也会喜欢他。         

virtualenv 解决了什么问题？如果你像我一样喜欢Python，你很可能会在基于 Werkzeug
的 Web 应用之外使用Python。但是随着项目越来越多，你使用不同版本python的可能性越
大，至少你有可能会用到支持不同Pytohn版本的库。我们不得不面对一种很常见的情况就
是库是不向后兼容的，或者很少有应用没有依赖包。所以当然有两个甚至更多项目的时候
你打算怎么解决依赖冲突？

Virtualenv 正是为此而生！它允许你安装多个Python版本, 每个项目对应自己的Python。
他其实并没有安装一个Python副本，而是通过很奇妙的方法来保持环境独立。

下面让我门看看 virtualenv 是怎么工作的！

如果你使用 Mac OS X 或 Linux, 这里有两种安装方法供你选择::

    $ sudo easy_install virtualenv

或者更好的方法::

    $ sudo pip install virtualenv

你可以通过上述命令在你的系统安装 virtualenv 。你甚至可以使用包管理器安装，如果
你使用Ubuntu，可以尝试::

    $ sudo apt-get install python-virtualenv

如果你是用Windows，没有 `easy_install` 命令，你必须首先安装它。一旦安装成功，
执行相同的命令，但是不需要带 `sudo` 前缀。

一旦成功安装 virtualenv，打开 shell 创建你自己的环境。我经常会创建一个 myproje
ct 文件夹，并在其中创建 `env` 文件夹::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv env
    New python executable in env/bin/python
    Installing setuptools............done.

现在，无论何时只要你想在某个项目上工作，只需激活相应环境。在 OS X 和 Linux，按
如下操作::

    $ . env/bin/activate

(注意 `.` 和脚本名称之间的空格。 `.` 意味着这个脚本在当前shell下运行。如果这个命令
在你的命令行无效, 尝试用 ``source`` 代替 `.`)

如果你是个 Windows 用户，可以使用以下命令::

    $ env\scripts\activate

无论哪种方式，现在你已经可以使用 virtualenv 了(观察shell中切换到的Virtualenv提
示)。

 安装Werkzeug ::

    $ pip install Werkzeug

几秒钟后你就可以使用werkzeug了。

.. _download page: https://pypi.python.org/pypi/Werkzeug
.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _Git: http://git-scm.org/
