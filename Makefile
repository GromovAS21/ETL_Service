typecheck:
	mypy src/ --explicit-package-bases

format:
	ruff check src/ --fix
	ruff check src/ --select I --fix

lint:
	ruff check src/
	ruff check src/ --select I
