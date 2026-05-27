"""
Hadoop HDFS 数据管理模块
用于存储非结构化数据（卫星图像、雷达图像、大规模历史数据）
"""

from hdfs import InsecureClient
import os
import yaml
from loguru import logger
from datetime import datetime
import json


class HDFSManager:
    """HDFS 管理器"""
    
    def __init__(self, config_path=None):
        """
        初始化 HDFS 管理器
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.hdfs_config = config['hadoop']['hdfs']
        self.paths = config['data_storage']['hdfs_paths']
        
        # 创建 HDFS 客户端
        self.client = self._create_client()
        
        # 初始化目录结构
        self._init_directories()
        
        logger.info("HDFS 管理器初始化成功")
    
    def _create_client(self):
        """创建 HDFS 客户端"""
        try:
            url = f"http://{self.hdfs_config['namenode']}:{self.hdfs_config['port']}"
            client = InsecureClient(
                url,
                user=self.hdfs_config['user']
            )
            
            # 测试连接
            client.status('/')
            
            logger.info(f"HDFS 客户端连接成功: {url}")
            return client
            
        except Exception as e:
            logger.error(f"HDFS 客户端连接失败: {str(e)}")
            # 返回 None，允许程序继续运行（降级为本地存储）
            return None
    
    def _init_directories(self):
        """初始化 HDFS 目录结构"""
        if not self.client:
            logger.warning("HDFS 客户端未连接，跳过目录初始化")
            return
        
        try:
            for path_name, path_value in self.paths.items():
                if not self.exists(path_value):
                    self.mkdir(path_value)
                    logger.info(f"创建 HDFS 目录: {path_value}")
            
            logger.info("HDFS 目录结构初始化完成")
            
        except Exception as e:
            logger.error(f"HDFS 目录初始化失败: {str(e)}")
    
    def exists(self, hdfs_path):
        """
        检查路径是否存在
        
        Args:
            hdfs_path: HDFS 路径
            
        Returns:
            是否存在
        """
        if not self.client:
            return False
        
        try:
            self.client.status(hdfs_path, strict=False)
            return True
        except:
            return False
    
    def mkdir(self, hdfs_path, permission=None):
        """
        创建目录
        
        Args:
            hdfs_path: HDFS 路径
            permission: 权限（如 '755'）
            
        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return False
        
        try:
            self.client.makedirs(hdfs_path, permission=permission)
            logger.info(f"创建 HDFS 目录成功: {hdfs_path}")
            return True
        except Exception as e:
            logger.error(f"创建 HDFS 目录失败: {hdfs_path}, 错误: {str(e)}")
            return False
    
    def upload_file(self, local_path, hdfs_path, overwrite=False):
        """
        上传文件到 HDFS
        
        Args:
            local_path: 本地文件路径
            hdfs_path: HDFS 目标路径
            overwrite: 是否覆盖
            
        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接，文件将保存在本地")
            return False
        
        try:
            self.client.upload(
                hdfs_path, 
                local_path, 
                overwrite=overwrite,
                replication=self.hdfs_config['replication']
            )
            
            logger.info(f"上传文件成功: {local_path} -> {hdfs_path}")
            return True
            
        except Exception as e:
            logger.error(f"上传文件失败: {str(e)}")
            return False
    
    def download_file(self, hdfs_path, local_path, overwrite=False):
        """
        从 HDFS 下载文件
        
        Args:
            hdfs_path: HDFS 文件路径
            local_path: 本地目标路径
            overwrite: 是否覆盖
            
        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return False
        
        try:
            self.client.download(hdfs_path, local_path, overwrite=overwrite)
            logger.info(f"下载文件成功: {hdfs_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"下载文件失败: {str(e)}")
            return False
    
    def write_json(self, data, hdfs_path, overwrite=False):
        """
        写入 JSON 数据到 HDFS
        
        Args:
            data: 要写入的数据（字典或列表）
            hdfs_path: HDFS 路径
            overwrite: 是否覆盖
            
        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return False
        
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            
            self.client.write(
                hdfs_path, 
                json_str.encode('utf-8'), 
                overwrite=overwrite
            )
            
            logger.info(f"写入 JSON 成功: {hdfs_path}")
            return True
            
        except Exception as e:
            logger.error(f"写入 JSON 失败: {str(e)}")
            return False
    
    def read_json(self, hdfs_path):
        """
        从 HDFS 读取 JSON 数据
        
        Args:
            hdfs_path: HDFS 路径
            
        Returns:
            解析后的数据
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return None
        
        try:
            with self.client.read(hdfs_path, encoding='utf-8') as reader:
                data = json.load(reader)
            
            logger.info(f"读取 JSON 成功: {hdfs_path}")
            return data
            
        except Exception as e:
            logger.error(f"读取 JSON 失败: {str(e)}")
            return None
    
    def list_dir(self, hdfs_path):
        """
        列出目录内容
        
        Args:
            hdfs_path: HDFS 目录路径
            
        Returns:
            文件列表
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return []
        
        try:
            files = self.client.list(hdfs_path)
            return files
        except Exception as e:
            logger.error(f"列出目录失败: {str(e)}")
            return []
    
    def delete(self, hdfs_path, recursive=False):
        """
        删除文件或目录
        
        Args:
            hdfs_path: HDFS 路径
            recursive: 是否递归删除
            
        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return False
        
        try:
            self.client.delete(hdfs_path, recursive=recursive)
            logger.info(f"删除成功: {hdfs_path}")
            return True
        except Exception as e:
            logger.error(f"删除失败: {str(e)}")
            return False
    
    def get_file_status(self, hdfs_path):
        """
        获取文件状态信息
        
        Args:
            hdfs_path: HDFS 路径
            
        Returns:
            文件状态字典
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return None
        
        try:
            status = self.client.status(hdfs_path)
            return status
        except Exception as e:
            logger.error(f"获取文件状态失败: {str(e)}")
            return None
    
    def save_weather_data_batch(self, data_list, date_str=None):
        """
        批量保存天气数据到 HDFS（按日期分区）
        
        Args:
            data_list: 数据列表
            date_str: 日期字符串（YYYY-MM-DD）
            
        Returns:
            是否成功
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 构建路径：/weather/processed/YYYY/MM/DD/data.json
        year, month, day = date_str.split('-')
        hdfs_path = f"{self.paths['processed_data']}/{year}/{month}/{day}/weather_{datetime.now().strftime('%H%M%S')}.json"
        
        return self.write_json(data_list, hdfs_path, overwrite=True)
    
    def get_capacity_info(self):
        """
        获取 HDFS 容量信息
        
        Returns:
            容量信息字典
        """
        if not self.client:
            logger.warning("HDFS 客户端未连接")
            return None
        
        try:
            status = self.client.status('/')
            return {
                'total': status.get('capacity', 0),
                'used': status.get('used', 0),
                'remaining': status.get('remaining', 0)
            }
        except Exception as e:
            logger.error(f"获取容量信息失败: {str(e)}")
            return None


# 全局 HDFS 管理器实例
hdfs_manager = None


def get_hdfs_manager(config_path=None):
    """
    获取 HDFS 管理器实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        HDFSManager 实例
    """
    global hdfs_manager
    
    if hdfs_manager is None:
        hdfs_manager = HDFSManager(config_path)
    
    return hdfs_manager


if __name__ == "__main__":
    """测试 HDFS 管理器"""
    
    # 配置日志
    logger.add(
        "../logs/hdfs_manager.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )
    
    print("="*60)
    print("  HDFS 管理器测试")
    print("="*60)
    
    # 创建管理器
    manager = HDFSManager()
    
    if manager.client:
        print("\n✅ HDFS 连接成功")
        
        # 测试写入 JSON
        print("\n测试写入 JSON 数据...")
        test_data = {
            'station_id': 'test_001',
            'temperature': 25.5,
            'humidity': 60,
            'timestamp': datetime.now().isoformat()
        }
        
        test_path = f"{manager.paths['raw_data']}/test.json"
        if manager.write_json(test_data, test_path, overwrite=True):
            print(f"✅ 写入成功: {test_path}")
            
            # 读取验证
            read_data = manager.read_json(test_path)
            if read_data:
                print(f"✅ 读取成功: {read_data}")
            
            # 删除测试文件
            manager.delete(test_path)
            print("✅ 删除测试文件")
        
        # 获取容量信息
        capacity = manager.get_capacity_info()
        if capacity:
            print(f"\n📊 HDFS 容量信息:")
            print(f"  总容量: {capacity['total'] / (1024**3):.2f} GB")
            print(f"  已使用: {capacity['used'] / (1024**3):.2f} GB")
            print(f"  剩余: {capacity['remaining'] / (1024**3):.2f} GB")
    else:
        print("\n⚠️  HDFS 未连接（这是正常的，如果还未安装 Hadoop）")
        print("提示：系统将使用本地文件存储作为替代方案")
    
    print("\n✅ HDFS 管理器测试完成")


