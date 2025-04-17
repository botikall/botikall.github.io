# Лінтинг у проєкті "Вебсистема оформлення замовлень кондитерських виробів"

## Обрані інструменти

- **flake8** — основний лінтер для Python
- **black** — форматування коду згідно з PEP8
- **isort** — впорядковує імпорти

Ці інструменти були обрані через їхню популярність, гнучкість та підтримку Python/Django.

---

## Основні правила лінтингу

- Довжина рядка — до 88 символів
- Всі імпорти мають бути впорядковані
- Відступи — 4 пробіли
- Не використовуються зайві пробіли та порожні рядки
- Код повинен бути автоматично форматований за допомогою `black`

---

## Інструкція з запуску

1. Встановіть інструменти:
    ```bash
    pip install flake8 black isort
    ```
2. Створення та налаштування нових файлів .flake8, pyproject.toml та isort.cfg:
    ```bash
    [flake8] # .flake8
    max-line-length = 88
    exclude =
      .git,
      __pycache__,
      env,
      venv,
      migrations,
      static,
      media
    ignore = E203, W503

    [tool.black] # pyproject.toml
    line-length = 88
    exclude = '''
    /(
      \.git
      | \.venv
      | env
      | venv
      | migrations
      | static
      | media
    )/
    '''
    
    [settings] # isort.cfg
    profile = black
    ```
3. Запуск перевірки:
    ```bash
    flake8 .
    ```
 4. Автоформатування:
    ```bash
    black .
    isort .
    ```   
---

## Ігноровані файли/папки

- `migrations/` — автогенеровані Django файли
- `env/`, `venv/` — віртуальне середовище
- `media/`, `static/` — файли користувачів та ресурсів
