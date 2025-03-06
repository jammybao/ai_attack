'''
Description: 
version: 
Author: Bao Jiaming
Date: 2025-03-04 12:47:05
LastEditTime: 2025-03-04 12:51:28
FilePath: \security_agent\chains\log_processor_chain.py
'''
"""
日志处理链
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import logging

logger = logging.getLogger(__name__)

class LogProcessorChain:
    """日志处理链"""
    
    def __init__(self, api_key, model_name="qwen-plus", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        """初始化日志处理链"""
        logger.info("初始化日志处理链")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key,
            base_url=base_url
        )
        
        # 定义日志处理提示模板
        self.processor_template = ChatPromptTemplate.from_template("""
        你是一个安全日志处理专家。请分析以下JSON格式的安全日志数据，并生成摘要统计信息。
        
        时间范围: {time_range}
        日志数据: {logs_json}
        
        请提供以下信息：
        1. 日志总数
        2. 不同事件类型的分布
        3. 唯一源IP地址数量
        4. 唯一目标IP地址数量
        5. 最活跃的源IP（列出前5个）
        6. 最常见的事件类型（列出前5个）
        
        请以JSON格式返回结果，包含上述所有信息。
        """)
        
        # 创建解析器
        self.output_parser = JsonOutputParser()
        
        # 构建链
        self.chain = self.processor_template | self.llm | self.output_parser
    
    async def process_logs(self, logs_df, time_range):
        """处理日志数据"""
        logger.info(f"处理日志数据，共 {len(logs_df)} 条记录")
        
        # 将DataFrame转换为JSON
        logs_json = logs_df.to_json(orient="records")
        
        # 如果数据量太大，只取一部分样本
        if len(logs_df) > 1000:
            logger.info(f"日志数据量过大，采样 1000 条记录进行处理")
            sample_df = logs_df.sample(1000)
            logs_json = sample_df.to_json(orient="records")
        
        try:
            response = await self.chain.ainvoke({
                "logs_json": logs_json,
                "time_range": time_range
            })
            
            logger.info("日志处理成功")
            return response
        except Exception as e:
            logger.error(f"日志处理失败: {e}")
            # 如果处理失败，返回基本统计信息
            basic_stats = {
                "total_logs": len(logs_df),
                "event_types": logs_df["event_type"].value_counts().to_dict() if "event_type" in logs_df.columns else {},
                "unique_source_ips": logs_df["source_ip"].nunique() if "source_ip" in logs_df.columns else 0,
                "unique_dest_ips": logs_df["destination_ip"].nunique() if "destination_ip" in logs_df.columns else 0,
                "error": str(e)
            }
            return basic_stats