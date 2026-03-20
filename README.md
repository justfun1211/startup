# Proofbot MVP

Production-minded MVP для Telegram-стартапа “Бот-аналитик и промоутер стартап-идей”. Пользователь отправляет идею в бота, backend ставит анализ в Redis-очередь, worker вызывает Polza AI через OpenAI-compatible SDK, сохраняет строго структурированный JSON-отчет, генерирует PDF и уведомляет пользователя в Telegram. Mini App дает историю, просмотр полного отчета, тарифы, реферальный экран и админскую статистику.

## Краткий план реализации

1. Backend foundation: FastAPI, Aiogram, SQLAlchemy async, Alembic, Redis queue, конфиг, health/readiness.
2. Бизнес-модули: users, credits ledger, referrals, analysis runs, payments, broadcasts, PDF.
3. Telegram layer: `/start`, `/help`, `/history`, `/buy`, `/ref`, `/paysupport`, `/admin`, invoice/pre-checkout/successful payment.
4. Worker layer: обработка AI-анализа и рассылок вне основного bot loop.
5. TWA: Dashboard, History, Report Detail, Pricing, Referrals, Admin.
6. Infra: Docker, docker compose, Nginx, README, seed, тесты.

## Финальное дерево проекта

```text
proofbot/
  backend/
    alembic/
    app/
      api/
      bot/
      core/
      db/
      models/
      repositories/
      schemas/
      services/
      templates/
      utils/
      workers/
      main.py
      worker.py
    tests/
    pyproject.toml
    Dockerfile
  webapp/
    src/
    package.json
    Dockerfile
  infra/
    nginx.conf
  docker-compose.yml
  docker-compose.prod.yml
  .env.example
  Makefile
```

## Выбор библиотек и почему

- `FastAPI` — быстрый API слой, удобно для TWA, health endpoints и webhook.
- `Aiogram 3` — современный async Telegram framework с нормальной маршрутизацией и payment hooks.
- `SQLAlchemy 2 async` — типизированный ORM без магии, подходит для модульного монолита.
- `Alembic` — нормальные миграции под PostgreSQL.
- `Redis + ARQ` — легкая asyncio-native очередь для heavy jobs без Celery-overkill.
- `AsyncOpenAI` — совместим с Polza AI через `base_url`, удобно держать fallback model и retry policy.
- `WeasyPrint` — надежная HTML->PDF генерация с русским текстом.
- `React + Vite + Tailwind + TanStack Query + Zustand` — быстрый TWA без тяжеловесного enterprise-стека.

## Архитектурные решения

- Один репозиторий и модульный монолит вместо микросервисов.
- PostgreSQL — source of truth, Redis — очереди, locks и rate-limiting foundation.
- Анализ идеи никогда не исполняется прямо в Telegram handler.
- Кредиты ведутся через `credit_ledger` и быстрый `user_balances`.
- Deep links поддерживаются через `ref_<code>`.
- TWA auth валидируется на backend по Telegram `initData`.
- В локальной разработке выбран `polling`, в production — `webhook`.
- Самый простой надежный сценарий покупки в TWA: пользователь смотрит тарифы в Mini App, а invoice инициирует через `/buy` в чате с ботом.

## Что уже реализовано

- Строгая схема AI-отчета из 5 блоков.
- Хранение истории анализов и PDF.
- Реферальная логика с бонусом новичку и наградой пригласившему после первого успешного анализа.
- Telegram Stars payment flow: intent, pre-checkout, successful payment, idempotent credit grant.
- Admin API: overview, user search, manual grant, broadcast creation/listing.
- Admin broadcasts через фоновые jobs.
- JSON logging, healthz/readyz, seed packs, миграция БД, базовые tests critical path.

## Как запустить локально

1. Скопируйте `.env.example` в `.env`.
2. Заполните минимум:
   - `BOT_TOKEN`
   - `BOT_USERNAME`
   - `POLZA_API_KEY`
   - `ADMIN_TG_IDS`
   - `WEBAPP_URL`
   - `APP_PUBLIC_URL`
3. Поднимите инфраструктуру:

```bash
docker compose up --build
```

4. В отдельном терминале примените миграции:

```bash
docker compose run --rm backend alembic upgrade head
```

5. Засидируйте тарифные пакеты:

```bash
docker compose run --rm backend python -m app.db.seed
```

