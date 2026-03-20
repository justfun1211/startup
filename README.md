# Proofbot MVP

Production-minded MVP Telegram-сервиса для анализа стартап-идей. Пользователь отправляет идею в бота или Mini App, backend ставит задачу в Redis-очередь, worker запрашивает Polza AI, сохраняет структурированный отчет, собирает PDF и отправляет результат в Telegram.

## Стек

- Backend: Python 3.12, FastAPI, Aiogram 3, SQLAlchemy 2 async, Alembic, Redis, ARQ, PostgreSQL
- Frontend: React, TypeScript, Vite, Tailwind, TanStack Query, Zustand
- Infra: Docker, Docker Compose, Nginx
- PDF: WeasyPrint
- AI: Polza AI через OpenAI-compatible API

## Структура

```text
proofbot/
  backend/
  webapp/
  infra/
  docker-compose.yml
  docker-compose.prod.yml
  .env.example
  Makefile
  README.md
```

## Что уже умеет MVP

- `/start`, `/help`, `/history`, `/buy`, `/ref`, `/paysupport`, `/admin`
- deep link рефералы `ref_<code>`
- AI-анализ с жесткой 5-блочной JSON-структурой
- история отчетов и просмотр PDF в Mini App
- покупка пакетов за Telegram Stars
- админка: overview, поиск пользователя, ручная выдача, рассылки, журнал действий

## Локальный запуск

1. Создайте `.env`:

```bash
cp .env.example .env
```

На Windows:

```powershell
copy .env.example .env
```

2. Заполните минимум:

- `BOT_TOKEN`
- `BOT_USERNAME`
- `POLZA_API_KEY`
- `ADMIN_TG_IDS`

3. Поднимите стек:

```bash
docker compose up --build
```

4. Примените миграции:

```bash
docker compose run --rm backend alembic upgrade head
```

5. Засидируйте тарифы:

```bash
docker compose run --rm backend python -m app.db.seed
```

6. Проверьте сервисы:

- API: [http://localhost:8080/healthz](http://localhost:8080/healthz)
- Web app dev: [http://localhost:3000](http://localhost:3000)
- Nginx proxy: [http://localhost](http://localhost)

## Важные переменные окружения

- `BOT_MODE=polling` для локальной разработки
- `BOT_MODE=webhook` для production
- `APP_PUBLIC_URL` в production должен указывать на публичный домен приложения
- `WEBAPP_URL` в production должен быть публичным HTTPS URL Mini App
- `VITE_API_URL` можно оставить пустым для production behind nginx

Практичный шаблон лежит в [.env.example](/D:/Gleb/Documents/antifravity/codex/proofbot/.env.example).

## Telegram Mini App локально

Telegram Mini App требует HTTPS. Для локальной ручной проверки удобно использовать один туннель на `80` порт:

```bash
ngrok http 80
```

Дальше используйте один и тот же публичный URL:

- `WEBAPP_URL=https://<your-ngrok-domain>`
- `APP_PUBLIC_URL=https://<your-ngrok-domain>`

## Покупки через Telegram Stars

В Mini App пользователь нажимает покупку пакета, backend отправляет `invoice` в чат с ботом, пользователь оплачивает Stars в Telegram, после `successful_payment` credits начисляются на баланс.

Для MVP выбран самый надежный сценарий:

- выбор пакета в Mini App
- оплата в диалоге с ботом
- Mini App автоматически подтягивает новый баланс после успешной оплаты

## Проверка рефералов

1. Откройте `/ref`
2. Возьмите ссылку формата:

```text
https://t.me/<bot_username>?start=ref_<code>
```

3. Новый пользователь должен открыть бота по этой ссылке и нажать `/start`
4. Бонус начисляется ему и пригласившему сразу после старта

## Production deploy на Ubuntu VM

1. Подготовьте Ubuntu VM
2. Установите Docker и Docker Compose plugin
3. Настройте DNS на IP VM
4. Склонируйте репозиторий
5. Создайте `.env`
6. Переключите:

- `BOT_MODE=webhook`
- `WEBHOOK_BASE_URL=https://your-domain`
- `WEBHOOK_SECRET_TOKEN=<strong-secret>`
- `APP_PUBLIC_URL=https://your-domain`
- `WEBAPP_URL=https://your-domain`

7. Поднимите production stack:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

8. Примените миграции и seed:

```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm backend python -m app.db.seed
```

9. Настройте TLS

Текущий `nginx.conf` слушает `80`. Для production нужен внешний TLS:

- либо отдельный reverse proxy перед VM
- либо расширение `infra/nginx.conf` и подключение сертификатов

## Production checklist для Ubuntu VM

### Инфраструктура

- Домен указывает на IP VM
- Открыты порты `80` и `443`
- Docker и Compose установлены
- На диске хватает места для PDF и Docker layers

### Конфиг

- `.env` создан на сервере
- `BOT_TOKEN` задан
- `POLZA_API_KEY` задан
- `BOT_MODE=webhook`
- `WEBHOOK_BASE_URL` корректный и с HTTPS
- `WEBHOOK_SECRET_TOKEN` непустой
- `ADMIN_TG_IDS` заполнен
- `WEBAPP_URL` указывает на тот же публичный HTTPS домен
- `APP_PUBLIC_URL` указывает на публичный домен

### Запуск

- `docker compose -f docker-compose.prod.yml up --build -d` отработал без ошибок
- миграции применены
- seed выполнен
- `backend`, `worker`, `postgres`, `redis`, `webapp`, `nginx` в статусе `Up`

### Проверка после деплоя

- `GET /healthz` отвечает
- `GET /readyz` отвечает
- `/start` в боте работает
- новый анализ ставится в очередь
- worker завершает анализ
- PDF открывается
- пакет `10 XTR` покупается
- баланс обновляется после оплаты
- реферальная ссылка работает
- `/admin` доступен только админам
- Mini App открывается из Telegram без ошибок auth

### Логи

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f worker
docker compose -f docker-compose.prod.yml logs -f nginx
```

## Полезные команды

```bash
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.db.seed
docker compose run --rm backend pytest
docker compose logs -f backend
```

## Что улучшать дальше

- HTTPS прямо в `nginx` с certbot или внешним LB
- более детальная админка по доставкам рассылок
- фильтры для broadcasts
- Sentry через env
- signed short-lived links для PDF
- richer unit-economics dashboard
