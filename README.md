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
## Unit testing and coverage
```
pip install -r requirements-crawler.txt -r requirements-web.txt -r requirements-test.txt
PYTHONPATH=. coverage run -m unittest discover -s tests/ 
coverage report --include crawler.py,search.py
```
## Performance 
```
docker run -ti --rm vitkhab/gobench -k=true -c 500 -t 10 -u  http://35.190.15.45/?query=search
```