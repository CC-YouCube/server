#!make

run:
	python src/youcube

docker-build:
	docker build -t youcube:latest src/.

pylint:
	pylint src/youcube/*.py

pyspelling:
	pyspelling

cleanup:
	rm src/data src/__pycache__ -Rv || true

install-pylint:
	pip install pylint

install-pyspelling:
	pip install pyspelling
