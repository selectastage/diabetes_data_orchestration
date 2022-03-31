import datetime
from client import ClinicalTrials
import pandas as pd
ct = ClinicalTrials()
import airflow
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator


DAG = DAG(
    dag_id='results_dag',
    start_date = datetime.datetime.now(),
    schedule_interval="@daily" 
    )


def api_call(**context):
    ct = ClinicalTrials()
    diabetes_fields = ct.get_study_fields(
        search_expr= "Diabetes",
        fields=[
        "NCTId", 
        "Condition", 
        "EnrollmentCount",
        "InterventionName", "PrimaryOutcomeMeasure","OverallStatus"],
        max_studies=500,
        fmt="csv",)
    task_instance = context['task_instance']
    task_instance.xcom_push(key="diabetes_fields", value=diabetes_fields)
    

fetch_csv_fields = PythonOperator(
    task_id='fetch_csv_fields',
    python_callable=api_call,
    provide_context=True,
    dag=DAG)


def read_data(**kwargs):
    ti = kwargs['ti']
    fields = ti.xcom_pull(task_ids='fetch_csv_fields', key='diabetes_fields')
    df = pd.DataFrame.from_records(fields[1:], columns=fields[0])


pull_data = PythonOperator(
    task_id='pull_data',
    python_callable=read_data,
    provide_context=True,
    dag=DAG)





fetch_csv_fields >> pull_data
