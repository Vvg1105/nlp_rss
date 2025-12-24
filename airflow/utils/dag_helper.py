"""
Helper functions for the Airflow DAGs
"""

import json
import os
import sys
from airflow.exceptions import AirflowFailException
from airflow.models import Variable
import logging
logger = logging.getLogger(__name__)


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def task_failure_alert(context):
    """
    Send an alert when a task fails.
    """
    task_id = (
        context.get('task_instance').task_id if context.get('task_instance') 
        else 'unknown task'
    )
    dag_id = context.get('dag').dag_id if context.get('dag') else 'unknown dag'
    exception = context.get('exception')
    logger.error(f"Task {task_id} in DAG {dag_id} failed with exception: {exception}")

def check_agent_response(response):
    """
    Ensure 200 and no application-level error in JSON body.
    """
    if response.status_code != 200:
        return False
    
    # Try to inspect JSON payload for error fields
    try:
        payload = response.json()
    except Exception:
        # If not JSON, still treat 200 as success
        return True
    
    if isinstance(payload, dict):
        status = str(payload.get('status', '')).lower()
        if status in {"error", "failure", "invalid", "failed"}:
            raise AirflowFailException(f"Agent returned failure status: {status}. Response: {payload}")
        if payload.get('error'):
            raise AirflowFailException(f"Agent returned error: {payload['error']}. Response: {payload}")
    return True

def get_injection_id(**context):
    """
    Get the injection ID from the task context.
    """
    dag_run = context.get('dag_run')
    if dag_run and dag_run.conf:
        return dag_run.conf.get("injection_ID", "default")
    return "default"

def increment_pipeline_id(**context):
    """
    Increment the persistent pipeline_current_id after a successful cycle.
    """
    current_id = int(Variable.get("pipeline_current_id", default_var=0))
    next_id = current_id + 1
    Variable.set("pipeline_current_id", str(next_id))
    logger.info(f"Incremented pipeline_current_id: {current_id} -> {next_id}")
    return next_id

