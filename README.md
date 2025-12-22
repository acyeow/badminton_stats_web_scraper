# Python Scraper for Scraping Badminton Stats

## Quickstart

### Create a venv

```
python3 -m venv venv python=3.10.12
```

### Activate the venv
```
source venv/bin/activate
```

### Install requirements

```
pip install -r requirements.txt
```

### Setup Airflow

```
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### Initialize the database

```
docker compose up airflow-init
```

### Run Airflow

```
docker compose up
```

### Login to Airflow

At localhost:8080 we can login to airflow with:

```
user: airflow  
password: airflow  
```

### Login to Postgres

At localhost:5050 we can login to postgres with: 

``` 
user: admin@admin.com
password: root

### Create a new server on Postgres

Connection:

```
user: airflow
password: airflow
```

Get the postgres container id:

```
docker container ls
docker inspect <container_id>
```
Copy the IP Address and paste in the connection information as the host, then create the connection.

