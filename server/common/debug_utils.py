# common/debug_utils.py
import os
from dotenv import load_dotenv
from core.logger import logger
from typing import Any, Optional
import functools

# 直接在这里加载环境变量，避免导入问题
load_dotenv()

class ColoredConsole:
    """简化的控制台颜色工具类"""
    
    # ANSI 颜色代码
    COLORS = {
        'reset': '\033[0m',
        'gray': '\033[90m',        # 浅灰色
        'light_gray': '\033[37m',  # 更浅的灰色
        'dim': '\033[2m',         # 暗淡效果
        'green': '\033[32m',
        'red': '\033[31m',
        'yellow': '\033[33m',
    }
    
    @classmethod
    def colorize(cls, text: str, color: str = 'gray') -> str:
        """给文本添加颜色"""
        if not cls._supports_color():
            return text
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"
    
    @classmethod
    def _supports_color(cls) -> bool:
        """检查是否支持颜色输出"""
        return hasattr(os.sys.stdout, 'isatty') and os.sys.stdout.isatty()

# 在DebugConfig类中添加新的配置项
class DebugConfig:
    """调试配置类"""
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    DEBUG_DATA_PROVIDER = os.getenv("DEBUG_DATA_PROVIDER", "False").lower() == "true"
    DEBUG_EVENT_PROVIDER = os.getenv("DEBUG_EVENT_PROVIDER", "False").lower() == "true"
    DEBUG_STRATEGY = os.getenv("DEBUG_STRATEGY", "False").lower() == "true"
    DEBUG_BACKTEST = os.getenv("DEBUG_BACKTEST", "False").lower() == "true"
    DEBUG_SIGNALS = os.getenv("DEBUG_SIGNALS", "False").lower() == "true"
    DEBUG_LEVEL = os.getenv("DEBUG_LEVEL", "INFO").upper()

# 添加一个类变量来跟踪状态提示是否已显示
class DebugPrinter:
    """调试打印器"""
    _status_shown = {  # 跟踪各类别的状态是否已显示
        'data_provider': False,
        'event_provider': False,
        'strategy': False,
        'backtest': False,
        'signals': False,
    }
    
    @staticmethod
    def show_status_once(category: str, enabled: bool):
        """只显示一次状态提示"""
        if not DebugPrinter._status_shown[category]:
            if enabled:
                status_msg = ColoredConsole.colorize(f"📊 {category.upper()}调试日志已开启", 'green')
            else:
                status_msg = ColoredConsole.colorize(f"📊 {category.upper()}调试日志已关闭", 'dim')
            print(status_msg)
            DebugPrinter._status_shown[category] = True
    
    @staticmethod
    def reset_status():
        """重置状态显示标记（用于新的调试会话）"""
        for key in DebugPrinter._status_shown:
            DebugPrinter._status_shown[key] = False
    
    # 同时修改DebugPrinter.print_if_enabled方法中的category_enabled检查
    @staticmethod
    def print_if_enabled(category: str, message: str, data: Any = None, level: str = "INFO"):
        """根据配置决定是否打印调试信息"""
        # 检查全局调试模式
        if not DebugConfig.DEBUG_MODE:
            return
            
        # 检查具体类别的调试开关
        category_enabled = {
            'data_provider': DebugConfig.DEBUG_DATA_PROVIDER, 
            'event_provider': DebugConfig.DEBUG_EVENT_PROVIDER,
            'strategy': DebugConfig.DEBUG_STRATEGY,
            'backtest': DebugConfig.DEBUG_BACKTEST,
            'signals': DebugConfig.DEBUG_SIGNALS,
        }.get(category, False)
        
        if not category_enabled:
            return
            
        # 检查调试级别
        level_priority = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3
        }
        
        if level_priority.get(level, 1) < level_priority.get(DebugConfig.DEBUG_LEVEL, 1):
            return
            
        # 根据类别选择颜色
        color_map = {
            'data_provider': 'dim',      # 数据提供者用浅灰色
            'event_provider': 'dim',   # 事件提供者用黄色
            'strategy': 'dim',          # 策略用绿色
            'backtest': 'dim',         # 回测用黄色
            'signals': 'dim',           # 信号用绿色
        }
        
        color = color_map.get(category, 'dim')
        
        # 打印调试信息（带颜色）
        header = ColoredConsole.colorize(f"\n=== [{category.upper()}] {message} ===", color)
        print(header)
        
        if data is not None:
            if hasattr(data, 'shape'):  # DataFrame
                print(ColoredConsole.colorize(f"数据形状: {data.shape}", color))
                print(ColoredConsole.colorize(f"列名: {data.columns.tolist()}", color))
                if len(data) > 0:
                    print(ColoredConsole.colorize("前几行数据:", color))
                    print(ColoredConsole.colorize(str(data.head()), color))
            elif isinstance(data, dict):
                for key, value in data.items():
                    print(ColoredConsole.colorize(f"{key}: {value}", color))
            elif isinstance(data, (list, tuple)):
                print(ColoredConsole.colorize(f"数据长度: {len(data)}", color))
                if len(data) > 0:
                    print(ColoredConsole.colorize(f"前几个元素: {data[:5]}", color))
            else:
                print(ColoredConsole.colorize(f"数据: {data}", color))
                
        footer = ColoredConsole.colorize(f"=== [{category.upper()}] 结束 ===\n", color)
        print(footer)

