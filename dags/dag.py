# dag - directed acyclic graph
# tasks: 1) fetch the data (extract) 2) clean the data (transform) 3) create and store the data in postgres (load)
# operators: PythonOperator, PostgresOperator
# hooks - allow connecction
# dependencies: task A -> task B -> task C

import datetime
import pendulum
import os

import requests
from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

@dag(
    dag_id="process_badminton_stats",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2025, 12, 17, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)

def ProcessBadmintonStats():
    create_badminton_stats_table = SQLExecuteQueryOperator(
        task_id='create_badminton_stats_table',
        conn_id='pg_conn',
        sql="""
            CREATE TABLE IF NOT EXISTS badminton_stats (
                "Rank" INT,
                "Player Name" VARCHAR(255) PRIMARY KEY,
                "Country" VARCHAR(255),
                "Points" INT,
                "Tournaments" INT,
                "Last Update" DATE,
                "Rank Change" VARCHAR(255)
            );
        """
    )

    create_badminton_stats_temp_table = SQLExecuteQueryOperator(
        task_id='create_badminton_stats_temp_table',
        conn_id='pg_conn',
        sql="""
            DROP TABLE IF EXISTS badminton_stats_temp;
            CREATE TABLE IF NOT EXISTS badminton_stats_temp (
                "Rank" INT,
                "Player Name" VARCHAR(255) PRIMARY KEY,
                "Country" VARCHAR(255),
                "Points" INT,
                "Tournaments" INT,
                "Last Update" DATE,
                "Rank Change" VARCHAR(255)
            );
        """
    )

    @task
    def get_data():
        data_path = "/opt/airflow/ranking_data/mens_single_rankings_2025-12-22.csv"
        os.makedirs(os.path.dirname(data_path), exist_ok=True)

        url = "https://raw.githubusercontent.com/acyeow/badminton_stats_web_scraper/refs/heads/main/ranking_data/mens_single_rankings_2025-12-22.csv"

        response = requests.request("GET", url)

        with open(data_path, "w") as file:
            file.write(response.text)

        postgres_hook = PostgresHook(postgres_conn_id='pg_conn')
        conn = postgres_hook.get_conn()
        cur = conn.cursor()
        with open(data_path, 'r') as file:
            cur.copy_expert(
                "COPY badminton_stats_temp FROM STDIN WITH CSV HEADER DELIMITER AS ',' QUOTE '\"'",
                file
            )
        conn.commit()

    @task
    def merge_data():
        query = """
            INSERT INTO badminton_stats
            SELECT *
            FROM (
                SELECT DISTINCT *
                FROM badminton_stats_temp
            ) t
            ON CONFLICT ("Player Name") DO UPDATE
            SET
                "Rank" = EXCLUDED."Rank",
                "Country" = EXCLUDED."Country",
                "Points" = EXCLUDED."Points",
                "Tournaments" = EXCLUDED."Tournaments",
                "Last Update" = EXCLUDED."Last Update",
                "Rank Change" = EXCLUDED."Rank Change"
        """
        try:
            postgres_hook = PostgresHook(postgres_conn_id='pg_conn')
            conn = postgres_hook.get_conn()
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            return 0
        except Exception as e:
            return 1
    [create_badminton_stats_table, create_badminton_stats_temp_table] >> get_data() >> merge_data()

dag = ProcessBadmintonStats()