import subprocess
import queue
import time
import json
from pathlib import Path
from queue import Queue
from datetime import datetime, timedelta
import colorama
from colorama import Fore, Back, Style
from wxpush import Logger, send_game_start, send_game_end, send_game_warning, send_summary, send_wechat
import shutdown
import psutil  # 需要安装：pip install psutil

# 初始化colorama
colorama.init(autoreset=True)

class GameProcess:
    def __init__(self, name, process, start_time):
        self.name = name
        self.process = process
        self.start_time = start_time
        self.end_time = None
        self.duration = None
        self.timeout = False  # 添加超时标记

    def check_timeout(self, timeout_minutes):
        """检查是否超时"""
        current_time = datetime.now()
        return (current_time - self.start_time).total_seconds() > timeout_minutes * 60

    def kill(self):
        """强制结束进程及其子进程"""
        try:
            parent = psutil.Process(self.process.pid)
            children = parent.children(recursive=True)
            
            # 先结束子进程
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # 结束主进程
            self.process.terminate()
            
            # 等待进程结束
            self.process.wait(timeout=5)
            
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            # 如果进程仍然存在，强制结束
            try:
                self.process.kill()
            except:
                pass
        
        self.timeout = True

    def mark_completed(self):
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time
        status = "超时结束" if self.timeout else "正常完成"
        return {
            "游戏名称": self.name,
            "开始时间": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "运行时长": str(self.duration).split('.')[0],
            "结束状态": status
        }

