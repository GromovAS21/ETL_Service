# Техническое задание: ELT-сервис для аналитики

## Цель

Реализовать сервис ELT, который будет перекачивать данные из мастер БД (M) в целевую аналитическую БД (A) с частотой раз в 5 минут.

---

## Состав и компоненты

- **Мастер БД (M)**: PostgreSQL, которая выступает источником данных.
    
- **Целевая БД (A)**: PostgreSQL, куда загружаются обработанные данные.
    
- **Redis**: хранилище состояния (хеши от данных, время обновлений).
    
- **ELT-кор**: основной сервис на Python, который обрабатывает файлы из специальной папки `jobs`. Формат файлов абсолютно любой. Один файл в этой папке - один ETL процесс.

---

## Как это работает

1. Аналитик добавляет файл в папку `/jobs`. Это должен быть YAML файл. В нем:
    
    - `CREATE_TABLE_SQL`: сырой SQL-запрос на создание таблицы
        
    - `SELECT_SOURCE_SQL`: запрос к БД M
        
    - `UPSERT_TARGET_SQL`: insert/update запрос к БД A
        
    - `SELECT_KEYS_SQL`: сырой SQL запрос для получения ключей в таблице, чтобы отсеять удаленные.
		
	- `TARGET_TABLE`: Имя созданной таблицы
		
	- `KEY_COLUMNS`: Колонка (или сочетания колонок), по которым нужно сравнить таблицы.
	

2. Каждые 5 минут запускается обновление:
    
    - Поиск новых файлов в папке `/jobs`.
        
    - Выполнение `CREATE_TABLE_SQL` (при необходимости).
        
    - Выполнение `SELECT_SOURCE_SQL`, сравнение с хранящимися хэшами в Redis.
        
    - Если есть изменения — `UPSERT_TARGET_SQL`.
        
3. При удалении записей из БД M, они должны исчезать из A. Для этого проводить сравнение по `KEY COLUMNS`.
    

---
### Логирование:

- Ошибки в `.log`-fайлы.
- Логирование критичных случаев.
___

### Правило написания запросов

1. Для **CREATE_TABLE_SQL**

- Запрос на создание таблицы необходимо начинать с `CREATE TABLE IF NOT EXISTS ` - это нужно для того чтобы не было конфликта при новом цикле работы приложения'. 

2. Для **SELECT_SOURCE_SQL**

- В конце SELECT запроса должно быть обязательно условие с placeholder\`ом (пример: `WHERE updated_at > %s`) для сравнения поля обновления с последней датой работы ETL процесса (храниться в хэше). Выгружает данные которые были обновлены или добавлены после последней даты работы ETL процесса. 

3. Для UPSERT_TARGET_SQL

- Запрос INSERT должен иметь `ON CONFLICT (col_name) DO UPDATE SET col_name_1 = EXCLUDED.title` - если объект существует то он обновляется, если нет то создается. 
- Запрос должен перечислять все поля объекта
- Внутри оператора VALUES должно быть равное колонкам объекта количество placeholder

_Пример: INSERT INTO products (product_id, title, created_at, updated_at) VALUES (%s, %s, %s, %s) ON CONFLICT (product_id) DO UPDATE SET title = EXCLUDED.title, created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at;_

4. Для SELECT_KEYS_SQL и KEY_COLUMNS

- В `KEY_COLUMNS` хранится список с названиями полей по которым будет производиться удаление. Может быть одно может быть несколько.
- В `SELECT_KEYS_SQL` должен быть SELECT запрос на получения всех объектов из основной таблицы
- В `SELECT_KEYS_SQL` запрос должен быть на колонки которые прописаны в `KEY_COLUMNS`. Количество и названия и порядок их прописывания должен быть одинаковый. 

_Пример:_
- SELECT_KEYS_SQL = "SELECT title, category FROM products;"
- KEY_COLUMNS = ["title", "category"]


Тестовые примеры данных в файле:

{
  "CREATE_TABLE_SQL": "CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, name VARCHAR, email VARCHAR, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);",
  "SELECT_SOURCE_SQL": "SELECT id, name, email, created_at, updated_at FROM users WHERE updated_at > %s;",
  "UPSERT_TARGET_SQL": "INSERT INTO users (id, name, email, created_at, updated_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email, created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at;",
  "SELECT_KEYS_SQL": "SELECT id FROM users;",
  "TARGET_TABLE": "users",
  "KEY_COLUMNS": ["id"]
}

{
  "CREATE_TABLE_SQL": "CREATE TABLE IF NOT EXISTS products (product_id INT PRIMARY KEY, title VARCHAR NOT NULL, price DECIMAL(10,2), category VARCHAR, stock_quantity INT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);",
  "SELECT_SOURCE_SQL": "SELECT product_id, title, price, category, stock_quantity, created_at, updated_at FROM products WHERE updated_at > %s;",
  "UPSERT_TARGET_SQL": "INSERT INTO products (product_id, title, price, category, stock_quantity, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (product_id) DO UPDATE SET title = EXCLUDED.title, price = EXCLUDED.price, category = EXCLUDED.category, stock_quantity = EXCLUDED.stock_quantity, created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at;",
  "SELECT_KEYS_SQL": "SELECT title, category FROM products;",
  "TARGET_TABLE": "products",
  "KEY_COLUMNS": ["title", "category"]
  }