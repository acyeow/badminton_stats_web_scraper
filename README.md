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
user: airflow  
password: airflow  

### Login to Postgres
At localhost:5432 we can login to postgres with:  
user: admin@admin.com
password: root
