from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

class Settings(BaseSettings):
    eventhub_namespace: str | None = Field(default=None, validation_alias='EVENTHUB_NAMESPACE')
    eventhub_topic: str | None = Field(default=None, validation_alias='EVENTHUB_TOPIC')
    eventhub_connection_string: str | None = Field(default=None, validation_alias='EVENTHUB_CONNECTION_STRING')

    default_rate_limit: int = 10

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