class GameManager:
    def __init__(self, config_path='config.json'):
        Logger.info("正在初始化游戏管理器...")
        self.program_queue = queue.Queue()
        self.current_processes = []
        self.process_history = []
        self.emu_queue = Queue()
        self.pc_queue = Queue()
        self.config = self._load_config(config_path)
        self.start_time = None
        
        self.MAX_CONCURRENT = self.config.get('Settings', {}).get('MaxConcurrent', 1)
        Logger.info(f"最大并发数设置为：{self.MAX_CONCURRENT}")
        
        # OBS命令设置
        obs_path = Path(self.config['OBSPath'])
        self.obs_start = f'start /d "{obs_path.parent}" {obs_path.name} --startrecording --disable-shutdown-check --minimize-to-tray'
        self.obs_kill = f'taskkill /f /t /im {obs_path.name}'

        self.all_queues_empty = False  # 添加标志来追踪队列状态
        settings = self.config.get('Settings', {})
        self.default_max_time = 60  # 默认最大运行时间（分钟）
        self.default_min_time = 3   # 默认最短运行时间（分钟）
        self.auto_shutdown = settings.get('AutoShutdown', False)
        self.shutdown_delay = settings.get('ShutdownDelay', 60)
        
        # 通知控制参数
        self.start_notice = settings.get('StartNotice', True)
        self.end_notice = settings.get('EndNotice', True)
        self.warn_notice = settings.get('WarnNotice', True)
        self.summary_notice = settings.get('SummaryNotice', True)
        
        # 设置日志开关
        log_enabled = settings.get('Log', True)
        Logger.set_log_enabled(log_enabled)
        
        Logger.info(f"默认超时时间设置为：{self.default_max_time} 分钟")
        Logger.info(f"默认最短时间设置为：{self.default_min_time} 分钟")
        Logger.info(f"通知设置 - 启动:{self.start_notice}, 结束:{self.end_notice}, 警告:{self.warn_notice}, 总结:{self.summary_notice}")
        Logger.info(f"日志记录：{'启用' if log_enabled else '禁用'}")
        if self.auto_shutdown:
            Logger.info(f"已启用自动关机，将在任务完成后 {self.shutdown_delay} 秒后关机")

    def _load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 确保 Settings 部分存在
            if 'Settings' not in config:
                config['Settings'] = {'MaxConcurrent': 1}
            return config

    def initialize_queues(self):
        """初始化游戏队列"""
        Logger.info("正在初始化游戏队列...")
        emu_count = 0
        pc_count = 0

        for game_name, game_info in self.config['Games'].items():
            exec_path = game_info['ExecPath']
            game_type = game_info['Type']
            max_time = game_info.get('MaxTime', self.default_max_time)
            min_time = game_info.get('MinTime', self.default_min_time)

            if game_type == 'EMU':
                self.emu_queue.put((game_name, Path(exec_path).parent, str(exec_path), game_type, max_time, min_time))
                emu_count += 1
            elif game_type == 'PC':
                self.pc_queue.put((game_name, Path(exec_path).parent, str(exec_path), game_type, max_time, min_time))
                pc_count += 1
            else:
                Logger.warning(f"未知游戏类型: {game_type}（{game_name}）")

        Logger.info(f"EMU类型：{emu_count} 个")
        Logger.info(f"PC类型：{pc_count} 个")

    def start_obs_if_needed(self):
        if self.config["OBSRecord"]:
            send_wechat("OBS录制开始")
            subprocess.run(self.obs_start, shell=True, capture_output=True, text=True)
            time.sleep(5)

    def process_emu_games(self):
        """处理 EMU 类型游戏"""
        Logger.info("开始处理 EMU 类型游戏...")
        while not self.emu_queue.empty() or self.current_processes:  # 修改循环条件
            if len(self.current_processes) < self.MAX_CONCURRENT and not self.emu_queue.empty():
                game_name, work_dir, exec_path, game_type, max_time, min_time = self.emu_queue.get()
                self._launch_game(game_name, work_dir, exec_path, game_type, max_time, min_time)
                
            self._check_processes()
            time.sleep(10)

        Logger.info("EMU类型游戏处理完成")

    def process_pc_games(self):
        """处理 PC 类型游戏"""
        if not self.pc_queue.empty():
            Logger.info("开始处理 PC 类型游戏...")
            
        while not self.pc_queue.empty() or self.current_processes:  # 修改循环条件
            if len(self.current_processes) < 1 and not self.pc_queue.empty():
                game_name, work_dir, exec_path, game_type, max_time, min_time = self.pc_queue.get()
                self._launch_game(game_name, work_dir, exec_path, game_type, max_time, min_time)
            
            self._check_processes()
            time.sleep(10)

        if self.pc_queue.empty() and not self.current_processes:
            Logger.info("PC类型游戏处理完成")
            self.all_queues_empty = True

    def _launch_game(self, game_name, work_dir, exec_path, game_type, max_time, min_time):
        """启动游戏进程"""
        try:
            process = subprocess.Popen(exec_path, shell=True, cwd=str(work_dir))
            start_time = datetime.now()
            
            if self.start_time is None:
                self.start_time = start_time
                Logger.info("开始运行首个游戏")
                
            game_process = GameProcess(game_name, process, start_time)
            game_process.max_time = max_time  # 新增属性
            game_process.min_time = min_time  # 新增属性
            self.current_processes.append(game_process)
            
            # 根据设置决定是否发送启动通知
            if self.start_notice:
                send_game_start(game_name, exec_path)
            Logger.info(f"当前运行中：{len(self.current_processes)} 个游戏")
            
        except Exception as e:
            Logger.error(f"启动游戏 {game_name} 失败: {str(e)}", push=True)

    def _check_processes(self):
        """检查进程状态"""
        for game_process in self.current_processes[:]:
            # 检查是否超时
            max_time = getattr(game_process, 'max_time', self.default_max_time)
            if game_process.check_timeout(max_time):
                Logger.warning(f"游戏 {game_process.name} 运行超过 {max_time} 分钟，准备强制结束")
                game_process.kill()
                process_info = game_process.mark_completed()
                self.process_history.append(process_info)
                self.current_processes.remove(game_process)
                
                # 根据设置决定是否发送警告通知
                if self.warn_notice:
                    send_game_warning("long_time", game_process.name, f"游戏运行时间过长：{max_time}分钟，已强制结束")
                # 根据设置决定是否发送结束通知
                if self.end_notice:
                    send_game_end(process_info)
                Logger.warning(f"已强制结束游戏：{game_process.name}")
                continue

            # 检查是否自然结束
            if game_process.process.poll() is not None:
                process_info = game_process.mark_completed()
                
                # 检查是否小于最短运行时间
                min_time = getattr(game_process, 'min_time', self.default_min_time)
                duration_minutes = game_process.duration.total_seconds() / 60
                if duration_minutes < min_time:
                    short_time_msg = f"运行时间过短：{duration_minutes:.1f}分钟，小于设定的最短时间{min_time}分钟"
                    Logger.warning(f"游戏 {game_process.name} {short_time_msg}")
                    # 根据设置决定是否发送警告通知
                    if self.warn_notice:
                        send_game_warning("short_time", game_process.name, short_time_msg)
                
                self.process_history.append(process_info)
                self.current_processes.remove(game_process)
                
                # 根据设置决定是否发送结束通知
                if self.end_notice:
                    send_game_end(process_info)
                Logger.info(f"当前运行中：{len(self.current_processes)} 个游戏")

    def cleanup(self):
        """清理和生成报告"""
        # 等待所有进程完成
        while self.current_processes:
            Logger.info("等待剩余游戏结束...")
            self._check_processes()
            time.sleep(10)

        Logger.info("开始清理工作...")
        
        if self.config["OBSRecord"]:
            subprocess.run(self.obs_kill, shell=True, capture_output=True, text=True)
            Logger.info("OBS录制已停止")
        
        if self.start_time:
            end_time = datetime.now()
            total_duration = end_time - self.start_time
            
            Logger.success("所有任务完成！")
            Logger.info(f"总用时：{str(total_duration).split('.')[0]}")
            
            summary_data = {
                "总体开始时间": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "总体结束时间": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "总耗时": str(total_duration).split('.')[0],
                "游戏列表": self.process_history
            }
            
            # 根据设置决定是否发送总结通知
            if self.summary_notice:
                send_summary(summary_data)
            
            # 处理自动关机
            if self.auto_shutdown:
                self._handle_shutdown()

    def _handle_shutdown(self):
        """处理关机流程"""
        if self.shutdown_delay > 0:
            shutdown_msg = f"系统将在 {self.shutdown_delay} 秒后关机"
            Logger.warning(shutdown_msg, push=True)
            
            # 倒计时显示
            for remaining in range(self.shutdown_delay, 0, -1):
                if remaining % 10 == 0 or remaining <= 5:  # 每10秒显示一次，最后5秒每秒显示
                    Logger.warning(f"距离关机还有 {remaining} 秒")
                time.sleep(1)
        
        try:
            Logger.warning("正在执行关机...", push=True)
            shutdown.close_PC()
        except Exception as e:
            error_msg = f"关机失败: {str(e)}"
            Logger.error(error_msg, push=True)

def main():
    try:
        manager = GameManager()
        manager.initialize_queues()
        time.sleep(3)
        
        if manager.auto_shutdown:
            # 如果启用了自动关机，先发送通知
            send_wechat("已启用自动关机，任务完成后系统将自动关机")
        
        manager.start_obs_if_needed()
        manager.process_emu_games()
        manager.process_pc_games()
        manager.cleanup()

        if not manager.auto_shutdown:
            # 如果没有启用自动关机，等待用户手动关闭
            Logger.success("程序执行完成！按任意键退出...")
            input()
    except Exception as e:
        Logger.error(f"程序执行出错: {str(e)}")
        Logger.error("按任意键退出...")
        input()

if __name__ == "__main__":
    main()


