# =================================================
# STAGE 1: Builder - Установка зависимостей
# =================================================
FROM python:3.12-slim AS builder

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Говорим Poetry, чтобы он не создавал venv, а ставил пакеты в системный site-packages
ENV POETRY_VIRTUALENVS_CREATE=false

# Устанавливаем системные зависимости, необходимые для СБОРКИ пакетов (например, Pillow)
# build-essential нужен для компиляции, -dev пакеты для сборки Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Создаем рабочую директорию
WORKDIR /app

# Копируем только файлы зависимостей для кэширования этого слоя
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости проекта. Poetry установит их в /usr/local/lib/python3.12/site-packages
RUN poetry install --no-interaction --no-ansi --no-root --only main


# =================================================
# STAGE 2: Final - Создание чистого и безопасного образа
# =================================================
FROM python:3.12-slim AS stage-final

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=dicquo.settings

# Устанавливаем только RUNTIME системные зависимости.
# Пакеты -dev и build-essential здесь не нужны.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя без прав root для безопасности
RUN addgroup --system app && adduser --system --ingroup app app

# Создаем рабочую директорию
WORKDIR /home/app/web

# Копируем установленные Python-пакеты из builder-стадии
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Копируем исполняемые файлы (gunicorn, pip и т.д.)
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код проекта и устанавливаем правильного владельца
COPY --chown=app:app . .

# Создаём директорию для конфигов nginx и даём права пользователю app
# Это выполняется ещё от root, поэтому проблем с permissions не будет.
RUN mkdir -p /nginx_configs_host/nginx && chown -R app:app /nginx_configs_host

# Создаём директорию для собранной статики и даём права пользователю app
RUN mkdir -p /home/app/web/staticfiles && chown -R app:app /home/app/web/staticfiles

# Создаём директорию для ошибок (404, 500) и даём права пользователю app
RUN mkdir -p /app/public/media/errors && chown -R app:app /app/public/media

# Переключаемся на пользователя без прав root
USER app


# Собираем статику
# Используем dummy ключ, так как .env файла нет на этапе сборки
RUN SECRET_KEY=dummy python dicquo/manage.py collectstatic --noinput --clear

# Открываем порт
EXPOSE 8000

# Проверка здоровья контейнера
# Docker будет периодически проверять, жив ли контейнер, отправляя GET запрос к главной странице.
# Параметры:
#   --interval=30s    - проверка каждые 30 секунд
#   --timeout=3s      - ожидаем ответ максимум 3 секунды
#   --start-period=10s - даем контейнеру 10 секунд на запуск перед первой проверкой
#   --retries=3       - объявляем контейнер unhealthy после 3 неудачных попыток
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# Переходим в директорию с manage.py для корректного запуска gunicorn
WORKDIR /home/app/web/dicquo

# Команда запуска
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "dicquo.wsgi:application"]