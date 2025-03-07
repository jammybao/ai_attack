"""
数据库操作单元测试
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from security_agent.models.security_log import Base, SecurityLog
from security_agent.utils.db_init import init_database, generate_sample_data

class TestDatabaseOperations(unittest.TestCase):
    """数据库操作单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库文件
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db_file.close()
        
        # 创建数据库连接字符串
        self.db_connection_string = f"sqlite:///{self.temp_db_file.name}"
        
        # 创建数据库引擎
        self.engine = create_engine(self.db_connection_string)
        
        # 创建表
        Base.metadata.create_all(self.engine)
        
        # 创建会话
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def tearDown(self):
        """测试后清理"""
        # 关闭会话
        self.session.close()
        
        # 删除临时数据库文件
        if os.path.exists(self.temp_db_file.name):
            os.unlink(self.temp_db_file.name)
    
    def test_create_tables(self):
        """测试创建表"""
        # 检查表是否存在
        self.assertTrue(self.engine.has_table("security_logs"))
    
    def test_generate_sample_data(self):
        """测试生成示例数据"""
        # 生成少量示例数据
        generate_sample_data(self.engine, num_records=10)
        
        # 查询数据
        logs = self.session.query(SecurityLog).all()
        
        # 验证数据
        self.assertEqual(len(logs), 10)
        
        # 验证字段
        for log in logs:
            self.assertIsNotNone(log.timestamp)
            self.assertIsNotNone(log.source_ip)
            self.assertIsNotNone(log.destination_ip)
            self.assertIsNotNone(log.event_type)
            self.assertIsNotNone(log.severity)
    
    @patch('security_agent.utils.db_init.generate_sample_data')
    def test_init_database_with_existing_data(self, mock_generate_sample_data):
        """测试初始化数据库（已有数据）"""
        # 添加一条记录
        log = SecurityLog(
            timestamp="2025-03-01 12:00:00",
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            event_type="登录尝试",
            severity="低"
        )
        self.session.add(log)
        self.session.commit()
        
        # 模拟配置
        with patch('security_agent.utils.db_init.settings') as mock_settings:
            mock_settings.DB_CONNECTION_STRING = self.db_connection_string
            
            # 调用初始化函数
            init_database()
            
            # 验证不会生成示例数据
            mock_generate_sample_data.assert_not_called()
    
    @patch('security_agent.utils.db_init.generate_sample_data')
    def test_init_database_without_existing_data(self, mock_generate_sample_data):
        """测试初始化数据库（无数据）"""
        # 模拟配置
        with patch('security_agent.utils.db_init.settings') as mock_settings:
            mock_settings.DB_CONNECTION_STRING = self.db_connection_string
            
            # 调用初始化函数
            init_database()
            
            # 验证会生成示例数据
            mock_generate_sample_data.assert_called_once()

if __name__ == "__main__":
    unittest.main() 