"""
安全代理主链
"""
from datetime import datetime
import logging

from security_agent.chains.time_parser_chain import TimeRangeParserChain
from security_agent.chains.sql_generator_chain import SQLGeneratorChain
from security_agent.chains.log_processor_chain import LogProcessorChain
from security_agent.chains.security_analysis_chain import SecurityAnalysisChain
from security_agent.database.accessor import DatabaseAccessor

logger = logging.getLogger(__name__)

class SecurityAgentChain:
    """安全代理主链"""
    
    def __init__(self, config):
        """初始化安全代理链"""
        logger.info("初始化安全代理主链")
        
        # 从配置中获取参数
        api_key = config["tongyi_api_key"]
        model_name = config.get("tongyi_model_name", "qwen-max")
        base_url = config.get("tongyi_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        db_connection = config["db_connection_string"]
        security_logs_table = config.get("security_logs_table", "security_logs")
        
        # 初始化各个子链
        self.time_parser = TimeRangeParserChain(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        )
        
        self.sql_generator = SQLGeneratorChain(
            api_key=api_key,
            table_name=security_logs_table,
            model_name=model_name,
            base_url=base_url
        )
        
        self.db_accessor = DatabaseAccessor(db_connection)
        
        self.log_processor = LogProcessorChain(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        )
        
        self.security_analyzer = SecurityAnalysisChain(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        )
    
    async def run(self, query):
        """执行完整的分析流程"""
        logger.info(f"开始处理查询: {query}")
        
        # 1. 解析时间范围
        time_range = await self.time_parser.parse_time_range(query)
        
        # 2. 获取表结构
        table_schema = self.db_accessor.get_table_schema("security_logs")
        
        # 3. 生成SQL查询
        sql_query = await self.sql_generator.generate_sql(time_range, table_schema)
        
        # 4. 执行SQL查询获取日志数据
        logs_df = await self.db_accessor.execute_query(sql_query)
        
        # 5. 处理日志数据
        processed_data = await self.log_processor.process_logs(logs_df, time_range["formatted_range"])
        
        # 6. 安全分析
        analysis_result = await self.security_analyzer.analyze_security(
            processed_data, 
            logs_df, 
            time_range["formatted_range"]
        )
        
        # 7. 格式化最终结果
        final_result = {
            "timestamp": datetime.now(),
            "time_range": time_range["formatted_range"],
            "has_risk": analysis_result["has_risk"],
            "risk_level": analysis_result["risk_level"],
            "risk_type": analysis_result.get("risk_type"),
            "analysis": analysis_result["analysis"],
            "recommendations": analysis_result["recommendations"]
        }
        
        logger.info("查询处理完成")
        return final_result 