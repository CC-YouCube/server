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
ifeq ($(OS), Windows_NT)
	del /s /q src\data src\__pycache__
else
	rm src/data src/__pycache__ -Rv || true
endif

install-pylint:
	pip install pylint

install-pyspelling:
	pip install pyspelling
