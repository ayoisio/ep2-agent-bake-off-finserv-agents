# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This file contains the tools used by the database agent."""

import datetime
import logging
import os
import re

import numpy as np
import pandas as pd
from ...utils.utils import get_env_var
from google.adk.tools import ToolContext
from google.cloud import bigquery
from google.genai import Client

from .chase_sql import chase_constants

# Assume that `BQ_COMPUTE_PROJECT_ID` and `BQ_DATA_PROJECT_ID` are set in the
# environment. See the `data_agent` README for more details.
data_project = os.getenv("BQ_DATA_PROJECT_ID", None)
compute_project = os.getenv("BQ_COMPUTE_PROJECT_ID", None)
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT", None)
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Lazy initialization of LLM client to avoid credential issues at import time
_llm_client = None

def get_llm_client():
    """Get the LLM client, initializing it if needed."""
    global _llm_client
    if _llm_client is None:
        _llm_client = Client(vertexai=True, project=vertex_project, location=location)
    return _llm_client

MAX_NUM_ROWS = 80


def _serialize_value_for_sql(value):
    """Serializes a Python value from a pandas DataFrame into a BigQuery SQL literal."""
    if pd.isna(value):
        return "NULL"
    if isinstance(value, str):
        # WORKAROUND: Perform replacement before f-string to avoid backslash in expression.
        escaped_value = value.replace('\\', '\\\\')
        return f"'''{escaped_value}'''"
    if isinstance(value, bytes):
        # WORKAROUND: Perform replacement before f-string to avoid backslash in expression.
        decoded_and_escaped_value = value.decode('utf-8', 'replace').replace('\\', '\\\\')
        return f"b'''{decoded_and_escaped_value}'''"
    if isinstance(value, (datetime.datetime, datetime.date, pd.Timestamp)):
        return f"'{value}'"
    if isinstance(value, (list, np.ndarray)):
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if isinstance(value, dict):
        return f"({', '.join(_serialize_value_for_sql(v) for v in value.values())})"
    return str(value)

database_settings = None
bq_client = None


def get_bq_client():
    """Get BigQuery client."""
    global bq_client
    if bq_client is None:
        bq_client = bigquery.Client(
            project=get_env_var("BQ_COMPUTE_PROJECT_ID"))
    return bq_client


def get_database_settings():
    """Get database settings."""
    global database_settings
    if database_settings is None:
        database_settings = update_database_settings()
    return database_settings


def update_database_settings():
    """Update database settings."""
    global database_settings
    ddl_schema = get_bigquery_schema(
        dataset_id=get_env_var("BQ_DATASET_ID"),
        data_project_id=get_env_var("BQ_DATA_PROJECT_ID"),
        client=get_bq_client(),
        compute_project_id=get_env_var("BQ_COMPUTE_PROJECT_ID")
    )
    database_settings = {
        "bq_data_project_id": get_env_var("BQ_DATA_PROJECT_ID"),
        "bq_dataset_id": get_env_var("BQ_DATASET_ID"),
        "bq_ddl_schema": ddl_schema,
        # Include ChaseSQL-specific constants.
        **chase_constants.chase_sql_constants_dict,
    }
    return database_settings


