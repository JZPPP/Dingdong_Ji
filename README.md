# 叮咚鸡 🎮![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
[![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-100-orange.svg)]()

> 一个强大的游戏脚本自动化管理工具，支持多游戏脚本队列管理、智能时间控制、微信通知和自动关机功能。

## ✨ 功能特点

- 🎯 **多游戏队列管理** - 支持EMU和PC两种类型的游戏自动化
- ⏱️ **智能时间控制** - 每个游戏可单独设置最大/最短运行时间
- 📱 **分类微信通知** - 启动、结束、警告、总结四种通知类型
- 💻 **自动关机支持** - 任务完成后可自动关机
- 📊 **本地日志记录** - 按日期生成详细运行日志
- ⚡ **进程超时控制** - 防止游戏卡死或异常运行
- 🎥 **OBS录制集成** - 支持自动开始/停止录制
- 🔄 **并发控制** - EMU类型支持并发，PC类型串行执行

## 🚀 快速开始


### 环境要求

- Python 3.8高版本
- Windows 操作系统
- 企业微信（用于通知功能）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/Dingdong_Ji.git
cd Dingdong_Ji
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置设置**
编辑 `config.json` 文件，配置您的游戏和通知设置。

4. **运行程序的三种方法**
- 1.直接运行EXE文件
- 2.配置好依赖后运行build_exe.bat自行编译exe
- 3.配置好依赖后运行run_queue_game.bat运行脚本
- 4.配置好依赖后```python queueGame.py```运行脚本

## 📋 配置说明

### 基础配置 (config.json)

```json
{
    "Settings": {
        "MaxConcurrent": 1,        // 最大并发运行数
        "TimeoutMinutes": 5,       // 单个游戏超时时间（分钟）
        "AutoShutdown": false,     // 是否自动关机
        "ShutdownDelay": 60,       // 关机等待时间（秒）
        "Log": true,            // 是否启用本地日志记录
        "StartNotice": true,      // 是否发送游戏启动通知
        "EndNotice": true,        // 是否发送游戏结束通知
        "WarnNotice": true,      // 是否发送游戏警告通知
        "SummaryNotice": true    // 是否发送总结报告通知
    },
    "OBSRecord": false,            // 是否启用 OBS 录制
    "OBSPath": "C:/Program Files/obs-studio/bin/64bit/obs64.exe", // OBS 路径
    "MUMUPath": "D:/MuMu Player 12/shell/MuMuManager.exe", // MUMU模拟器路径，实现模拟器排序（已弃用）
    "WxPush": { // 企业微信通知
        "Secret": "your-secret",
        "CorpId": "your-corpid",
        "AgentId": 1000003, // your-AgentId
        "ToParty": "1" // 全体发送
    },
    "HomeAssistant": { // 利用HomeAssistant实现自动关机，如开机卡/智能插座
        "BaseUrl": "http://your-ha-server:8123",
        "Token": "your-long-lived-access-token",
        "DeviceId": "your-device-id"
    },
    "Games": {   
        "游戏1": {
            "ExecPath": "D:/Games/Game1/game.exe", //脚本路径
            "Type": "EMU", //脚本类型
            "MaxTime": 30,         // 最大运行时间（分钟）
            "MinTime": 5           // 最短运行时间（分钟）
        },
        "游戏2": {
            "ExecPath": "D:/Games/Game2/game.exe",
            "Type": "PC", //脚本类型
            "MaxTime": 20,         // 最大运行时间（分钟）
            "MinTime": 3           // 最短运行时间（分钟）
        }
    }
}
```

**参数说明：**
- `MaxConcurrent`: 最大并发运行数（默认：1）
- `AutoShutdown`: 是否自动关机（默认：false）
- `ShutdownDelay`: 关机等待时间（默认：60秒）
- `Log`: 是否启用本地日志记录（默认：true）
- `Type`: EMU是游戏在模拟器运行，PC是游戏在PC运行
- `MaxTime`: 游戏最大运行时间（分钟），超过此时间将强制结束游戏
- `MinTime`: 游戏最短运行时间（分钟），少于此时间将发送警告通知
- 如果不配置这些参数，将使用程序默认值（MaxTime:60，MinTime: 1分钟）

