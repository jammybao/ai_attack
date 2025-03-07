"""
SQL生成链单元测试
"""
import unittest
from unittest.mock import patch, MagicMock

from security_agent.chains.sql_generator_chain import SQLGeneratorChain

class TestSQLGeneratorChain(unittest.TestCase):
    """SQL生成链单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.api_key = "fake_api_key"
        self.table_name = "test_security_logs"
        self.db_connection = "sqlite:///test.db"
        
        # 模拟LLM和链
        self.patcher = patch('security_agent.chains.sql_generator_chain.ChatOpenAI')
        self.mock_llm = self.patcher.start()
        
        # 模拟SQLDatabase
        self.db_patcher = patch('security_agent.chains.sql_generator_chain.SQLDatabase')
        self.mock_db = self.db_patcher.start()
        
        # 设置模拟数据库返回值
        self.mock_db_instance = MagicMock()
        self.mock_db.from_uri.return_value = self.mock_db_instance
        self.mock_db_instance.get_table_info.return_value = "id (INTEGER), timestamp (DATETIME), source_ip (VARCHAR), event_type (VARCHAR)"
        
        # 创建SQL生成链实例
        self.sql_generator = SQLGeneratorChain(self.api_key, self.table_name)
        
        # 模拟链的调用结果
        self.mock_chain = MagicMock()
        self.sql_generator.chain = self.mock_chain
    
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
        self.db_patcher.stop()
    
    async def test_generate_sql_success(self):
        """测试成功生成SQL查询"""
        # 模拟时间范围
        time_range = {
            "start_time": "2025-03-01 04:00:00",
            "end_time": "2025-03-01 12:00:00"
        }
        
        # 模拟生成的SQL
        expected_sql = f"""
        SELECT * FROM {self.table_name}
        WHERE timestamp >= '{time_range["start_time"]}'
        AND timestamp <= '{time_range["end_time"]}'
        ORDER BY timestamp DESC
        LIMIT 10000
        """.strip()
        
        # 创建模拟响应对象
        mock_response = MagicMock()
        mock_response.content = expected_sql
        
        # 设置模拟链的返回值
        self.mock_chain.ainvoke.return_value = mock_response
        
        # 调用SQL生成函数
        result = await self.sql_generator.generate_sql(time_range, "table_schema", self.db_connection)
        
        # 验证结果
        self.assertEqual(result, expected_sql)
        self.mock_chain.ainvoke.assert_called_once()
        
        # 验证调用参数
        call_args = self.mock_chain.ainvoke.call_args[0][0]
        self.assertEqual(call_args["table_name"], self.table_name)
        self.assertEqual(call_args["start_time"], time_range["start_time"])
        self.assertEqual(call_args["end_time"], time_range["end_time"])
    
    async def test_generate_sql_failure(self):
        """测试生成SQL失败时的默认行为"""
        # 模拟时间范围
        time_range = {
            "start_time": "2025-03-01 04:00:00",
            "end_time": "2025-03-01 12:00:00"
        }
        
        # 设置模拟链抛出异常
        self.mock_chain.ainvoke.side_effect = Exception("生成SQL失败")
        
        # 调用SQL生成函数
        result = await self.sql_generator.generate_sql(time_range, "table_schema", self.db_connection)
        
        # 验证结果
        expected_default_sql = f"""
            SELECT * FROM {self.table_name}
            WHERE timestamp >= '{time_range["start_time"]}'
            AND timestamp <= '{time_range["end_time"]}'
            ORDER BY timestamp DESC
            LIMIT 10000
            """.strip()
        
        self.assertEqual(result, expected_default_sql)

if __name__ == "__main__":
    unittest.main() 