'''
Description: 
version: 
Author: Bao Jiaming
Date: 2025-03-04 12:46:37
LastEditTime: 2025-03-06 20:45:36
FilePath: \security_agent\chains\sql_generator_chain.py
'''
"""
SQL生成链
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

logger = logging.getLogger(__name__)

class SQLGeneratorChain:
    """SQL生成链"""
    
    def __init__(self, api_key, table_name="security_logs", model_name="qwen-plus", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        """初始化SQL生成链"""
        logger.info(f"初始化SQL生成链，表名: {table_name}")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key,
            base_url=base_url
        )
        
        self.table_name = table_name
        
        # 定义SQL生成提示模板
        self.sql_template = ChatPromptTemplate.from_template("""
        你是一个SQL专家。请根据以下信息生成一个SQL查询语句，用于从安全日志表中检索指定时间范围内的数据。
        
        表名: {table_name}
        表结构: {table_schema}
        时间范围: 起始时间 = {start_time}, 结束时间 = {end_time}
        
        生成的SQL应该：
        1. 选择所有相关字段
        2. 根据提供的时间范围过滤数据
        3. 按时间戳降序排序
        4. 限制返回最多10000条记录以避免性能问题
        
        只返回SQL语句本身，不要有其他文本。
        """)
        
        # 创建解析器
        self.output_parser = StrOutputParser()
        
        # 构建链
        self.chain = self.sql_template | self.llm | self.output_parser
    
    async def generate_sql(self, time_range, table_schema):
        """生成SQL查询"""
        logger.info(f"生成SQL查询，时间范围: {time_range['start_time']} 到 {time_range['end_time']}")
        
        try:
            response = await self.chain.ainvoke({
                "table_name": self.table_name,
                "table_schema": table_schema,
                "start_time": time_range["start_time"],
                "end_time": time_range["end_time"]
            })
            
            sql_query = response.strip()
            logger.info(f"SQL查询生成成功: {sql_query}")
            return sql_query
        except Exception as e:
            logger.error(f"SQL查询生成失败: {e}")
            # 如果生成失败，返回默认SQL
            default_sql = f"""
            SELECT * FROM {self.table_name}
            WHERE event_time >= '{time_range["start_time"]}'
            AND event_time <= '{time_range["end_time"]}'
            ORDER BY event_time DESC
            LIMIT 10000
            """
            return default_sql.strip() 