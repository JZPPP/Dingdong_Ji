# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhMTk3MGRlNWQ0NzQ0Njc0YmEzNGNiNmQzYTUwOTNkMCIsImlhdCI6MTczMjMyMzM3OSwiZXhwIjoyMDQ3NjgzMzc5fQ.JPdVcYlb8bd-fjmsa2HRrHQTTPuUBC0YPV1K7CIJYX8

# curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhMTk3MGRlNWQ0NzQ0Njc0YmEzNGNiNmQzYTUwOTNkMCIsImlhdCI6MTczMjMyMzM3OSwiZXhwIjoyMDQ3NjgzMzc5fQ.JPdVcYlb8bd-fjmsa2HRrHQTTPuUBC0YPV1K7CIJYX8" -H "Content-Type: application/json" -d '{"entity_id": "d2e6e00a725c9b1d81c4eb5e9dcb7cd8"}' http://192.168.50.5:8123/api/services/switch/turn_off

import requests
import json
import time
from typing import Dict, Optional
from pathlib import Path

class HomeAssistantAPI:
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        ha_config = self.config.get('HomeAssistant', {})
        
        # 从配置文件加载 Home Assistant 配置
        self.base_url = ha_config.get('BaseUrl', 'http://192.168.50.5:8123')
        self.token = ha_config.get('Token')
        self.device_id = ha_config.get('DeviceId')
        
        if not all([self.base_url, self.token, self.device_id]):
            raise ValueError("Home Assistant 配置不完整，请检查config.json")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"无法加载配置文件: {str(e)}")

    def _make_request(self, endpoint: str, method: str = 'POST', data: Optional[Dict] = None) -> Dict:
        """发送请求到 Home Assistant"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=10  # 10秒超时
            )
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            raise TimeoutError("请求超时，请检查网络连接")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"请求失败: {str(e)}")

    def turn_off_device(self) -> bool:
        """关闭设备"""
        try:
            data = {"device_id": self.device_id}
            self._make_request("services/switch/turn_off", data=data)
            return True
        except Exception as e:
            raise Exception(f"关闭设备失败: {str(e)}")

def close_PC(delay: int = 0) -> bool:
    """
    关闭PC
    :param delay: 延迟关机时间（秒）
    :return: 是否成功发送关机命令
    """
    try:
        # 创建 Home Assistant API 实例
        ha = HomeAssistantAPI()
        
        # 如果有延迟，等待指定时间
        if delay > 0:
            time.sleep(delay)
        
        # 发送关机命令
        return ha.turn_off_device()
        
    except Exception as e:
        print(f"关机操作失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试关机功能
    try:
        print("正在发送关机命令...")
        if close_PC():
            print("关机命令发送成功！")
        else:
            print("关机命令发送失败！")
    except Exception as e:
        print(f"发生错误: {str(e)}")

