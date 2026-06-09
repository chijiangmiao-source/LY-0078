from setuptools import setup, find_packages

setup(
    name='breakfast_management',
    version='1.0',
    description='民宿早餐备餐时段与餐篮配送管理系统',
    author='Breakfast Management Team',
    packages=find_packages(),
    include_package_data=True,
    package_data={'breakfast_management': ['i18n/*/LC_MESSAGES/*.mo']},
    install_requires=[
        "TurboGears2 >= 2.4.0",
        "SQLObject >= 3.9.0",
        "Genshi >= 0.7.7",
        "tgext.admin >= 0.7.2",
        "tgext.crud >= 0.8.1",
        "tw2.forms",
        "mysqlclient",
    ],
    entry_points={
        'paste.app_factory': [
            'main = breakfast_management.config.middleware:make_app',
        ],
    },
)
