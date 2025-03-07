"""
LangChain 数据库工具单元测试
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime, timedelta

from langchain_community.utilities.sql_database import SQLDatabase
from security_agent.models.security_log import Base, SecurityLog

class TestLangChainDBTools(unittest.TestCase):
    """LangChain 数据库工具单元测试"""
    
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
        
        # 生成测试数据
        self._generate_test_data()
    
    def tearDown(self):
        """测试后清理"""
        # 关闭会话
        self.session.close()
        
        # 删除临时数据库文件
        if os.path.exists(self.temp_db_file.name):
            os.unlink(self.temp_db_file.name)
    
    def _generate_test_data(self):
        """生成测试数据"""
        # 创建测试数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        # 创建数据框
        data = {
            "timestamp": [start_time + timedelta(hours=i) for i in range(24)],
            "source_ip": [f"192.168.1.{i}" for i in range(1, 25)],
            "destination_ip": [f"10.0.0.{i}" for i in range(1, 25)],
            "event_type": ["登录尝试", "登录成功", "登录失败", "权限提升"] * 6,
            "severity": ["低", "中", "高", "严重"] * 6,
            "protocol": ["TCP", "UDP", "HTTP", "HTTPS"] * 6,
            "source_port": [random_port for random_port in range(1024, 1024 + 24)],
            "destination_port": [80, 443, 22, 3306] * 6,
            "user_id": ["admin", "user1", "user2", "system"] * 6,
            "action": ["允许", "拒绝", "警告", "阻止"] * 6,
            "status": ["成功", "失败", "超时", "中断"] * 6,
            "bytes_sent": [100 * i for i in range(1, 25)],
            "bytes_received": [200 * i for i in range(1, 25)],
            "session_duration": [10 * i for i in range(1, 25)]
        }
        
        # 添加描述和原始日志
        descriptions = []
        raw_logs = []
        
        for i in range(24):
            event = data["event_type"][i]
            src_ip = data["source_ip"][i]
            dst_ip = data["destination_ip"][i]
            user = data["user_id"][i]
            action = data["action"][i]
            status = data["status"][i]
            
            description = f"{event}：来自 {src_ip} 的用户 {user} 尝试访问 {dst_ip}，{action}，{status}"
            descriptions.append(description)
            
            raw_log = (
                f"{data['timestamp'][i].strftime('%Y-%m-%d %H:%M:%S.%f')} "
                f"{data['protocol'][i]} {src_ip}:{data['source_port'][i]} -> "
                f"{dst_ip}:{data['destination_port'][i]} {event} {action} {status} "
                f"user={user} sent={data['bytes_sent'][i]} rcvd={data['bytes_received'][i]} "
                f"duration={data['session_duration'][i]}s"
            )
            raw_logs.append(raw_log)
        
        data["description"] = descriptions
        data["raw_log"] = raw_logs
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 写入数据库
        df.to_sql("security_logs", self.engine, if_exists="append", index=False)
    
    def test_sql_database_connection(self):
        """测试 SQLDatabase 连接"""
        # 创建 SQLDatabase 实例
        db = SQLDatabase.from_uri(self.db_connection_string)
        
        # 验证连接
        self.assertIsNotNone(db)
        
        # 验证表信息
        table_info = db.get_table_info()
        self.assertIn("security_logs", table_info)
    
    def test_sql_database_run_query(self):
        """测试 SQLDatabase 查询"""
        # 创建 SQLDatabase 实例
        db = SQLDatabase.from_uri(self.db_connection_string)
        
        # 执行查询
        result = db.run("SELECT COUNT(*) FROM security_logs")
        
        # 验证结果
        self.assertIn("24", result)
    
    def test_sql_database_get_table_info(self):
        """测试获取表信息"""
        # 创建 SQLDatabase 实例
        db = SQLDatabase.from_uri(self.db_connection_string)
        
        # 获取表信息
        table_info = db.get_table_info(["security_logs"])
        
        # 验证表信息
        self.assertIn("security_logs", table_info)
        self.assertIn("timestamp", table_info)
        self.assertIn("source_ip", table_info)
        self.assertIn("event_type", table_info)

if __name__ == "__main__":
    unittest.main() 