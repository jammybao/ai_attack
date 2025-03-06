'''
Description: 
version: 
Author: Bao Jiaming
Date: 2025-03-04 12:45:21
LastEditTime: 2025-03-04 12:46:32
FilePath: \security_agent\database\accessor.py
'''
"""
数据库访问器
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DatabaseAccessor:
    """数据库访问器类"""
    
    def __init__(self, connection_string):
        """初始化数据库连接"""
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        logger.info(f"数据库连接已初始化: {connection_string}")
    
    def get_table_schema(self, table_name):
        """获取表结构"""
        if table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            schema = []
            for column in table.columns:
                schema.append(f"{column.name} ({column.type})")
            return ", ".join(schema)
        logger.warning(f"表 {table_name} 不存在")
        return None
    
    async def execute_query(self, sql_query):
        """执行SQL查询并返回结果"""
        try:
            logger.debug(f"执行SQL查询: {sql_query}")
            # 使用pandas读取SQL查询结果
            df = pd.read_sql(sql_query, self.engine)
            logger.info(f"查询成功，返回 {len(df)} 条记录")
            return df
        except Exception as e:
            logger.error(f"SQL执行错误: {e}")
            return pd.DataFrame()
    
    async def get_logs_by_timerange(self, start_time, end_time, table_name="security_logs"):
        """获取指定时间范围内的安全日志"""
        query = f"""
            SELECT * FROM {table_name}
            WHERE timestamp >= '{start_time}'
            AND timestamp <= '{end_time}'
            ORDER BY timestamp DESC
            LIMIT 10000
        """
        logger.info(f"获取时间范围内的日志: {start_time} 到 {end_time}")
        return await self.execute_query(query) 