up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.db.seed

worker:
	docker compose run --rm worker python -m app.worker

tests:
	docker compose run --rm backend pytest
