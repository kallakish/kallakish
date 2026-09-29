"""Extract Microsoft Fabric semantic-model metadata in a Fabric notebook.

Outputs Spark DataFrames for tables, columns, relationships, partitions,
detected query joins, measures, calculated objects, hierarchies and roles.
Optionally persists every output as a Delta table in the attached Lakehouse.
"""

from __future__ import annotations

import base64
import json
import re
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import requests
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import BooleanType, StringType, StructField, StructType


# ---------------------------------------------------------------------------
# PARAMETERS - replace these two values
# ---------------------------------------------------------------------------
WORKSPACE_ID = "<workspace-guid>"
SEMANTIC_MODEL_ID = "<semantic-model-guid>"

# Set True only when a default Lakehouse is attached to the notebook.
SAVE_AS_DELTA = False
OUTPUT_SCHEMA = "semantic_metadata"

FABRIC_API = "https://api.fabric.microsoft.com/v1"


def get_fabric_token() -> str:
    """Return a Fabric REST API access token from the notebook identity."""
    try:
        from notebookutils import mssparkutils  # type: ignore

        return mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
    except Exception:
        import notebookutils  # type: ignore

        return notebookutils.credentials.getToken("https://api.fabric.microsoft.com")


def raise_for_fabric_error(response: requests.Response, action: str) -> None:
    if response.ok:
        return
    try:
        detail = response.json()
    except ValueError:
        detail = response.text
    raise RuntimeError(f"{action} failed ({response.status_code}): {detail}")


def wait_for_lro(
    session: requests.Session,
    response: requests.Response,
    timeout_seconds: int = 300,
) -> requests.Response:
    """Poll a Fabric long-running operation and return its final response."""
    if response.status_code != 202:
        return response

    location = response.headers.get("Location")
    if not location:
        raise RuntimeError("Fabric returned HTTP 202 without a Location header")

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        delay = int(response.headers.get("Retry-After", "3"))
        time.sleep(min(max(delay, 1), 15))
        response = session.get(location)

        if response.status_code != 202:
            return response

        location = response.headers.get("Location", location)

    raise TimeoutError(f"Fabric operation exceeded {timeout_seconds} seconds")


