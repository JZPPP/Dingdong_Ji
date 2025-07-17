import requests
import urllib3
import json
from datetime import datetime
from typing import Dict, Any, Optional
import colorama
from colorama import Fore, Back, Style
import os
from pathlib import Path
urllib3.disable_warnings()

# 初始化彩色输出
colorama.init(autoreset=True)

def initialize_wx_push():
    """初始化微信推送服务"""
    try:
        push_instance = WxPushMessage()
        Logger.info("微信推送服务初始化成功")
        return push_instance
    except Exception as e:
        Logger.error(f"初始化微信推送失败: {str(e)}")
        return None

class Logger:
    _log_enabled = True
    _log_dir = "Log"
    
    @classmethod
    def set_log_enabled(cls, enabled: bool):
        """设置日志开关"""
        cls._log_enabled = enabled
        if enabled:
            # 确保日志目录存在
            os.makedirs(cls._log_dir, exist_ok=True)
    
    @classmethod
    def write_to_file(cls, message: str):
        """写入日志到文件"""
        if not cls._log_enabled:
            return
            
        try:
            # 生成当天的日志文件名
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = Path(cls._log_dir) / f"{today}.log"
            
            # 写入日志文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{message}\n")
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")
    
    @staticmethod
    def info(message: str, push: bool = False):
        """信息日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console_msg = f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {timestamp} - {message}"
        log_msg = f"[INFO] {timestamp} - {message}"
        print(console_msg)
        Logger.write_to_file(log_msg)
        if push and wx_push:
            wx_push.send_message(message)

    @staticmethod
    def warning(message: str, push: bool = False):
        """警告日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console_msg = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {timestamp} - {message}"
        log_msg = f"[WARN] {timestamp} - {message}"
        print(console_msg)
        Logger.write_to_file(log_msg)
        if push and wx_push:
            wx_push.send_message(f"【警告】\n{message}")

    @staticmethod
    def error(message: str, push: bool = False):
        """错误日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console_msg = f"{Fore.RED}[ERROR]{Style.RESET_ALL} {timestamp} - {message}"
        log_msg = f"[ERROR] {timestamp} - {message}"
        print(console_msg)
        Logger.write_to_file(log_msg)
        if push and wx_push:
            wx_push.send_message(f"【错误】\n{message}")

    @staticmethod
    def success(message: str, push: bool = False):
        """成功日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console_msg = f"{Fore.BLUE}[SUCCESS]{Style.RESET_ALL} {timestamp} - {message}"
        log_msg = f"[SUCCESS] {timestamp} - {message}"
        print(console_msg)
        Logger.write_to_file(log_msg)
        if push and wx_push:
            wx_push.send_message(message)

class WxPushMessage:
    def __init__(self, config_path='config.json'):
        self.config = self._load_config(config_path)
        wx_config = self.config.get('WxPush', {})
        
        # 从配置文件加载微信推送配置
        self.secret = wx_config.get('Secret')
        self.corpid = wx_config.get('CorpId')
        self.agentid = wx_config.get('AgentId')
        self.toparty = wx_config.get('ToParty')
        
        if not all([self.secret, self.corpid, self.agentid, self.toparty]):
            raise ValueError("微信推送配置不完整，请检查config.json文件")
        
        self._access_token = None
        self._token_expires = 0

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"无法加载配置文件: {str(e)}")

    def _get_access_token(self) -> str:
        """获取access_token，包含缓存机制"""
        current_time = datetime.now().timestamp()
        if self._access_token and current_time < self._token_expires:
            return self._access_token

        url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.secret}'
        response = requests.get(url, verify=False).json()
        
        if response.get('errcode') != 0:
            raise Exception(f"获取access_token失败: {response.get('errmsg')}")
        
        self._access_token = response.get('access_token')
        self._token_expires = current_time + response.get('expires_in', 7200) - 300  # 提前5分钟过期
        return self._access_token

    def send_message(self, content: str, msg_type: str = "text") -> Optional[Dict]:
        """
        发送消息
        :param content: 消息内容
        :param msg_type: 消息类型
        :return: 发送结果
        """
        try:
            data = {
                "toparty": self.toparty,
                "msgtype": msg_type,
                "agentid": self.agentid,
                "text": {"content": content},
                "safe": 0
            }

            access_token = self._get_access_token()
            response = requests.post(
                url=f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}",
                verify=False,
                json=data
            ).json()

            if response.get('errcode') != 0:
                print(f"发送消息失败: {response.get('errmsg')}")
            return response
        except Exception as e:
            print(f"发送消息时发生错误: {str(e)}")
            return None

    def _format_game_end_message(self, process_info: Dict) -> str:
        """格式化游戏结束消息"""
        status_icon = "⚠️" if process_info.get('结束状态') == "超时结束" else "✅"
        return (
            "【游戏结束通知】\n"
            "---------------\n"
            f"游戏：{process_info['游戏名称']}\n"
            f"开始：{process_info['开始时间']}\n"
            f"结束：{process_info['结束时间']}\n"
            f"用时：{process_info['运行时长']}\n"
            f"状态：{status_icon} {process_info.get('结束状态', '正常完成')}"
        )

    def _format_summary_message(self, summary_data: Dict) -> str:
        """格式化总结报告"""
        content = (
            "【日常任务完成报告】\n"
            "=================\n"
            "■ 总体统计\n"
            f"开始：{summary_data['总体开始时间']}\n"
            f"结束：{summary_data['总体结束时间']}\n"
            f"总耗时：{summary_data['总耗时']}\n\n"
            "■ 游戏详情\n"
        )
        
        for game in summary_data['游戏列表']:
            status_icon = "⚠️" if game.get('结束状态') == "超时结束" else "✅"
            content += (
                "---------------\n"
                f"游戏：{game['游戏名称']}\n"
                f"  开始：{game['开始时间']}\n"
                f"  结束：{game['结束时间']}\n"
                f"  用时：{game['运行时长']}\n"
                f"  状态：{status_icon} {game.get('结束状态', '正常完成')}\n"
            )
        
        return content

