.PHONY: run worker test lint

run:
	PYTHONPATH=src python3 -m orderflow.api

worker:
	PYTHONPATH=src python3 -m orderflow.worker

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

lint:
	python3 -m compileall -q src tests
