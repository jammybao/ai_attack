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
        
        # 模拟LLM和链
        self.patcher = patch('security_agent.chains.sql_generator_chain.ChatOpenAI')
        self.mock_llm = self.patcher.start()
        
        # 创建SQL生成链实例
        self.sql_generator = SQLGeneratorChain(self.api_key, self.table_name)
        
        # 模拟链的调用结果
        self.mock_chain = MagicMock()
        self.sql_generator.chain = self.mock_chain
    
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    async def test_generate_sql_success(self):
        """测试成功生成SQL查询"""
        # 模拟时间范围
        time_range = {
            "start_time": "2025-03-01 04:00:00",
            "end_time": "2025-03-01 12:00:00"
        }
        
        # 模拟表结构
        table_schema = "id (INTEGER), timestamp (DATETIME), source_ip (VARCHAR), event_type (VARCHAR)"
        
        # 模拟生成的SQL
        expected_sql = f"""
        SELECT * FROM {self.table_name}
        WHERE timestamp >= '{time_range["start_time"]}'
        AND timestamp <= '{time_range["end_time"]}'
        ORDER BY timestamp DESC
        LIMIT 10000
        """.strip()
        
        # 设置模拟链的返回值
        self.mock_chain.ainvoke.return_value = expected_sql
        
        # 调用SQL生成函数
        result = await self.sql_generator.generate_sql(time_range, table_schema)
        
        # 验证结果
        self.assertEqual(result, expected_sql)
        self.mock_chain.ainvoke.assert_called_once()
    
    async def test_generate_sql_failure(self):
        """测试生成SQL失败时的默认行为"""
        # 模拟时间范围
        time_range = {
            "start_time": "2025-03-01 04:00:00",
            "end_time": "2025-03-01 12:00:00"
        }
        
        # 模拟表结构
        table_schema = "id (INTEGER), timestamp (DATETIME), source_ip (VARCHAR), event_type (VARCHAR)"
        
        # 设置模拟链抛出异常
        self.mock_chain.ainvoke.side_effect = Exception("生成SQL失败")
        
        # 调用SQL生成函数
        result = await self.sql_generator.generate_sql(time_range, table_schema)
        
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