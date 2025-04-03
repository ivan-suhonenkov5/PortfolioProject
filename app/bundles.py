import os

from flask_assets import Bundle

from .functions import recursive_flatten_iterator


def get_bundle(route, tpl, ext, paths, type=False):
    """
    Функция возвращает нужный Bundle (css/js) для регистрации в главном файле приложения.
    Содержит пути до локальных исходников css/js-файлов, сгруппированных друг с другом по использованию в шаблонах html.
    ------------------------------------------------------------
    1-й параметр route - название роута
    2-й параметр tpl - название шаблона html из папки /templates
    3-й параметр ext - расширение (css/js)
    4-й параметр paths(массив) - все пути к исходникам
    -------------------------------------------------------------
    5-й параметр type (опциональный) - используется только для JS.
    !!!Важно!!! Если нужен главный файл "main.js", параметр не указывать!
    Если нужен скрипт длительной загрузки "defer.js", передать булево значение True
    """
    if route and tpl and ext:
        return {
            'instance': Bundle(*paths, output=get_path(route, tpl, ext, type), filters=get_filter(ext)),
            'name': get_filename(route, tpl, ext, type),
            'dir': os.getcwd()
        }


def register_bundle(assets, bundle):
    assets.register(bundle['name'], bundle['instance'])
    return f" Bundle {bundle['name']} registered successfully!"


def register_bundles(assets, bundles):
    for x in recursive_flatten_iterator(bundles):
        for bundle in x:
            register_bundle(assets, bundle)


def get_filename(route, tpl, ext, type):
    if type:
        return f"{route}_{tpl}_{ext}_defer"
    else:
        return f"{route}_{tpl}_{ext}"


def get_path(route, tpl, ext, type):
    if type:
        return f"gen/{route}/{tpl}/defer.{ext}"
    else:
        return f"gen/{route}/{tpl}/main.{ext}"


def get_filter(ext):
    return f"{ext}min"


bundles = {
    "post": {
        "all": {
            "css": [get_bundle('post', 'all', 'css', ['css/blocks/table.css', 'css/libs/font-awesome.min.css'])],
            "js": [get_bundle('post', 'all', 'js', ['js/blocks/js1.js', 'js/blocks/js2.js', 'js/blocks/js3.js'])]
        },
        "create": {},
        "update": {},
    },
    "user": {
        "login": {},
        "register": {},
    },
}