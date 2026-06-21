.PHONY: install dev test lint run clean docker docker-up docker-down

# ──────────────────────────────────────────────
# Install
# ──────────────────────────────────────────────
install:
	pip install -e .

dev:
	pip install -e ".[dev,qrcode]"

# ──────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────
test:
	python3 -m pytest tests/ -v --tb=short

test-fast:
	python3 -m pytest tests/ -v --tb=short -x

test-warn:
	python3 -m pytest tests/ -v --tb=short -W error

coverage:
	python3 -m pytest tests/ --cov=src --cov-report=term-missing

# ──────────────────────────────────────────────
# Lint
# ──────────────────────────────────────────────
lint:
	ruff check src/ tests/

lint-fix:
	ruff check --fix src/ tests/

format:
	ruff format src/ tests/

# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
run:
	python3 -m src.main

cli:
	python3 cli.py

status:
	python3 cli.py status

init:
	python3 cli.py init

health:
	python3 cli.py health

# ──────────────────────────────────────────────
# Clean
# ──────────────────────────────────────────────
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	rm -rf src/__pycache__ src/**/__pycache__
	rm -rf tests/__pycache__ tests/.pytest_cache
	rm -rf *.egg-info dist build
	rm -rf logs/

# ──────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────
docker:
	docker build -t telegram-board-system .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ──────────────────────────────────────────────
# Systemd
# ──────────────────────────────────────────────
install-service:
	sudo cp systemd/telegram-board.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable telegram-board
	sudo systemctl start telegram-board

uninstall-service:
	sudo systemctl stop telegram-board
	sudo systemctl disable telegram-board
	sudo rm /etc/systemd/system/telegram-board.service
	sudo systemctl daemon-reload
