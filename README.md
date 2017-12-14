# search_engine

# Usage
## Prerequisite
```
docker-compose up -d postgres
docker exec -i searchengine_postgres_1 psql -U postgres < schema.sql
```
Or in kubernetes
```
kubectl exec -i <postgres-pod-name> -- psql -U postgres < schema.sql
```
## Run
```
docker-compose build
docker-compose up -d --scale web=3 postgres rabbit balancer web
docker-compose up --scale crawler=3 crawler
```

# Testing
## Performance 
```
docker run -ti --rm vitkhab/gobench -k=true -c 500 -t 10 -u  http://35.190.15.45/?query=search
```