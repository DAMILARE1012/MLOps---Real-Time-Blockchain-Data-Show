from feast import FeatureView, Field
from feast.types import Int64, Float64
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource
from entities import address
import pandas as pd

# Define the PostgreSQL source
postgres_source = PostgreSQLSource(
    name="address_features_source",
    query="""
        SELECT address, total_value, tx_count, avg_value, CURRENT_TIMESTAMP AS event_timestamp
        FROM address_features_table
    """,
    timestamp_field="event_timestamp",
)

# Define the schema for your features
address_features_view = FeatureView(
    name="address_features",
    entities=[address],
    ttl=None,
    schema=[
        Field(name="total_value", dtype=Int64),
        Field(name="tx_count", dtype=Int64),
        Field(name="avg_value", dtype=Float64),
    ],
    online=True,
    source=postgres_source,
    description="Aggregated transaction features per blockchain address."
) 