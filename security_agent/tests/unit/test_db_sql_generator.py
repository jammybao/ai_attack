# -*- coding: utf-8 -*-
"""
数据库 SQL 生成测试
"""
import unittest
import asyncio
import sys
from datetime import datetime

import pytest

from security_agent.chains.sql_generator_chain import SQLGeneratorChain
from security_agent.chains.time_parser_chain import TimeRangeParserChain
from security_agent.config import settings

class TestDBSQLGenerator(unittest.TestCase):
    """数据库 SQL 生成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 使用实际的API密钥（从环境变量或配置中获取）
        self.api_key = settings.TONGYI_API_KEY
        
        # 创建实际的SQL生成链和时间解析链实例
        self.sql_generator = SQLGeneratorChain(
            self.api_key, 
            settings.SECURITY_LOGS_TABLE,
            model_name=settings.TONGYI_MODEL_NAME,
            base_url=settings.TONGYI_BASE_URL
        )
        
        self.time_parser = TimeRangeParserChain(
            self.api_key,
            model_name=settings.TONGYI_MODEL_NAME,
            base_url=settings.TONGYI_BASE_URL
        )
    
    def test_generate_sql_from_time_query(self):
        """测试从时间查询生成 SQL"""
        # 使用事件循环运行异步测试
        asyncio.run(self._async_test_generate_sql())
    
    async def _async_test_generate_sql(self):
        """异步测试实现"""
        # 测试案例列表
        test_cases = [
            "前8小时是否有网络安全攻击风险",
            "昨天有哪些登录失败的记录",
            "上周五到本周一期间的异常活动",
            "今天早上8点到现在的所有高危警报"
        ]
        
        print("\n\n========== 测试结果 ==========")
        
        for query in test_cases:
            # 实际调用时间解析链
            time_range = await self.time_parser.parse_time_range(query)
            
            # 实际调用SQL生成链
            sql = await self.sql_generator.generate_sql(
                time_range, 
                "table_schema", 
                settings.DB_CONNECTION_STRING
            )
            
            # 打印结果
            print("\n查询:", query)
            
            # 获取时间范围信息
            start_time = time_range.get("start_time", "")
            end_time = time_range.get("end_time", "")
            formatted_range = time_range.get("formatted_range", f"{start_time} 至 {end_time}")
            
            print("时间范围:", formatted_range)
            print("时间解析详情:", time_range)
            print("生成的 SQL:", sql)
            print("-" * 50)
            
            # 强制刷新标准输出
            sys.stdout.flush()


# 另一种方法：使用 pytest-asyncio 装饰器
@pytest.mark.asyncio
async def test_generate_sql_with_pytest():
    """使用 pytest-asyncio 的异步测试"""
    # 创建实例
    api_key = settings.TONGYI_API_KEY
    sql_generator = SQLGeneratorChain(
        api_key, 
        settings.SECURITY_LOGS_TABLE,
        model_name=settings.TONGYI_MODEL_NAME,
        base_url=settings.TONGYI_BASE_URL
    )
    
    time_parser = TimeRangeParserChain(
        api_key,
        model_name=settings.TONGYI_MODEL_NAME,
        base_url=settings.TONGYI_BASE_URL
    )
    
    # 测试案例
    test_cases = [
        "前8小时是否有网络安全攻击风险",
        "昨天有哪些登录失败的记录",
        "上周五到本周一期间的异常活动",
        "今天早上8点到现在的所有高危警报"
    ]
    
    print("\n\n========== pytest-asyncio 测试结果 ==========")
    
    for query in test_cases:
        # 实际调用时间解析链
        time_range = await time_parser.parse_time_range(query)
        
        # 实际调用SQL生成链
        sql = await sql_generator.generate_sql(
            time_range, 
            "table_schema", 
            settings.DB_CONNECTION_STRING
        )
        
        # 打印结果
        print("\n查询:", query)
        
        # 获取时间范围信息
        start_time = time_range.get("start_time", "")
        end_time = time_range.get("end_time", "")
        formatted_range = time_range.get("formatted_range", f"{start_time} 至 {end_time}")
        
        print("时间范围:", formatted_range)
        print("时间解析详情:", time_range)
        print("生成的 SQL:", sql)
        print("-" * 50)
        
        # 强制刷新标准输出
        sys.stdout.flush()


def run_async_test():
    """运行异步测试"""
    test = TestDBSQLGenerator()
    test.setUp()
    asyncio.run(test._async_test_generate_sql())

if __name__ == "__main__":
    # 直接运行此文件时，执行异步测试
    run_async_test()