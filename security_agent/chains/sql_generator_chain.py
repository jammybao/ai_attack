"""
SQL生成链 - 使用 LangChain 0.3
"""
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
import logging

logger = logging.getLogger(__name__)

class SQLGeneratorChain:
    """SQL生成链"""
    
    def __init__(self, api_key, table_name="security_logs", model_name="qwen-plus", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        """初始化SQL生成链"""
        logger.info(f"初始化SQL生成链，表名: {table_name}")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url
        )
        
        self.table_name = table_name
        
        # 定义SQL生成提示模板
        self.sql_prompt = ChatPromptTemplate.from_template("""
        你是一个SQL专家。请根据以下信息生成一个SQL查询：
        
        数据库表: {table_name}
        时间范围: 从 {start_time} 到 {end_time}
        
        请生成一个SQL查询，查询该表中时间在指定范围内的所有记录，使用event_time字段作为时间字段，按event_time降序排序，限制返回10000条记录。
        
        仅返回SQL查询语句，不要有其他解释。
        """)
        
        # 构建链
        self.chain = self.sql_prompt | self.llm
        
    async def generate_sql(self, time_range, table_schema, db_connection):
        """生成SQL查询"""
        logger.info(f"生成SQL查询，时间范围: {time_range['start_time']} 到 {time_range['end_time']}")
        
        try:
            # 创建临时数据库连接
            db = SQLDatabase.from_uri(db_connection)
            
            # 获取表结构信息
            table_info = db.get_table_info([self.table_name])
            
            # 生成查询
            sql_query = await self.chain.ainvoke({
                "table_name": self.table_name,
                "start_time": time_range["start_time"],
                "end_time": time_range["end_time"],
                "table_info": table_info
            })
            
            # 提取内容
            if hasattr(sql_query, 'content'):
                sql_query = sql_query.content
            
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