from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str | None = None  # Optional: only needed for local JWT verification; get_user(token) does not use it
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}
