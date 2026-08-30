from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase connection string format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    openai_api_key: str = "sk-mock-key"
    
    # LangSmith Observability
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str | None = None
    langsmith_project: str = "default"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()