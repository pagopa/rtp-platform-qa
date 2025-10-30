from pydantic import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    eventhub_namespace: str = Field(..., env='EVENTHUB_NAMESPACE')
    eventhub_topic: str = Field(..., env='EVENTHUB_TOPIC')
    eventhub_connection_string: str | None = Field(None, env='EVENTHUB_CONNECTION_STRING')

    default_rate_limit: int = 10

    class Config:
        case_sensitive = True

settings = Settings()
