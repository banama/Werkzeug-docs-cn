过渡到 Werkzeug 1.0
==========================

Werkzeug 原本有一个神奇的导入系统钩子，如果启用它则可以从一个模块导入所有东西而且
还可以根据实际需要选择性加载。不幸的是，这种方法被证明是效率低下的，用它来代替Pyt
hon实现和GAE是不可靠的。

从 0.7 开始我们不推荐短入口，强烈鼓励从一个实际实现的模块来导入。Werkzeug 1.0 将完
全不支持这种神奇的导入钩子。

因为手动去发现那么实际的函数被导入并重写他们是一个痛苦和乏味的过程，所以我们写
了一个工具来帮助过渡。

自动重写入口
-------------------------------

举个例子， Werkzeug < 0.7 版本推荐的方法是使用 `escape`  函数，用法如下::

    from werkzeug import escape

Werkzeug 0.7 版本推荐的方法是直接从工具包导入 `escape`  函数(1.0 版本这个方
法将会变成强制性的)。为了自动重写所有的入口你可以使用 `werkzeug-import-rewri
te <http://bit.ly/import-rewrite>`_ script。

你可以通过 Python 和 Werkzeug 基础代码的文件夹列表来执行它。它将会输出一个 hg/git 
兼容的补丁文件。如下::

    $ python werkzeug-import-rewrite.py . > new-imports.udiff

通过下列方法应用补丁文件:

hg:

    ::

        hg import new-imports.udiff

git:

    ::

        git apply new-imports.udiff

patch:

    ::

        patch -p1 < new-imports.udiff

停止使用废弃的东西
----------------------------

Werkzeug 上的一些东西将停止更新，我们强烈建议替换掉即使他们短时间内还可以使用。

不要使用:

-   `werkzeug.script` ，用 `argparse` 或其他相似的工具定制脚本替换它。
-   `werkzeug.template`, 用一个适当的模板引擎替换它。
-   `werkzeug.contrib.jsrouting` ，停止使用Javascript URL 生成器，它与许多公共公
    共路由的扩展性不是很好。
-   `werkzeug.contrib.kickstart` ，取代手写代码，实际上 Werkzeug API 变得越来越
    好，他不再是必需的。
-   `werkzeug.contrib.testtools` ，已经不是那么有用了。
