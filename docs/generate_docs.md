# Генерація документації

## Підготовка

1. Встановити залежності:
    ```bash
    pip install sphinx
    pip install sphinx-autodoc-typehints
2. Генерація документації:
     ```bash
     sphinx-quickstart docs

3. Обираємо такі налаштування:
    ```bash
    > Separate source and build directories (y/n) [n]: y
    > Project name: Order Website
    > Author name(s): [ім’я]
    > Project release []: 1.0
4. Налаштовуєм docs/source/conf.py:
    ```bash
    import os
    import sys
    import django

    sys.path.insert(0, os.path.abspath('../..')) 
    os.environ['DJANGO_SETTINGS_MODULE'] = 'bakery_order_system.settings'
    django.setup()
5. Налаштовуєм docs/source/index.rst:
    ```bash
    .. toctree::
   :maxdepth: 2
   :caption: Зміст:

   modules
    .. automodule:: orders.models
   :members:
   :undoc-members:
   :show-inheritance:
    .. automodule:: orders.views
   :members:
   :undoc-members:
6. Перевіряєм/пишемо коментарі.
7. Запускаєм процес генерації документації:
    ```bash
    cd docs
    make html  # .\make.bat html - windows
Генерація проведена успішно
