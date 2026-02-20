# ==========================================
# Dockerfile для Django + Gunicorn + WhiteNoise
# ==========================================

# 1. Базовый образ: Python 3.12 (Slim версия для меньшего размера)
FROM python:3.12-slim

# 2. Переменные окружения для Python
# PYTHONDONTWRITEBYTECODE: Запрещает Python писать .pyc файлы
# PYTHONUNBUFFERED:        Гарантирует, что вывод консоли (logs) виден сразу (не буферизуется)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Poetry настройки: не создавать виртуальное окружение внутри контейнера (ставим системно).
# Дублирует `poetry config virtualenvs.create false` в пп.7 (на всякий случай).
ENV POETRY_VIRTUALENVS_CREATE=false
# Путь настройки Django (по умолчанию для production) на случай если контейнер будет запущен не через docker-compose.
ENV DJANGO_SETTINGS_MODULE=dicquo.settings

# 3. Рабочая директория внутри контейнера
WORKDIR /app

# 4. Установка системных зависимостей
# - libjpeg-dev zlib1g-dev: библиотеки для работы с изображениями (Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Установка Poetry через pip (быстро и надежно)
RUN pip install --no-cache-dir poetry

# 6. Копируем файлы зависимостей (pyproject.toml и poetry.lock)
# Делаем это ДО копирования всего кода, чтобы использовать кэш Docker layers.
COPY pyproject.toml poetry.lock /app/

# 7. Установка зависимостей проекта
# --no-interaction: не будет спрашивать подтверждения
# --no-ansi: уберваем цветные символы из логов сборки (они иногда мусорят)
# --no-root: не устанавливать сам проект как пакет (мы просто копируем код)
# --only main: не ставить dev-зависимости (тесты, линтеры и т.п.) для продакшена
# RUN poetry install --no-root --only main
# Настройка Poetry: не создавать venv и установка зависимостей (без dev-зависимостей для продакшена)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# 8. Копируем весь исходный код проекта в контейнер
COPY . /app/

# 9. Сборка статики (CSS, JS)
# Важно: Запускаем collectstatic с фейковым SECRET_KEY, так как на этапе сборки env файла может не быть.
RUN SECRET_KEY=dummy_build_key python dicquo/manage.py collectstatic --noinput --clear

# 10. Открываем порт 8000
EXPOSE 8000

# 11. Команда запуска
# Переходим в подпапку dicquo, где лежит код Django проекта
WORKDIR /app/dicquo

# Запускаем Gunicorn (по умолчанию, если не переопределено в docker-compose) на три воркера, привязывая его к
# порту 8000 и указывая на точку входа приложения (wsgi.py).
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "dicquo.wsgi:application"]

