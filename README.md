# search_engine

# Usage
```
docker-compose up --build
docker exec -i searchengine_postgres_1 psql -U postgres < schema.sql
docker exec -ti searchengine_search_engine_1 python crawler.py https://example.com
```