def get_tmsl_definition(
    workspace_id: str,
    semantic_model_id: str,
    access_token: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (complete definition, decoded model.bim JSON)."""
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {access_token or get_fabric_token()}",
            "Content-Type": "application/json",
        }
    )

    url = (
        f"{FABRIC_API}/workspaces/{workspace_id}/semanticModels/"
        f"{semantic_model_id}/getDefinition?format=TMSL"
    )
    response = wait_for_lro(session, session.post(url))
    raise_for_fabric_error(response, "Get semantic model definition")

    body = response.json()
    if "definition" not in body and isinstance(body.get("result"), dict):
        body = body["result"]

    definition = body["definition"]
    model_part = next(
        (p for p in definition.get("parts", []) if p.get("path") == "model.bim"),
        None,
    )
    if model_part is None:
        raise ValueError("TMSL response did not contain model.bim")

    decoded = base64.b64decode(model_part["payload"]).decode("utf-8-sig")
    return definition, json.loads(decoded)


def expression_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        return "\n".join(str(line) for line in value)
    if isinstance(value, (dict, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def relationship_endpoint(rel: Mapping[str, Any], side: str) -> Tuple[Optional[str], Optional[str]]:
    """Handle common TMSL relationship endpoint representations."""
    table = rel.get(f"{side}Table")
    column = rel.get(f"{side}Column")

    if isinstance(column, Mapping):
        table = table or column.get("table")
        column = column.get("column") or column.get("name")

    return (
        str(table) if table is not None else None,
        str(column) if column is not None else None,
    )


def extract_metadata(model_bim: Mapping[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    model = model_bim.get("model", {})

    tables: List[Dict[str, Any]] = []
    columns: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    partitions: List[Dict[str, Any]] = []
    joins: List[Dict[str, Any]] = []
    measures: List[Dict[str, Any]] = []
    calculated_objects: List[Dict[str, Any]] = []
    hierarchies: List[Dict[str, Any]] = []
    roles: List[Dict[str, Any]] = []

    for table in model.get("tables", []):
        table_name = table.get("name")
        table_type = "Calculated" if any(
            p.get("source", {}).get("type") == "calculated"
            for p in table.get("partitions", [])
        ) else "Physical"

        tables.append(
            {
                "TableName": table_name,
                "TableType": table_type,
                "Description": table.get("description"),
                "IsHidden": bool(table.get("isHidden", False)),
                "ColumnCount": str(len(table.get("columns", []))),
                "MeasureCount": str(len(table.get("measures", []))),
                "PartitionCount": str(len(table.get("partitions", []))),
            }
        )

        for column in table.get("columns", []):
            calc_expression = expression_text(column.get("expression"))
            columns.append(
                {
                    "TableName": table_name,
                    "ColumnName": column.get("name"),
                    "SourceColumn": column.get("sourceColumn"),
                    "DataType": column.get("dataType"),
                    "ColumnType": "Calculated" if calc_expression else "Physical",
                    "Expression": calc_expression,
                    "FormatString": column.get("formatString"),
                    "Description": column.get("description"),
                    "SummarizeBy": column.get("summarizeBy"),
                    "SortByColumn": column.get("sortByColumn"),
                    "IsHidden": bool(column.get("isHidden", False)),
                    "IsKey": bool(column.get("isKey", False)),
                    "IsNullable": bool(column.get("isNullable", True)),
                }
            )
            if calc_expression:
                calculated_objects.append(
                    {
                        "TableName": table_name,
                        "ObjectName": column.get("name"),
                        "ObjectType": "CalculatedColumn",
                        "Expression": calc_expression,
                    }
                )

        for measure in table.get("measures", []):
            measures.append(
                {
                    "TableName": table_name,
                    "MeasureName": measure.get("name"),
                    "Expression": expression_text(measure.get("expression")),
                    "FormatString": measure.get("formatString"),
                    "Description": measure.get("description"),
                    "DisplayFolder": measure.get("displayFolder"),
                    "IsHidden": bool(measure.get("isHidden", False)),
                }
            )

        for hierarchy in table.get("hierarchies", []):
            for position, level in enumerate(hierarchy.get("levels", []), start=1):
                hierarchies.append(
                    {
                        "TableName": table_name,
                        "HierarchyName": hierarchy.get("name"),
                        "LevelPosition": str(position),
                        "LevelName": level.get("name"),
                        "ColumnName": level.get("column"),
                        "IsHidden": bool(hierarchy.get("isHidden", False)),
                    }
                )

        for partition in table.get("partitions", []):
            source = partition.get("source", {}) or {}
            expression = expression_text(source.get("expression"))
            query = expression_text(source.get("query"))
            source_text = "\n".join(x for x in (query, expression) if x)

            partitions.append(
                {
                    "TableName": table_name,
                    "PartitionName": partition.get("name"),
                    "Mode": partition.get("mode"),
                    "SourceType": source.get("type"),
                    "DataSource": source.get("dataSource"),
                    "EntityName": source.get("entityName") or source.get("entity"),
                    "SchemaName": source.get("schemaName") or source.get("schema"),
                    "Query": query,
                    "Expression": expression,
                }
            )

            if source.get("type") == "calculated":
                calculated_objects.append(
                    {
                        "TableName": table_name,
                        "ObjectName": partition.get("name"),
                        "ObjectType": "CalculatedTable",
                        "Expression": expression,
                    }
                )

            if source_text:
                m_join_types = re.findall(
                    r"Table\.(NestedJoin|Join)\s*\(", source_text, flags=re.IGNORECASE
                )
                sql_join_types = re.findall(
                    r"\b(?:(LEFT|RIGHT|FULL|INNER|CROSS)\s+)?JOIN\b",
                    source_text,
                    flags=re.IGNORECASE,
                )

                for join_type in m_join_types:
                    joins.append(
                        {
                            "TableName": table_name,
                            "PartitionName": partition.get("name"),
                            "JoinLanguage": "PowerQueryM",
                            "JoinType": join_type,
                            "SourceText": source_text,
                        }
                    )

                for join_type in sql_join_types:
                    joins.append(
                        {
                            "TableName": table_name,
                            "PartitionName": partition.get("name"),
                            "JoinLanguage": "SQL",
                            "JoinType": join_type.upper() if join_type else "UNSPECIFIED",
                            "SourceText": source_text,
                        }
                    )

    for rel in model.get("relationships", []):
        from_table, from_column = relationship_endpoint(rel, "from")
        to_table, to_column = relationship_endpoint(rel, "to")
        relationships.append(
            {
                "RelationshipName": rel.get("name"),
                "FromTable": from_table,
                "FromColumn": from_column,
                "FromCardinality": rel.get("fromCardinality"),
                "ToTable": to_table,
                "ToColumn": to_column,
                "ToCardinality": rel.get("toCardinality"),
                "CrossFilteringBehavior": rel.get("crossFilteringBehavior"),
                "SecurityFilteringBehavior": rel.get("securityFilteringBehavior"),
                "IsActive": bool(rel.get("isActive", True)),
            }
        )

    for role in model.get("roles", []):
        role_name = role.get("name")
        permissions = role.get("tablePermissions", [])
        if not permissions:
            roles.append(
                {
                    "RoleName": role_name,
                    "TableName": None,
                    "FilterExpression": None,
                    "ModelPermission": role.get("modelPermission"),
                }
            )
        for permission in permissions:
            roles.append(
                {
                    "RoleName": role_name,
                    "TableName": permission.get("name"),
                    "FilterExpression": expression_text(
                        permission.get("filterExpression")
                    ),
                    "ModelPermission": role.get("modelPermission"),
                }
            )

    return {
        "tables": tables,
        "columns": columns,
        "relationships": relationships,
        "partitions": partitions,
        "joins": joins,
        "measures": measures,
        "calculated_objects": calculated_objects,
        "hierarchies": hierarchies,
        "roles": roles,
    }


SCHEMAS = {
    "tables": [
        ("TableName", "string"), ("TableType", "string"),
        ("Description", "string"), ("IsHidden", "boolean"),
        ("ColumnCount", "string"), ("MeasureCount", "string"),
        ("PartitionCount", "string"),
    ],
    "columns": [
        ("TableName", "string"), ("ColumnName", "string"),
        ("SourceColumn", "string"), ("DataType", "string"),
        ("ColumnType", "string"), ("Expression", "string"),
        ("FormatString", "string"), ("Description", "string"),
        ("SummarizeBy", "string"), ("SortByColumn", "string"),
        ("IsHidden", "boolean"), ("IsKey", "boolean"),
        ("IsNullable", "boolean"),
    ],
    "relationships": [
        ("RelationshipName", "string"), ("FromTable", "string"),
        ("FromColumn", "string"), ("FromCardinality", "string"),
        ("ToTable", "string"), ("ToColumn", "string"),
        ("ToCardinality", "string"), ("CrossFilteringBehavior", "string"),
        ("SecurityFilteringBehavior", "string"), ("IsActive", "boolean"),
    ],
    "partitions": [
        ("TableName", "string"), ("PartitionName", "string"),
        ("Mode", "string"), ("SourceType", "string"),
        ("DataSource", "string"), ("EntityName", "string"),
        ("SchemaName", "string"), ("Query", "string"),
        ("Expression", "string"),
    ],
    "joins": [
        ("TableName", "string"), ("PartitionName", "string"),
        ("JoinLanguage", "string"), ("JoinType", "string"),
        ("SourceText", "string"),
    ],
    "measures": [
        ("TableName", "string"), ("MeasureName", "string"),
        ("Expression", "string"), ("FormatString", "string"),
        ("Description", "string"), ("DisplayFolder", "string"),
        ("IsHidden", "boolean"),
    ],
    "calculated_objects": [
        ("TableName", "string"), ("ObjectName", "string"),
        ("ObjectType", "string"), ("Expression", "string"),
    ],
    "hierarchies": [
        ("TableName", "string"), ("HierarchyName", "string"),
        ("LevelPosition", "string"), ("LevelName", "string"),
        ("ColumnName", "string"), ("IsHidden", "boolean"),
    ],
    "roles": [
        ("RoleName", "string"), ("TableName", "string"),
        ("FilterExpression", "string"), ("ModelPermission", "string"),
    ],
}


def spark_schema(fields: Iterable[Tuple[str, str]]) -> StructType:
    return StructType(
        [
            StructField(name, BooleanType() if dtype == "boolean" else StringType(), True)
            for name, dtype in fields
        ]
    )


def create_dataframes(
    spark: SparkSession,
    metadata: Mapping[str, List[Dict[str, Any]]],
) -> Dict[str, DataFrame]:
    return {
        name: spark.createDataFrame(rows, schema=spark_schema(SCHEMAS[name]))
        for name, rows in metadata.items()
    }


def save_delta_tables(
    spark: SparkSession,
    dataframes: Mapping[str, DataFrame],
    output_schema: str,
) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{output_schema}`")
    for name, dataframe in dataframes.items():
        (
            dataframe.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(f"`{output_schema}`.`semantic_model_{name}`")
        )


def run_extraction(
    workspace_id: str = WORKSPACE_ID,
    semantic_model_id: str = SEMANTIC_MODEL_ID,
    save_as_delta: bool = SAVE_AS_DELTA,
) -> Dict[str, DataFrame]:
    _, model_bim = get_tmsl_definition(workspace_id, semantic_model_id)
    metadata = extract_metadata(model_bim)
    dataframes = create_dataframes(spark, metadata)  # noqa: F821 - Fabric provides spark

    print("Semantic model metadata extracted successfully")
    for name, rows in metadata.items():
        print(f"{name}: {len(rows)}")

    if save_as_delta:
        save_delta_tables(spark, dataframes, OUTPUT_SCHEMA)  # noqa: F821
        print(f"Delta outputs saved under schema: {OUTPUT_SCHEMA}")

    return dataframes


# Run in the final notebook cell:
# metadata_dfs = run_extraction()
# display(metadata_dfs["tables"])
# display(metadata_dfs["columns"])
# display(metadata_dfs["relationships"])
# display(metadata_dfs["joins"])
