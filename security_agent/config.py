"""
配置文件
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """应用程序设置"""
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 主机和端口配置
    HOST: str = "0.0.0.0"  # 默认值，可被环境变量覆盖
    PORT: int = 8000       # 默认值，可被环境变量覆盖
    
    # 通义千问API配置
    TONGYI_API_KEY: str = ""  # 敏感信息，不设默认值，必须从环境变量获取
    TONGYI_MODEL_NAME: str = "qwen-plus"  # 默认值
    TONGYI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 默认值
    
    # 数据库配置
    DB_CONNECTION_STRING: str = "sqlite:///./security_logs.db"  # 默认值
    SECURITY_LOGS_TABLE: str = "security_logs"  # 默认值
    
    # 日志配置
    LOG_LEVEL: str = "INFO"  # 默认值
    
    # 使用新的配置方式
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # 允许额外的字段
    )

# 创建设置实例
settings = Settings()