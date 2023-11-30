# Foodgram

## Описание

Фудграм — сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Запуск проекта на удаленном сервере

Для запуска проекта на удаленном сервере используется workflow для GitHub Actions

Форкните данный репозиторий, перейдите в настройки репозитория — Settings, выберите на панели слева Secrets and Variables → Actions

Необходимо создать переменные:

```
DOCKER_USERNAME - ваш логин DockerHub
DOCKER_PASSWORD - ваш пароль DockerHub
SSH_KEY - SSH ключ вашего удаленного сервера
SSH_PASSPHRASE - пароль вашего удаленного сервера
HOST - IP-адрес вашего удаленного сервера
USER - логин вашего удаленного сервера
TELEGRAM_TO - ID вашего телеграм-аккаунта
TELEGRAM_TOKEN - токен вашего бота в Telegram
```

Подключитесь к вашему удаленному серверу и создайте директорию foodgram/ в домашней директории сервера

Создайте файл .env в директории foodgram/, внесите в него необходимые значения:

```
POSTGRES_DB=название вашей БД
POSTGRES_USER=имя пользователя БД
POSTGRES_PASSWORD=пароль пользователя БД
DB_HOST=db
DB_PORT=порт, по умолчанию 5432

SECRET_KEY='ваш секретный ключ'
DEBUG=False
ALLOWED_HOSTS='127.0.0.1 localhost'
```

Установите Nginx - [инструкция](https://github.com/Seleznev808/infra_sprint1)

В файле конфигурации Nginx пропишите:

```
server {
        server_name ваше_доменное_имя;
	    server_tokens off;

        location / {
            proxy_pass http://127.0.0.1:8080;
        }
}
```

Получите и настройте SSL-сертификат - [инструкция](https://github.com/Seleznev808/infra_sprint1)

В файле main.yml директории .github/workflows/ измените название образов

```
seleznev808/kittygram_gateway:latest → ваш_логин_DockerHub/kittygram_gateway:latest
```

Для деплоя на сервер достаточно запушить коммит на GitHub:

```
git add .
```
```
git commit -m "ваш коммит"
```
```
git push
```

После отправки изменений зайдите в свой репозиторий проекта на GitHub и откройте раздел Actions. В нем вы увидите выполнение workflow (он назван именем вашего последнего коммита). После успешного деплоя в ваш телеграм придет сообщение от бота:

```
Деплой успешно выполнен!
```

После деплоя необходимо подключиться к удаленному серверу, перейти в директорию foodgram/ и добавить ингредиенты для рецептов в базу:

```
sudo docker compose -f docker-compose.yml exec backend python manage.py loaddata db.json
```

При необходимости вы можете сделать свой дамп базы данных - скрипт для внесения данных в базу из csv файла лежит в папке data. После заполнения базы выполните:

```
python -Xutf8 manage.py dumpdata recipes.ingredient recipes.tag --indent 2 > db.json
```

это создаст дамп таблиц ingredient и tag из приложения recipes

## Технологии

```
Django 3.2.16
Django REST framework 3.14
Djoser 2.2
PostgreSQL
Docker
Nginx
React
```

## Автор

[Селезнев Василий](https://github.com/Seleznev808/)
