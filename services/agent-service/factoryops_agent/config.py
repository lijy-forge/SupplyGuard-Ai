from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FACTORYOPS_")
    business_url: str = "http://business-service:8081/api/v1"
    redis_url: str = "redis://redis:6379/0"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "factoryops"
    qdrant_url: str = "http://qdrant:6333"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/%2F"
    llm_provider: str = "fake"
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

settings = Settings()
