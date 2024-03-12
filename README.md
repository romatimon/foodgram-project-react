### Foodgram - сайт 'Продуктовый помощник'

### Опиание проекта
«Продуктовый помощник»: приложение, на котором пользователи публикуют свои рецепты, добавляют в избранное и подписываться на публикации других авторов.
Сервис «Список покупок» позволяет пользователям создавать свой список продуктов, которые необходимо купить для приготовления блюд по выбранным рецептам.

#### В проекте используются технологии:
- Python
- Django
- Django REST Framework
- Docker
- Nginx
- PostgreSQL
- Gunicorn

### Проект доступен по ссылке:
 - https://fdgm.ddns.net/

### Инструкция по запуску:
***- Клонировать репозиторий:***
```
git clone git@github.com:romatimon/foodgram-project-react.git
```
В директории foodgram-project-react/infra создайте файл .env и наполните его по следющему шаблону:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<ваш пароль для базы данных>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<ваш секретный ключ для django проекта>
```

### Команды для запуска приложения в Docker-контейнерах:

Перейти в директорию:
```
cd foodgram-project-react/
```
Запустить контейнеры:

```
sudo docker-compose up -d
```

Выполнить миграции:

```
sudo docker-compose exec web python manage.py migrate
```
Создать суперпользователя:

```
sudo docker-compose exec web python manage.py createsuperuser
```

Собрать статику:

```
sudo docker-compose exec python manage.py collectstatic
```

Наполнить базу данными ингредиентами:
```
sudo docker-compose exec python manage.py load_base ingredients.csv
```
Автор [romatimon](https://github.com/romatimon)