# 创建全局实例
wx_push = initialize_wx_push()

def format_duration(seconds: int) -> str:
    """格式化持续时间"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_game_start_message(game_name: str, exec_path: str) -> str:
    """格式化游戏启动消息"""
    return (
        "🎮【游戏启动通知】\n"
        "=================\n"
        f"游戏：{game_name}\n"
        f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"路径：{exec_path}"
    )

def format_game_end_message(process_info: Dict) -> str:
    """格式化游戏结束消息"""
    status_icon = "⚠️" if process_info.get('结束状态') == "超时结束" else "✅"
    return (
        "🏁【游戏结束通知】\n"
        "=================\n"
        f"游戏：{process_info['游戏名称']}\n"
        f"开始：{process_info['开始时间']}\n"
        f"结束：{process_info['结束时间']}\n"
        f"用时：{process_info['运行时长']}\n"
        f"状态：{status_icon} {process_info.get('结束状态', '正常完成')}"
    )

def format_game_warning_message(warning_type: str, game_name: str, details: str) -> str:
    """格式化游戏警告消息"""
    warning_icons = {
        "short_time": "⏰",
        "long_time": "⏳",
        "error": "❌",
        "other": "⚠️"
    }
    icon = warning_icons.get(warning_type, "⚠️")
    return (
        f"{icon}【游戏警告通知】\n"
        "=================\n"
        f"游戏：{game_name}\n"
        f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"警告：{details}"
    )

def format_summary_message(summary_data: Dict) -> str:
    """格式化总结报告"""
    content = (
        "📊【日常任务完成报告】\n"
        "===================\n"
        "■ 总体统计\n"
        f"开始：{summary_data['总体开始时间']}\n"
        f"结束：{summary_data['总体结束时间']}\n"
        f"总耗时：{summary_data['总耗时']}\n\n"
        "■ 游戏详情\n"
    )
    
    for game in summary_data['游戏列表']:
        status_icon = "⚠️" if game.get('结束状态') == "超时结束" else "✅"
        content += (
            "---------------\n"
            f"游戏：{game['游戏名称']}\n"
            f"  开始：{game['开始时间']}\n"
            f"  结束：{game['结束时间']}\n"
            f"  用时：{game['运行时长']}\n"
            f"  状态：{status_icon} {game.get('结束状态', '正常完成')}\n"
        )
    
    return content

def send_game_start(game_name: str, exec_path: str) -> Optional[Dict]:
    """发送游戏启动通知"""
    if not wx_push:
        return None
    content = format_game_start_message(game_name, exec_path)
    return wx_push.send_message(content)

def send_game_end(process_info: Dict) -> Optional[Dict]:
    """发送游戏结束通知"""
    if not wx_push:
        return None
    content = format_game_end_message(process_info)
    return wx_push.send_message(content)

def send_game_warning(warning_type: str, game_name: str, details: str) -> Optional[Dict]:
    """发送游戏警告通知"""
    if not wx_push:
        return None
    content = format_game_warning_message(warning_type, game_name, details)
    return wx_push.send_message(content)

def send_summary(summary_data: Dict) -> Optional[Dict]:
    """发送总结报告"""
    if not wx_push:
        return None
    content = format_summary_message(summary_data)
    return wx_push.send_message(content)

def send_wechat(content: str) -> Optional[Dict]:
    """简单发送接口，用于向后兼容"""
    if not wx_push:
        return None
    return wx_push.send_message(f"【系统通知】\n---------------\n{content}")

# 向后兼容的函数（保持原有接口）
def format_game_end_message_old(process_info: Dict) -> str:
    """格式化游戏结束消息（旧版本，向后兼容）"""
    status_icon = "⚠️" if process_info.get('结束状态') == "超时结束" else "✅"
    return (
        "【游戏结束通知】\n"
        "---------------\n"
        f"游戏：{process_info['游戏名称']}\n"
        f"开始：{process_info['开始时间']}\n"
        f"结束：{process_info['结束时间']}\n"
        f"用时：{process_info['运行时长']}\n"
        f"状态：{status_icon} {process_info.get('结束状态', '正常完成')}"
    )

def format_summary_message_old(summary_data: Dict) -> str:
    """格式化总结报告（旧版本，向后兼容）"""
    content = (
        "【日常任务完成报告】\n"
        "=================\n"
        "■ 总体统计\n"
        f"开始：{summary_data['总体开始时间']}\n"
        f"结束：{summary_data['总体结束时间']}\n"
        f"总耗时：{summary_data['总耗时']}\n\n"
        "■ 游戏详情\n"
    )
    
    for game in summary_data['游戏列表']:
        status_icon = "⚠️" if game.get('结束状态') == "超时结束" else "✅"
        content += (
            "---------------\n"
            f"游戏：{game['游戏名称']}\n"
            f"  开始：{game['开始时间']}\n"
            f"  结束：{game['结束时间']}\n"
            f"  用时：{game['运行时长']}\n"
            f"  状态：{status_icon} {game.get('结束状态', '正常完成')}\n"
        )
    
    return content
