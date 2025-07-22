typecheck:
	mypy etl_service/src/ --explicit-package-bases

format:
	ruff check etl_service/src/ --fix
	ruff check etl_service/src/ --select I --fix

lint:
	ruff check etl_service/src/
	ruff check etl_service/src/ --select I

run:
	docker compose build && docker compose up