# search_engine

# Usage
## First Run
```
docker-compose up -d postgres
docker exec -i searchengine_postgres_1 psql -U postgres < schema.sql
docker-compose up --build --scale crawler=3 --scale web=3
```
## Later runs
```
docker-compose up --build --scale crawler=3 --scale web=3
```

# Testing
## Performance 
```
docker run -ti --rm --network searchengine_default vitkhab/gobench  -k=true -c 500 -t 10 -u  http://balancer/
```