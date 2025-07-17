from pydantic import BaseModel, Field


class JobSchema(BaseModel):
    """Модель задания."""
    create_table_query: str  = Field(validation_alias="CREATE_TABLE_SQL")
    select_source_query: str = Field(validation_alias="SELECT_SOURCE_SQL")
    upsert_target_query: str = Field(validation_alias="UPSERT_TARGET_SQL")
    select_keys_query: str = Field(validation_alias="SELECT_KEYS_SQL")
    target_table: str = Field(validation_alias="TARGET_TABLE")
    key_columns: list[str] = Field(validation_alias="KEY_COLUMNS")