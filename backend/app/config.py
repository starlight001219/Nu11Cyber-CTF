import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = 'Nu11Cyber CTF Platform'
    # 生产环境必须通过 .env 或环境变量设置以下三个密钥
    SECRET_KEY: str = ''  # JWT 签名密钥（必填）
    MASTER_KEY: str = ''  # 密码加密主密钥（必填）
    FLAG_KEY: str = ''    # Flag 加密密钥（必填）
    PRODUCTION: bool = os.getenv('PRODUCTION', 'true').lower() in ('true', '1', 'yes')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./nu11cyber.db')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    FLAG_PREFIX: str = 'Nu11Cyber'
    LAB_FLAG_PREFIX: str = '{ADMIN_NAME}'
    LAB_CONTAINER_TIMEOUT: int = 3600
    MAX_CONCURRENT_LABS: int = 50
    LAB_PORT_RANGE_START: int = 10000
    LAB_PORT_RANGE_END: int = 10100
    DOCKER_NETWORK: str = 'nu11cyber-lab-net'
    RATE_LIMIT_PER_MINUTE: int = 20

    class Config:
        env_file = '.env'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SECRET_KEY or not self.MASTER_KEY or not self.FLAG_KEY:
            raise RuntimeError(
                "SECRET_KEY, MASTER_KEY, FLAG_KEY 必须在 .env 或环境变量中设置。"
            )

settings = Settings()

