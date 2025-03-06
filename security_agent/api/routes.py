'''
Description: 
version: 
Author: Bao Jiaming
Date: 2025-03-04 12:43:49
LastEditTime: 2025-03-04 12:44:35
FilePath: \security_agent\api\routes.py
'''
"""
API路由定义
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime

from security_agent.chains.security_agent_chain import SecurityAgentChain
from security_agent.config import settings

router = APIRouter()

class SecurityQuery(BaseModel):
    """安全查询请求模型"""
    query: str  # 用户自然语言查询，如"前8小时是否有网络安全攻击风险"

class RiskAnalysisResult(BaseModel):
    """风险分析结果模型"""
    timestamp: datetime.datetime
    time_range: str
    has_risk: bool
    risk_level: str
    risk_type: Optional[str] = None
    analysis: str
    recommendations: List[str]

def get_security_chain():
    """获取安全代理链的依赖注入函数"""
    config = {
        "tongyi_api_key": settings.TONGYI_API_KEY,
        "tongyi_model_name": settings.TONGYI_MODEL_NAME,
        "tongyi_base_url": settings.TONGYI_BASE_URL,
        "db_connection_string": settings.DB_CONNECTION_STRING,
        "security_logs_table": settings.SECURITY_LOGS_TABLE
    }
    return SecurityAgentChain(config)

@router.post("/security/analyze", response_model=RiskAnalysisResult)
async def analyze_security_logs(query: SecurityQuery, security_chain: SecurityAgentChain = Depends(get_security_chain)):
    """分析网络安全日志"""
    try:
        result = await security_chain.run(query.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 