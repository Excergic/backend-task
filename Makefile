.PHONY: dev db-up db-down test lint db-check

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

db-up:
	docker-compose up -d postgres

db-down:
	docker-compose down

db-check:
	@echo "=== Database Status ==="
	@docker exec -it backend-task-postgres-1 psql -U postgres -d stories_db -c "SELECT 'users' as table, COUNT(*) FROM users UNION ALL SELECT 'stories', COUNT(*) FROM stories UNION ALL SELECT 'follows', COUNT(*) FROM follows;"

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check app/