**通知控制参数：**
- `StartNotice`: 是否发送游戏启动通知（默认：true）
- `EndNotice`: 是否发送游戏结束通知（默认：true）
- `WarnNotice`: 是否发送游戏警告通知（默认：true）
- `SummaryNotice`: 是否发送总结报告通知（默认：true）

**日志参数：**
- `Log`: 是否启用本地日志记录（默认：true）
  - 启用时会在程序目录下的 `Log` 文件夹中生成日志文件
  - 日志文件按日期命名，格式为 `YYYY-MM-DD.log`
  - 包含所有程序运行信息、警告和错误日志

## 🔧 使用说明

### 运行模式

- **EMU模式**：适用于模拟器中的游戏自动化
  - 支持并发运行多个游戏
  - 适用于Android模拟器中的游戏
- **PC模式**：适用于PC端桌面游戏的自动化
  - 串行运行，避免资源冲突
  - 适用于Windows桌面游戏

### 微信通知分类

#### 🎮 游戏启动通知
- 游戏名称、启动时间、执行路径
- 可通过 `StartNotice` 参数控制是否发送

#### 🏁 游戏结束通知  
- 游戏名称、开始/结束时间、运行时长、结束状态
- 可通过 `EndNotice` 参数控制是否发送

#### ⚠️ 游戏警告通知
- **⏰ 运行时间过短警告**：游戏运行时间小于设定的最短时间
- **⏳ 运行时间过长警告**：游戏运行时间超过设定的最大时间，已强制结束
- **❌ 运行异常警告**：游戏启动失败或其他异常情况
- 可通过 `WarnNotice` 参数控制是否发送

#### 📊 总结报告通知
- 总体统计信息（开始时间、结束时间、总耗时）
- 每个游戏的详细运行记录
- 可通过 `SummaryNotice` 参数控制是否发送

### 状态监控

程序运行时会显示：
- 当前运行状态
- 游戏执行时间
- 错误信息
- 完成进度



### 日志文件格式示例
```
[INFO]22401510300 - 正在初始化游戏管理器...
[INFO]22401150:30:01 - 最大并发数设置为：1
[INFO]22401-1510:30:2 - 默认超时时间设置为：60 分钟
[INFO]22401510:30:03正在初始化游戏队列...
[INFO]224011510:304 开始处理 EMU 类型游戏...
[WARN]22401-15 1035:00 - 游戏 1999运行时间过短：0.5于设定的最短时间5分钟
[SUCCESS]2240115110 - 所有任务完成！
```

## 🛠️ 高级功能

1. 首次使用请正确配置 `config.json`
2. 确保所有游戏路径正确
3. 建议先使用小规模测试
4. 请勿修改运行中的配置文件

## 常见问题

 **有问题自己折腾吧谢谢**



## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目！



## 📝 更新日志

### v1.00 (2024-1005)
- ✨ 初始版本发布
- 🎯 基础游戏队列管理功能
- 📱 微信推送通知集成
- 💻 自动关机支持
- 📊 本地日志记录
- ⏱️ 智能时间控制
- 🔄 并发控制优化

## 📄 许可证

本项目采用 MIT 许可证 - 查看 LICENSE](LICENSE) 文件了解详情

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

- 项目主页：[https://github.com/your-username/Dingdong_Ji](https://github.com/your-username/Dingdong_Ji)
- 问题反馈：[Issues](https://github.com/your-username/Dingdong_Ji/issues)
- 邮箱：your-email@example.com

## ⭐ 如果这个项目对您有帮助，请给它一个星标！

---

**注意**：使用本工具时请遵守相关游戏的使用条款和法律法规。 
