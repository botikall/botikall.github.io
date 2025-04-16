# 🔄 Інструкція з оновлення вебсистеми оформлення замовлень кондитерських виробів

## 📋 1. Підготовка до оновлення

1. Повідомити команду про заплановане оновлення.
2. Переконатися, що всі останні зміни пройшли тестування в dev/stage середовищі.
3. Оновити список змін (changelog), якщо він ведеться.
4. Підготувати план відкату (див. нижче).

## 💾 2. Створення резервних копій

1. Створити резервну копію SQLite-бази даних:
   ```bash
   cp db.sqlite3 db_backup_$(date +%F_%T).sqlite3
2. Зберегти копію конфігурацій:
   ```bash
   cp .env .env.backup
3. (Опціонально) Архівувати весь проєкт:
   ```bash
   tar -czvf project_backup_$(date +%F_%T).tar.gz .
 
## ✅ 3. Перевірка сумісності
Перевірити сумісність нових залежностей у requirements.txt:
1. Перевірити сумісність нових залежностей у requirements.txt:
   ```bash
   pip install -r requirements.txt --dry-run
Перевірити, чи не змінився формат бази даних (для SQLite — рідко, але можливо при зміні типів полів).

## 🕒 4. Планування часу простою (якщо потрібно)
SQLite не підтримує одночасну роботу кількох процесів на запис. Тому під час оновлення бажано відключити сайт на 2–5 хвилин.

Встановити сторінку-заглушку або повідомлення користувачам.

## ⚙️ 5. Процес оновлення
1. 🔴Зупинка потрібних служб:
   ```bash
   sudo systemctl stop gunicorn
2. 📦 Розгортання нового коду:
   ```bash
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
3. ⚙️ Оновлення конфігурацій:
   Перевірити .env — чи додано нові змінні

4. Виконайте міграції:
   ```bash
   python manage.py migrate
6. ✅ Перезапуск сервісу:
   ```bash
   python manage.py runserver
## 🔁 6. Процедура відкату (rollback)
У разі помилки:
1. Зупинити Gunicorn:
   ```bash
   sudo systemctl stop gunicorn
2. Відновити попередній стан:
   ```bash
   git reset --hard HEAD@{1}  # або попередній коміт
   cp db_backup_*.sqlite3 db.sqlite3
   cp .env.backup .env
3. Встановити попередні залежності, якщо змінювалися:
   ```bash
   pip install -r requirements.txt

4. Запустити сайт:
   ```bash
   python manage.py runserver
5. Перевірити логи:
   ```bash
   journalctl -u gunicorn
   tail -f logs/nginx/access.log
5. 📌 Примітки
Якщо зміни стосуються лише front-end шаблонів або статики — достатньо виконати collectstatic:
   ```bash
   python manage.py collectstatic --noinput

## ✅ Оновлення завершене! У разі будь-яких збоїв, скористайтесь rollback-інструкцією вище.
