# dag - directed acyclic graph
# tasks: 1) fetch the data (extract) 2) clean the data (transform) 3) create and store the data in postgres (load)
# operators: PythonOperator, PostgresOperator
# hooks - allow connecction
# dependencies: task A -> task B -> task C

from airflow import DAG
from datetime import datetime, timedelta

from config.scraper_config import RANKINGS_URL, OUTPUT_DIR, EVENT_TYPES
from scraper.scraper import Scraper

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 12, 17),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fetch_and_store_badminton_stats',
    default_args=default_args,
    description='A DAG to fetch and store badminton stats',
    schedule="@daily"
)