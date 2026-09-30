.PHONY: setup dev test test-backend test-frontend build docker-up docker-down create-user

setup:
	python -m venv .venv
	.venv/Scripts/pip install -r backend/requirements.txt
	cd frontend && npm install

dev-backend:
	$env:PYTHONPATH="backend"; .venv/Scripts/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test-backend:
	$env:PYTHONPATH="backend"; .venv/Scripts/pytest backend/tests

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down -v

create-user:
	$env:PYTHONPATH="backend"; .venv/Scripts/python -m app.cli create-user $(AGENCY_ID)