6. Проверьте:
   - API: [http://localhost:8080/healthz](http://localhost:8080/healthz)
   - TWA dev UI: [http://localhost:3000](http://localhost:3000)
   - Nginx proxy: [http://localhost](http://localhost)

## Как заполнить `.env`

Обязательный минимум для MVP:

- `BOT_TOKEN` — токен бота из BotFather
- `BOT_USERNAME` — username бота без `@`
- `POLZA_API_KEY` — ключ Polza AI
- `DATABASE_URL` — строка подключения к PostgreSQL
- `REDIS_URL` — строка подключения к Redis
- `ADMIN_TG_IDS` — telegram id админов через запятую
- `WEBAPP_URL` — адрес Mini App
- `APP_PUBLIC_URL` — публичный адрес backend

Практичные defaults уже лежат в [.env.example](/D:/Gleb/Documents/antifravity/codex/proofbot/.env.example).

## Docker Compose

Локальный стек поднимает:

- `postgres`
- `redis`
- `backend`
- `worker`
- `webapp`
- `nginx`

Основная команда:

```bash
docker compose up --build
```

## Миграции

```bash
docker compose run --rm backend alembic upgrade head
```

Rollback:

```bash
docker compose run --rm backend alembic downgrade -1
```

## Seed payment packs

```bash
docker compose run --rm backend python -m app.db.seed
```

## Как запустить worker

При `docker compose up` worker поднимается автоматически. Ручной запуск:

```bash
docker compose run --rm worker python -m app.worker
```

## Локальный polling режим

- В `.env` оставьте `BOT_MODE=polling`
- Убедитесь, что webhook у бота выключен или будет перезаписан
- Запускайте `backend` и `worker`

## Production webhook режим

1. Переключите `BOT_MODE=webhook`
2. Заполните:
   - `WEBHOOK_BASE_URL=https://your-domain`
   - `WEBHOOK_SECRET_TOKEN=<strong-secret>`
3. Поднимите стек:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

4. Backend на старте сам выставит webhook на `/webhook/telegram`

## Настройка Main Mini App в BotFather

1. В `BotFather` откройте `Bot Settings`.
2. Настройте `Menu Button` на URL Mini App.
3. Для Main Mini App укажите тот же `WEBAPP_URL`.
4. Убедитесь, что домен публичный и доступен по HTTPS.

## Как тестировать Telegram Stars

1. Засидируйте `payment_packs`.
2. В чате с ботом вызовите `/buy`.
3. Выберите пакет.
4. Бот создаст `invoice_payload` и отправит invoice с `currency = XTR`.
5. После `successful_payment` credits начисляются idempotent образом.

Принятое решение для MVP:
Покупка из TWA не дублирует invoice UI внутри webapp, а ведет пользователя в bot flow `/buy`. Это самый простой и надежный способ не ломать Telegram payment UX.

## Как проверить referral links

1. У пользователя должен быть сгенерирован `referral_code`.
2. Ссылка имеет вид:

```text
https://t.me/<bot_username>?start=ref_<code>
```

3. Новый пользователь стартует по deep link.
4. Invitee получает бонус сразу.
5. Inviter получает бонус после первого успешного анализа invitee.

## Деплой на Ubuntu VM в Yandex Cloud

1. Создайте Ubuntu VM.
2. Установите Docker и Docker Compose plugin.
3. Склонируйте репозиторий и создайте `.env`.
4. Настройте DNS на IP VM.
5. Поднимите стек:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

6. Выполните миграции и seed:

```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm backend python -m app.db.seed
```

7. Подключите TLS через внешний reverse proxy или расширьте Nginx конфиг сертификатами.

## Как смотреть health и логи

Health:

- [http://localhost/healthz](http://localhost/healthz)
- [http://localhost/readyz](http://localhost/readyz)

Логи:

```bash
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f nginx
```

## Тесты

Запуск:

```bash
docker compose run --rm backend pytest
```

Покрыты критические сценарии:

- стартовые бесплатные запросы
- парсинг referral payload
- self-referral protection
- idempotent referral rewards
- debit/refund credits
- idempotent payment crediting
- admin guard
- strict AI schema validation
- базовые integration path для user bootstrap, queueing, completion, payment, TWA auth, PDF ownership

## Что проверить вручную после запуска

1. Новый пользователь делает `/start` и получает 10 запросов.
2. Отправка идеи ставит `analysis_run` в статус `queued`.
3. Worker завершает анализ и присылает summary + PDF.
4. `/buy` отправляет invoice.
5. После оплаты баланс обновляется.
6. `/ref` показывает корректную ссылку.
7. `/admin` доступен только allowlist admin ids.
8. Mini App показывает историю, деталку отчета, тарифы и рефералы.

## Что можно улучшить дальше

- реальный Redis lock на user-specific active analysis и payment idempotency key поверх текущей БД-схемы
- rate limiting middleware для API и bot handlers
- Sentry интеграция через env
- richer admin panel: dry-run preview, target filters, просмотр доставок
- signed short-lived PDF URLs
- более детальная unit economics аналитика и cohort views