def get_bigquery_schema(dataset_id,
                        data_project_id,
                        client=None,
                        compute_project_id=None):
    """Retrieves schema and generates DDL with example values for a BigQuery dataset.

    Args:
        dataset_id (str): The ID of the BigQuery dataset (e.g., 'my_dataset').
        data_project_id (str): Project used for BQ data.
        client (bigquery.Client): A BigQuery client.
        compute_project_id (str): Project used for BQ compute.

    Returns:
        str: A string containing the generated DDL statements.
    """

    if client is None:
        client = bigquery.Client(project=compute_project_id)

    dataset_ref = bigquery.DatasetReference(data_project_id, dataset_id)

    ddl_statements = ""

    info_schema_query = f"""
        SELECT table_name
        FROM `{data_project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
    """
    query_job = client.query(info_schema_query)

    for table_row in query_job.result():
        table_ref = dataset_ref.table(table_row.table_name)
        table_obj = client.get_table(table_ref)

        if table_obj.table_type == "VIEW":
            view_query = table_obj.view_query
            ddl_statements += f"CREATE OR REPLACE VIEW `{table_ref}` AS\n{view_query};\n\n"
            continue
        elif table_obj.table_type == "EXTERNAL":
            # (External table logic remains unchanged as it did not have the issue)
            if (
                table_obj.external_data_configuration
                and table_obj.external_data_configuration.source_format
                == "ICEBERG"
            ):
                config = table_obj.external_data_configuration
                uris_list_str = ",\n    ".join([f"'{uri}'" for uri in config.source_uris])
                column_defs = []
                for field in table_obj.schema:
                    col_type = field.field_type
                    if field.mode == "REPEATED":
                        col_type = f"ARRAY<{col_type}>"
                    column_defs.append(f"  `{field.name}` {col_type}")
                columns_str = ",\n".join(column_defs)

                ddl_statements += f"""CREATE EXTERNAL TABLE `{table_ref}` (
{columns_str}
)
WITH CONNECTION `{config.connection_id}`
OPTIONS (
  uris = [{uris_list_str}],
  format = 'ICEBERG'
);\n\n"""
            continue
        elif table_obj.table_type == "TABLE":
            column_defs = []
            for field in table_obj.schema:
                col_type = field.field_type
                if field.mode == "REPEATED":
                    col_type = f"ARRAY<{col_type}>"
                col_def = f"  `{field.name}` {col_type}"
                if field.description:
                    escaped_description = field.description.replace('\\', '\\\\')
                    col_def += f" OPTIONS(description='''{escaped_description}''')"
                column_defs.append(col_def)

            # --- IMPROVED AND CORRECTED DDL STATEMENT CREATION ---
            # 1. Join the column definitions into a single string first.
            #    This is clearer and avoids complex operations inside the f-string.
            columns_ddl_string = ",\n".join(column_defs)

            # 2. Use a simple, readable multiline f-string to build the final statement.
            ddl_statement = f"""CREATE OR REPLACE TABLE `{table_ref}` (
{columns_ddl_string}
);

"""
            # --- END OF IMPROVEMENT ---

            try:
                sample_query = f"SELECT * FROM `{table_ref}` LIMIT 5"
                rows = client.query(sample_query).to_dataframe()

                if not rows.empty:
                    ddl_statement += f"-- Example values for table `{table_ref}`:\n"
                    for _, row in rows.iterrows():
                        values_str = ", ".join(
                            _serialize_value_for_sql(v) for v in row.values
                        )
                        ddl_statement += f"INSERT INTO `{table_ref}` VALUES ({values_str});\n\n"
            except Exception as e:
                logging.warning(
                    f"Could not retrieve sample rows for table {table_ref.path}: {e}"
                )
                ddl_statement += f"-- NOTE: Could not retrieve sample rows for table {table_ref.path}.\n\n"

            ddl_statements += ddl_statement
        else:
            continue

    return ddl_statements


