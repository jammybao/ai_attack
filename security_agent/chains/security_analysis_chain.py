"""
安全分析链
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import logging

logger = logging.getLogger(__name__)

class SecurityAnalysisChain:
    """安全分析链"""
    
    def __init__(self, api_key, model_name="qwen-max", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        """初始化安全分析链"""
        logger.info("初始化安全分析链")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key,
            base_url=base_url
        )
        
        # 定义安全分析提示模板
        self.analysis_template = ChatPromptTemplate.from_template("""
        你是一位网络安全专家，负责分析指定时间范围内的网络安全日志并识别潜在的入侵风险。
        
        时间范围: {time_range}
        
        日志统计摘要:
        {processed_data}
        
        日志样本:
        {sample_logs}
        
        请根据以上信息，对网络安全状况进行分析。特别关注:
        1. 是否存在可能的入侵风险（回答"是"或"否"）
        2. 风险等级（无、低、中、高）
        3. 发现的可疑活动（如果有）
        4. 风险类型（如果有）
        5. 详细分析（包括可疑活动的具体描述）
        6. 建议的应对措施
        
        请以JSON格式返回分析结果，包含如下字段:
        {{"has_risk": true/false, "risk_level": "无/低/中/高", "risk_type": "...", "analysis": "...", "recommendations": [...]}}
        """)
        
        # 创建解析器
        self.output_parser = JsonOutputParser()
        
        # 构建链
        self.chain = self.analysis_template | self.llm | self.output_parser
    
    async def analyze_security(self, processed_data, logs_df, time_range):
        """分析安全风险"""
        logger.info("开始安全风险分析")
        
        # 获取日志样本
        sample_logs = logs_df.head(50).to_string() if not logs_df.empty else "无日志数据"
        
        try:
            response = await self.chain.ainvoke({
                "processed_data": json.dumps(processed_data, indent=2, ensure_ascii=False),
                "time_range": time_range,
                "sample_logs": sample_logs
            })
            
            logger.info("安全风险分析完成")
            return response
        except Exception as e:
            logger.error(f"安全风险分析失败: {e}")
            # 返回一个默认的结果
            return {
                "has_risk": False,
                "risk_level": "未知",
                "risk_type": None,
                "analysis": f"无法解析分析结果，请稍后重试。错误: {str(e)}",
                "recommendations": ["检查系统日志", "联系安全团队"]
            } 