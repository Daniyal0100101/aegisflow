.PHONY: install run-api run-web docker-build docker-up docker-down test clean

# Help command displaying all scripts
help:
	@echo "AegisFlow Make Workflow Console:"
	@echo "  make install        - Install python dependencies & frontend node modules"
	@echo "  make run-api        - Start local FastAPI backend (port 8000)"
	@echo "  make run-web        - Start local Next.js frontend dev server (port 3000)"
	@echo "  make docker-build   - Compile docker images for web and api"
	@echo "  make docker-up      - Launch multi-container services via docker-compose"
	@echo "  make docker-down    - Terminate docker-compose active container structures"
	@echo "  make test           - Run automated verification testing suites"
	@echo "  make clean          - Purge local temporary caches, pycaches, etc."

install:
	pip install -r apps/api/requirements.txt
	cd apps/web && npm install

run-api:
	python apps/api/main.py

run-web:
	cd apps/web && npm run dev

docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down

test:
	python -m unittest discover -s packages -p "*_test.py"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
