"""
官方SQL查询链 - 使用 LangChain 0.3 官方方法
"""
import logging
import re
from typing import Dict, Any, Optional, List

from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

logger = logging.getLogger(__name__)

class OfficialSQLChain:
    """使用LangChain官方方法的SQL查询链"""
    
    def __init__(
        self, 
        api_key: str, 
        db_connection: str,
        model_name: str = "qwen-plus", 
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature: float = 0
    ):
        """初始化官方SQL查询链
        
        Args:
            api_key: API密钥
            db_connection: 数据库连接字符串
            model_name: 模型名称
            base_url: API基础URL
            temperature: 温度参数
        """
        logger.info("初始化官方SQL查询链")
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            temperature=temperature
        )
        
        # 初始化数据库连接
        self.db = SQLDatabase.from_uri(db_connection)
        
        # 创建SQL查询工具
        self.execute_query_tool = QuerySQLDataBaseTool(db=self.db)
        
        # 创建SQL查询链
        self.sql_chain = create_sql_query_chain(self.llm, self.db)
        
        # 创建回答提示模板
        self.answer_chain = self._create_answer_chain()
        
        # 创建完整的查询和回答链
        self.query_and_answer_chain = self._create_query_and_answer_chain()
    
    def _create_answer_chain(self):
        """创建回答链"""
        from langchain_core.prompts import ChatPromptTemplate
        
        template = """根据以下信息回答用户的问题:

用户问题: {question}
SQL查询: {query}
查询结果: {result}

查询结果是JSON格式，包含了查询返回的记录。每个记录是一个包含字段名和值的对象。
请提供详细的回答，解释查询结果的含义。如果结果为空，请说明可能的原因。
请分析数据中的模式和趋势，并提供有意义的见解。
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm | StrOutputParser()
    
    def _create_query_and_answer_chain(self):
        """创建完整的查询和回答链"""
        def _get_result(inputs):
            """获取查询结果并转换为更友好的格式"""
            query = self._extract_sql(inputs["query"])
            raw_result = self.execute_query_tool.invoke(query)
            
            # 尝试将结果转换为更友好的格式
            try:
                # 如果结果是字符串形式的列表或元组
                if raw_result.strip().startswith('[') and raw_result.strip().endswith(']'):
                    import ast
                    import pandas as pd
                    
                    # 解析结果
                    parsed_result = ast.literal_eval(raw_result)
                    
                    # 如果是空列表，直接返回
                    if not parsed_result:
                        return {"result": "[]", **inputs}
                    
                    # 获取列名
                    if query.lower().strip().startswith('select'):
                        # 从查询中提取列名
                        columns = self._extract_columns_from_query(query)
                        
                        # 如果无法从查询中提取列名，尝试从数据库获取
                        if not columns and 'table_names_to_use' in inputs:
                            table_info = self.db.get_table_info(inputs['table_names_to_use'])
                            columns = self._extract_columns_from_table_info(table_info)
                        
                        # 如果仍然没有列名，使用默认列名
                        if not columns:
                            columns = [f"column_{i}" for i in range(len(parsed_result[0]))]
                        
                        # 确保列名数量与结果列数匹配
                        if isinstance(parsed_result[0], (list, tuple)) and len(columns) > len(parsed_result[0]):
                            columns = columns[:len(parsed_result[0])]
                        
                        # 创建DataFrame
                        if isinstance(parsed_result[0], (list, tuple)):
                            df = pd.DataFrame(parsed_result, columns=columns[:len(parsed_result[0])])
                        else:
                            # 处理单列结果
                            df = pd.DataFrame({columns[0]: parsed_result})
                        
                        # 转换为JSON格式
                        result_json = df.to_json(orient='records')
                        return {"result": result_json, **inputs}
            except Exception as e:
                logger.warning(f"转换查询结果格式失败: {e}")
            
            # 如果转换失败，返回原始结果
            return {"result": raw_result, **inputs}
        
        return (
            RunnablePassthrough.assign(query=self.sql_chain)
            | RunnablePassthrough.assign(result=_get_result)
            | self.answer_chain
        )
    
    def _extract_sql(self, sql_text: str) -> str:
        """从LLM输出中提取实际的SQL查询
        
        Args:
            sql_text: 包含SQL查询的文本
            
        Returns:
            提取出的SQL查询
        """
        logger.info(f"提取SQL查询，原始文本: {sql_text[:100]}...")
        
        # 尝试提取SQL代码块
        sql_pattern = r"```sql\s*(.*?)\s*```"
        matches = re.search(sql_pattern, sql_text, re.DOTALL)
        if matches:
            return matches.group(1).strip()
        
        # 尝试提取SQLQuery标记后的内容
        if "SQLQuery:" in sql_text:
            parts = sql_text.split("SQLQuery:")
            if len(parts) > 1:
                # 检查是否有代码块
                code_matches = re.search(r"```\s*(.*?)\s*```", parts[1], re.DOTALL)
                if code_matches:
                    return code_matches.group(1).strip()
                # 否则取整个内容
                return parts[1].strip()
        
        # 如果没有特定标记，返回原始文本
        return sql_text
    
    def generate_sql(self, question: str, table_names: Optional[List[str]] = None) -> str:
        """生成SQL查询
        
        Args:
            question: 用户问题
            table_names: 要使用的表名列表
        
        Returns:
            生成的SQL查询
        """
        logger.info(f"生成SQL查询，问题: {question}")
        
        inputs = {"question": question}
        if table_names:
            inputs["table_names_to_use"] = table_names
            
        try:
            sql_query = self.sql_chain.invoke(inputs)
            logger.info(f"SQL查询生成成功: {sql_query[:100]}...")
            return sql_query
        except Exception as e:
            logger.error(f"SQL查询生成失败: {e}")
            raise
    
    def execute_sql(self, sql_query: str) -> str:
        """执行SQL查询
        
        Args:
            sql_query: SQL查询语句
        
        Returns:
            查询结果
        """
        logger.info(f"执行SQL查询: {sql_query[:100]}...")
        
        try:
            # 提取实际的SQL语句
            clean_sql = self._extract_sql(sql_query)
            logger.info(f"提取的SQL查询: {clean_sql[:100]}...")
            
            # 执行查询
            result = self.execute_query_tool.invoke(clean_sql)
            return result
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            raise
    
    def query_and_answer(self, question: str, table_names: Optional[List[str]] = None) -> str:
        """查询并回答
        
        Args:
            question: 用户问题
            table_names: 要使用的表名列表
        
        Returns:
            回答
        """
        logger.info(f"查询并回答，问题: {question}")
        
        inputs = {"question": question}
        if table_names:
            inputs["table_names_to_use"] = table_names
            
        try:
            answer = self.query_and_answer_chain.invoke(inputs)
            return answer
        except Exception as e:
            logger.error(f"查询并回答失败: {e}")
            raise
    
    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """获取表信息
        
        Args:
            table_names: 表名列表
        
        Returns:
            表信息
        """
        return self.db.get_table_info(table_names)
    
    def get_usable_table_names(self) -> List[str]:
        """获取可用表名列表
        
        Returns:
            可用表名列表
        """
        return self.db.get_usable_table_names()
    
    def _extract_columns_from_query(self, query: str) -> List[str]:
        """从SQL查询中提取列名"""
        try:
            # 简单的正则表达式提取
            match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
            if match:
                columns_str = match.group(1)
                # 处理 SELECT * 的情况
                if '*' in columns_str:
                    return []
                
                # 分割并清理列名
                columns = []
                for col in columns_str.split(','):
                    col = col.strip()
                    # 处理别名
                    if ' AS ' in col.upper():
                        col = col.split(' AS ')[1]
                    elif ' as ' in col:
                        col = col.split(' as ')[1]
                    # 移除反引号和其他修饰
                    col = col.replace('`', '').replace('\'', '').replace('"', '')
                    # 处理函数
                    if '(' in col and ')' in col:
                        col = col.split(')')[-1].strip()
                        if col == '':
                            # 使用函数名作为列名
                            func_match = re.search(r'(\w+)\(', col)
                            if func_match:
                                col = func_match.group(1)
                    columns.append(col)
                return columns
        except Exception as e:
            logger.warning(f"从查询中提取列名失败: {e}")
        return []
    
    def _extract_columns_from_table_info(self, table_info: str) -> List[str]:
        """从表信息中提取列名"""
        try:
            # 简单的正则表达式提取
            columns = []
            for line in table_info.split('\n'):
                if '(' in line and ')' in line:
                    col_match = re.search(r'(\w+)\s+\(', line)
                    if col_match:
                        columns.append(col_match.group(1))
            return columns
        except Exception as e:
            logger.warning(f"从表信息中提取列名失败: {e}")
        return [] 