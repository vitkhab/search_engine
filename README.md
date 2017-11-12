# search_engine

# Usage
## First Run
```
docker-compose up -d postgres
docker exec -i searchengine_postgres_1 psql -U postgres < schema.sql
docker-compose up --build --scale crawler=3
```
## Later runs
```
docker-compose up --build --scale crawler=3
```