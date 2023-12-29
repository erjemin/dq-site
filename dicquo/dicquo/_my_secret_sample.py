# -*- coding: utf-8 -*-
# ВСЕ СЕКРЕТНЫЕ НАСТРОЙКИ ПРОЕКТА ДЛЯ РАЗРАБОТКИ В ОФИСЕ (под Windows)
"""
В этот файл вынесены все секретные настройки, чтобы не светить их в settings.py
Например, при размещении в публичный репозиториях.
"""

MY_DEBUG = True

# Хосты на которых может работать приложение
MY_ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '10.3.1.***',  # разработка офис
]


# Ключ Django
MY_SECRET_KEY = '**********************************************'

# Настройки для сообщений об ошибках когда все упало и т.п.
MY_ADMINS = (
    ('S.Erjemin', '*******@gmail.com'),
)

#########################################
# настройки для почтового сервера
MY_EMAIL = 'info@***.ru'
MY_EMAIL_FROM = 'info@***.ru'
MY_EMAIL_HOST = 'smtp.mail.ru'             # host разработка домашний
MY_EMAIL_HOST_USER = 'info@***.ru'    # login разработка домашний
MY_EMAIL_HOST_PASSWORD = '****'     # password  разработка домашний
MY_EMAIL_PORT = 2525                       # port разработка домашний
MY_EMAIL_USE_TLS = True

# Настройки подключения к БД MySQL
MY_DATABASE_HOST = '10.3.1.198'          # db-host разработка домашний
MY_DATABASE_NAME = 'django_dq'             # db-name разработка домашний
MY_DATABASE_PORT = '3307'
MY_DATABASE_USER = '***'
MY_DATABASE_PASSWORD = '***'

# дёргаем этот файл, чтобы перегрузить uWSGI
MY_TOUCH_RELOAD = 'M:/PRJ/2023-dq/logs/reload_dq'

# пути к медиа-файлам и статике
MY_MEDIA_ROOT = 'M:/PRJ/2023-dq/public/media'
MY_STATIC_ROOT = 'M:/PRJ/2023-dq/public/static/'