def debug_decorator(category: str, message: str = "", level: str = "INFO"):
    """调试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_message = message or f"{func.__name__} 执行"
            DebugPrinter.print_if_enabled(category, f"开始 {func_message}", level=level)
            
            try:
                result = func(*args, **kwargs)
                DebugPrinter.print_if_enabled(category, f"完成 {func_message}", level=level)
                return result
            except Exception as e:
                DebugPrinter.print_if_enabled(category, f"错误 {func_message}: {str(e)}", level="ERROR")
                raise
                
        return wrapper
    return decorator

# 便捷函数
# 简化的debug_data_provider函数
def debug_data_provider(message: str, data: Any = None, level: str = "INFO"):
    """数据提供者调试打印"""
    if DebugConfig.DEBUG_DATA_PROVIDER:
        # 只在第一次调用时显示状态
        if not DebugPrinter._status_shown['data_provider']:
            status_msg = ColoredConsole.colorize("📊 DATA_PROVIDER调试日志已开启", 'green')
            print(status_msg)
            DebugPrinter._status_shown['data_provider'] = True
        
        # 显示调试信息
        DebugPrinter.print_if_enabled('data_provider', message, data, level)
    else:
        # 只在第一次调用时显示关闭状态
        if not DebugPrinter._status_shown['data_provider']:
            status_msg = ColoredConsole.colorize("📊 DATA_PROVIDER调试日志已关闭", 'dim')
            print(status_msg)
            DebugPrinter._status_shown['data_provider'] = True

# 同时修改其他调试函数保持一致性
def debug_strategy(message: str, data: Any = None, level: str = "INFO"):
    """策略调试打印"""
    DebugPrinter.show_status_once('strategy', DebugConfig.DEBUG_STRATEGY)
    if DebugConfig.DEBUG_STRATEGY:
        DebugPrinter.print_if_enabled('strategy', message, data, level)

def debug_backtest(message: str, data: Any = None, level: str = "INFO"):
    """回测调试打印"""
    DebugPrinter.show_status_once('backtest', DebugConfig.DEBUG_BACKTEST)
    if DebugConfig.DEBUG_BACKTEST:
        DebugPrinter.print_if_enabled('backtest', message, data, level)

def debug_signals(message: str, data: Any = None, level: str = "INFO"):
    """信号调试打印"""
    DebugPrinter.show_status_once('signals', DebugConfig.DEBUG_SIGNALS)
    if DebugConfig.DEBUG_SIGNALS:
        DebugPrinter.print_if_enabled('signals', message, data, level)

# 在文件末尾添加新的调试函数
def debug_event_provider(message: str, data: Any = None, level: str = "INFO"):
    """事件提供者调试打印"""
    DebugPrinter.show_status_once('event_provider', DebugConfig.DEBUG_EVENT_PROVIDER)
    if DebugConfig.DEBUG_EVENT_PROVIDER:
        DebugPrinter.print_if_enabled('event_provider', message, data, level)