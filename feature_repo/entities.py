from feast import Entity, ValueType

address = Entity(
    name="address",
    join_keys=["address"],
    value_type=ValueType.STRING,
    description="Blockchain address entity for feature store"
) 