from datetime import datetime
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.bash import BashOperator      # Airflow 3 import

DBT = "/opt/airflow/dbt_venv/bin/dbt"
DBT_PROJECT = "/opt/airflow/dbt/swiggy"

COPY_RAW = [
    "USE WAREHOUSE SWIGGY_WH",
    "COPY INTO SWIGGY.RAW.restaurants FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/restaurants/  ON_ERROR='CONTINUE'",
    "COPY INTO SWIGGY.RAW.users       FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/users/        ON_ERROR='CONTINUE'",
    "COPY INTO SWIGGY.RAW.food        FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/food/         ON_ERROR='CONTINUE'",
    "COPY INTO SWIGGY.RAW.menu        FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/menu/         ON_ERROR='CONTINUE'",
    "COPY INTO SWIGGY.RAW.orders      FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/orders/",
    "COPY INTO SWIGGY.RAW.order_items FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/order_items/",
    "COPY INTO SWIGGY.RAW.reviews     FROM @SWIGGY.RAW.SWIGGY_RAW_STAGE/reviews/",
]

with DAG(
    dag_id="swiggy_batch",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["swiggy", "dbt", "snowflake"],
    doc_md=__doc__,
) as dag:

    reload_raw = SQLExecuteQueryOperator(
        task_id="reload_raw", conn_id="snowflake_default",
        sql=COPY_RAW, split_statements=True, autocommit=True,
    )

    dbt_build_core = BashOperator(
        task_id="dbt_build_core",
        bash_command=f"{DBT} build --exclude tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
    )

    enrich_reviews = BashOperator(
        task_id="enrich_reviews",
        bash_command=f"python /opt/airflow/ai/enrich_reviews.py",
    )

    dbt_build_ai = BashOperator(
        task_id = "dbt_build_ai",
        bash_command=f"{DBT} build --select tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}"
    )

    reload_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai