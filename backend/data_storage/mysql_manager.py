"""
MySQL 数据库管理模块
基于大数据的天气数据分析与可视化系统
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import yaml
import os
from loguru import logger

from .models import Base, create_all_tables


class MySQLManager:
    """MySQL 数据库管理器"""
    
    def __init__(self, config_path=None):
        """
        初始化 MySQL 管理器
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/config.yaml'
            )
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.db_config = self.config['database']['mysql']
        
        # 创建数据库连接
        self.engine = self._create_engine()
        self.SessionFactory = scoped_session(sessionmaker(bind=self.engine))
        
        logger.info("MySQL 管理器初始化成功")
    
    def _create_engine(self):
        """创建数据库引擎"""
        connection_string = (
            f"mysql+pymysql://{self.db_config['username']}:"
            f"{self.db_config['password']}@{self.db_config['host']}:"
            f"{self.db_config['port']}/{self.db_config['database']}"
            f"?charset={self.db_config['charset']}"
        )
        
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=self.db_config['pool_size'],
            max_overflow=self.db_config['max_overflow'],
            pool_pre_ping=True,  # 自动检测连接是否有效
            echo=False  # 不显示 SQL 语句
        )
        
        logger.info(f"MySQL 连接创建成功: {self.db_config['host']}:{self.db_config['port']}")
        return engine
    
    @contextmanager
    def get_session(self):
        """
        获取数据库会话（上下文管理器）
        
        使用示例:
            with mysql_manager.get_session() as session:
                result = session.query(User).all()
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {str(e)}")
            raise
        finally:
            session.close()
    
    def create_database_if_not_exists(self):
        """创建数据库（如果不存在）"""
        try:
            # 连接到 MySQL 服务器（不指定数据库）
            connection_string = (
                f"mysql+pymysql://{self.db_config['username']}:"
                f"{self.db_config['password']}@{self.db_config['host']}:"
                f"{self.db_config['port']}/?charset={self.db_config['charset']}"
            )
            
            temp_engine = create_engine(connection_string)
            
            with temp_engine.connect() as conn:
                # 检查数据库是否存在
                result = conn.execute(
                    text(f"SHOW DATABASES LIKE '{self.db_config['database']}'")
                )
                
                if result.fetchone() is None:
                    # 数据库不存在，创建数据库
                    conn.execute(
                        text(f"CREATE DATABASE {self.db_config['database']} "
                             f"CHARACTER SET {self.db_config['charset']} "
                             f"COLLATE {self.db_config['charset']}_unicode_ci")
                    )
                    conn.commit()
                    logger.info(f"数据库 {self.db_config['database']} 创建成功")
                else:
                    logger.info(f"数据库 {self.db_config['database']} 已存在")
            
            temp_engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"创建数据库失败: {str(e)}")
            return False
    
    def init_tables(self):
        """初始化所有数据表"""
        try:
            create_all_tables(self.engine)
            logger.info("数据表初始化成功")
            return True
        except Exception as e:
            logger.error(f"数据表初始化失败: {str(e)}")
            return False
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            return False
    
    def execute_sql(self, sql, params=None):
        """
        执行 SQL 语句
        
        Args:
            sql: SQL 语句
            params: 参数字典
            
        Returns:
            查询结果
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(sql), params)
                else:
                    result = conn.execute(text(sql))
                conn.commit()
                return result
        except Exception as e:
            logger.error(f"SQL 执行失败: {str(e)}")
            raise
    
    def get_table_info(self, table_name):
        """获取表信息"""
        try:
            sql = f"""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                IS_NULLABLE, 
                COLUMN_KEY, 
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = :database 
            AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
            """
            
            result = self.execute_sql(
                sql, 
                {
                    'database': self.db_config['database'], 
                    'table_name': table_name
                }
            )
            
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2],
                    'key': row[3],
                    'comment': row[4]
                })
            
            return columns
            
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}")
            return []
    
    def get_table_count(self, table_name):
        """获取表记录数"""
        try:
            sql = f"SELECT COUNT(*) FROM {table_name}"
            result = self.execute_sql(sql)
            count = result.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"获取表记录数失败: {str(e)}")
            return 0
    
    def truncate_table(self, table_name):
        """清空表数据"""
        try:
            sql = f"TRUNCATE TABLE {table_name}"
            self.execute_sql(sql)
            logger.info(f"表 {table_name} 已清空")
            return True
        except Exception as e:
            logger.error(f"清空表失败: {str(e)}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        try:
            self.SessionFactory.remove()
            self.engine.dispose()
            logger.info("MySQL 连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")


# 全局 MySQL 管理器实例
mysql_manager = None


def get_mysql_manager(config_path=None):
    """
    获取 MySQL 管理器实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        MySQLManager 实例
    """
    global mysql_manager
    
    if mysql_manager is None:
        mysql_manager = MySQLManager(config_path)
    
    return mysql_manager


if __name__ == "__main__":
    """测试 MySQL 管理器"""
    
    # 配置日志
    logger.add(
        "../logs/mysql_manager.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    # 创建管理器
    manager = MySQLManager()
    
    # 测试连接
    if manager.test_connection():
        print("✅ 数据库连接测试成功")
    else:
        print("❌ 数据库连接测试失败")
        exit(1)
    
    # 创建数据库
    if manager.create_database_if_not_exists():
        print("✅ 数据库创建/检查成功")
    else:
        print("❌ 数据库创建失败")
        exit(1)
    
    # 初始化表
    if manager.init_tables():
        print("✅ 数据表初始化成功")
    else:
        print("❌ 数据表初始化失败")
        exit(1)
    
    # 获取表信息
    print("\n📊 数据表信息:")
    tables = [
        'weather_stations',
        'weather_realtime',
        'weather_historical',
        'weather_alerts',
        'weather_predictions',
        'users'
    ]
    
    for table in tables:
        count = manager.get_table_count(table)
        print(f"  - {table}: {count} 条记录")
    
    # 关闭连接
    manager.close()
    print("\n✅ MySQL 管理器测试完成")


