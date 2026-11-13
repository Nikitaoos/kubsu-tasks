.PHONY: install install-dev test run docker-build docker-test

install:
	pip install .

install-dev:
	pip install ".[test]"

test:
	pytest tests

run:
	uvicorn src.main:app --reload

docker-build:
	docker build --target runtime -t kubsu-users .

docker-test:
	docker build --target test -t kubsu-users-test .
	docker run --rm --network host kubsu-users-test