def initial_bq_nl2sql(
    question: str,
    tool_context: ToolContext,
) -> str:
    """Generates an initial SQL query from a natural language question.

    Args:
        question (str): Natural language question.
        tool_context (ToolContext): The tool context to use for generating the SQL
          query.

    Returns:
        str: An SQL statement to answer this question.
    """

    prompt_template = """
You are a BigQuery SQL expert tasked with answering user's questions about BigQuery tables by generating SQL queries in the GoogleSql dialect.  Your task is to write a Bigquery SQL query that answers the following question while using the provided context.

**Guidelines:**

- **Table Referencing:** Always use the full table name with the database prefix in the SQL statement.  Tables should be referred to using a fully qualified name with enclosed in backticks (`) e.g. `project_name.dataset_name.table_name`.  Table names are case sensitive.
- **Joins:** Join as few tables as possible. When joining tables, ensure all join columns are the same data type. Analyze the database and the table schema provided to understand the relationships between columns and tables.
- **Aggregations:**  Use all non-aggregated columns from the `SELECT` statement in the `GROUP BY` clause.
- **SQL Syntax:** Return syntactically and semantically correct SQL for BigQuery with proper relation mapping (i.e., project_id, owner, table, and column relation). Use SQL `AS` statement to assign a new name temporarily to a table column or even a table wherever needed. Always enclose subqueries and union queries in parentheses.
- **Column Usage:** Use *ONLY* the column names (column_name) mentioned in the Table Schema. Do *NOT* use any other column names. Associate `column_name` mentioned in the Table Schema only to the `table_name` specified under Table Schema.
- **FILTERS:** You should write query effectively  to reduce and minimize the total rows to be returned. For example, you can use filters (like `WHERE`, `HAVING`, etc. (like 'COUNT', 'SUM', etc.) in the SQL query.
- **LIMIT ROWS:**  The maximum number of rows returned should be less than {MAX_NUM_ROWS}.

**Schema:**

The database structure is defined by the following table schemas (possibly with sample rows):

```
{SCHEMA}
```

**Natural language question:**

```
{QUESTION}
```

**Think Step-by-Step:** Carefully consider the schema, question, guidelines, and best practices outlined above to generate the correct BigQuery SQL.

   """

    ddl_schema = tool_context.state["database_settings"]["bq_ddl_schema"]

    prompt = prompt_template.format(
        MAX_NUM_ROWS=MAX_NUM_ROWS, SCHEMA=ddl_schema, QUESTION=question
    )

    response = get_llm_client().models.generate_content(
        model=os.getenv("BASELINE_NL2SQL_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config={"temperature": 0.1},
    )

    sql = response.text
    if sql:
        sql = sql.replace("```sql", "").replace("```", "").strip()

    print("\n sql:", sql)

    tool_context.state["sql_query"] = sql

    return sql


def run_bigquery_validation(
    sql_string: str,
    tool_context: ToolContext,
) -> str:
    """Validates BigQuery SQL syntax and functionality.

    This function validates the provided SQL string by attempting to execute it
    against BigQuery in dry-run mode. It performs the following checks:

    1. **SQL Cleanup:**  Preprocesses the SQL string using a `cleanup_sql`
    function
    2. **DML/DDL Restriction:**  Rejects any SQL queries containing DML or DDL
       statements (e.g., UPDATE, DELETE, INSERT, CREATE, ALTER) to ensure
       read-only operations.
    3. **Syntax and Execution:** Sends the cleaned SQL to BigQuery for validation.
       If the query is syntactically correct and executable, it retrieves the
       results.
    4. **Result Analysis:**  Checks if the query produced any results. If so, it
       formats the first few rows of the result set for inspection.

    Args:
        sql_string (str): The SQL query string to validate.
        tool_context (ToolContext): The tool context to use for validation.

    Returns:
        str: A message indicating the validation outcome. This includes:
             - "Valid SQL. Results: ..." if the query is valid and returns data.
             - "Valid SQL. Query executed successfully (no results)." if the query
                is valid but returns no data.
             - "Invalid SQL: ..." if the query is invalid, along with the error
                message from BigQuery.
    """

    def cleanup_sql(sql_string):
        """Processes the SQL string to get a printable, valid SQL string."""

        # 1. Remove backslashes escaping double quotes
        sql_string = sql_string.replace('\\"', '"')

        # 2. Remove backslashes before newlines (the key fix for this issue)
        sql_string = sql_string.replace("\\\n", "\n")  # Corrected regex

        # 3. Replace escaped single quotes
        sql_string = sql_string.replace("\\'", "'")

        # 4. Replace escaped newlines (those not preceded by a backslash)
        sql_string = sql_string.replace("\\n", "\n")

        # 5. Add limit clause if not present
        if "limit" not in sql_string.lower():
            sql_string = sql_string + " limit " + str(MAX_NUM_ROWS)

        return sql_string

    logging.info("Validating SQL: %s", sql_string)
    sql_string = cleanup_sql(sql_string)
    logging.info("Validating SQL (after cleanup): %s", sql_string)

    final_result = {"query_result": None, "error_message": None}

    # More restrictive check for BigQuery - disallow DML and DDL
    if re.search(
        r"(?i)\b(update|delete|drop|insert|create|alter|truncate|merge)\b", sql_string
    ):
        final_result["error_message"] = (
            "Invalid SQL: Contains disallowed DML/DDL operations."
        )
        return final_result

    try:
        query_job = get_bq_client().query(sql_string)
        results = query_job.result()  # Get the query results

        if results.schema:  # Check if query returned data
            rows = [
                {
                    key: (
                        value
                        if not isinstance(value, datetime.date)
                        else value.strftime("%Y-%m-%d")
                    )
                    for (key, value) in row.items()
                }
                for row in results
            ][
                :MAX_NUM_ROWS
            ]  # Convert BigQuery RowIterator to list of dicts
            # return f"Valid SQL. Results: {rows}"
            final_result["query_result"] = rows

            tool_context.state["query_result"] = rows

        else:
            final_result["error_message"] = (
                "Valid SQL. Query executed successfully (no results)."
            )

    except (
        Exception
    ) as e:  # Catch generic exceptions from BigQuery  # pylint: disable=broad-exception-caught
        final_result["error_message"] = f"Invalid SQL: {e}"

    print("\n run_bigquery_validation final_result: \n", final_result)

    return final_result
