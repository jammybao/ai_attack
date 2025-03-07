"""
安全代理主链 - 使用 LangChain 0.3
"""
from datetime import datetime
import logging
from operator import itemgetter

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain

from security_agent.chains.time_parser_chain import TimeRangeParserChain
from security_agent.chains.log_processor_chain import LogProcessorChain
from security_agent.chains.security_analysis_chain import SecurityAnalysisChain

logger = logging.getLogger(__name__)

class SecurityAgentChain:
    """安全代理主链"""
    
    def __init__(self, config):
        """初始化安全代理链"""
        logger.info("初始化安全代理主链")
        
        # 从配置中获取参数
        api_key = config.TONGYI_API_KEY
        model_name = config.TONGYI_MODEL_NAME
        base_url = config.TONGYI_BASE_URL
        db_connection = config.DB_CONNECTION_STRING
        security_logs_table = config.SECURITY_LOGS_TABLE
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        )
        
        # 初始化数据库连接
        self.db = SQLDatabase.from_uri(db_connection)
        self.execute_query_tool = QuerySQLDataBaseTool(db=self.db)
        
        # 初始化各个子链
        self.time_parser = TimeRangeParserChain(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        )
        
        # 初始化SQL生成链
        self.sql_chain = create_sql_query_chain(self.llm, self.db)
        
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
        
        # 创建回答提示模板
        self.answer_prompt = PromptTemplate.from_template(
            """根据以下用户问题、SQL查询和查询结果，提供详细的安全分析。
            
            问题: {question}
            时间范围: {time_range}
            SQL查询: {query}
            查询结果: {result}
            
            请提供专业的安全分析和建议:"""
        )
    
    async def run(self, query):
        """执行完整的分析流程"""
        logger.info(f"开始处理查询: {query}")
        
        try:
            # 1. 解析时间范围
            time_range = await self.time_parser.parse_time_range(query)
            
            # 2. 生成SQL查询
            sql_query = self.sql_chain.invoke({
                "question": f"查询时间范围在 {time_range['start_time']} 到 {time_range['end_time']} 之间的安全日志",
                "table_names_to_use": ["security_logs"]
            })
            
            # 3. 执行SQL查询获取日志数据
            result = self.execute_query_tool.invoke(sql_query)
            
            # 将结果转换为DataFrame
            import pandas as pd
            import ast
            try:
                data = ast.literal_eval(result)
                if isinstance(data, list) and len(data) > 0:
                    # 获取列名
                    columns = self.db.get_usable_column_names(table_names=["security_logs"])
                    logs_df = pd.DataFrame(data, columns=columns[:len(data[0])] if isinstance(data[0], tuple) else None)
                else:
                    logs_df = pd.DataFrame([{"result": result}])
            except:
                logs_df = pd.DataFrame([{"result": result}])
            
            # 4. 处理日志数据
            processed_data = await self.log_processor.process_logs(logs_df, time_range["formatted_range"])
            
            # 5. 安全分析
            analysis_result = await self.security_analyzer.analyze_security(
                processed_data, 
                logs_df, 
                time_range["formatted_range"]
            )
            
            # 6. 格式化最终结果
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
            
        except Exception as e:
            logger.error(f"处理查询时出错: {str(e)}")
            return {
                "error": f"处理查询时出错: {str(e)}",
                "query": query
            }