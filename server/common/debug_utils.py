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
    # 数据调试工具
    DEBUG_DATA_PROVIDER = os.getenv("DEBUG_DATA_PROVIDER", "False").lower() == "true"
    # 事件调试工具
    DEBUG_EVENT_PROVIDER = os.getenv("DEBUG_EVENT_PROVIDER", "False").lower() == "true"
    # 策略调试工具
    DEBUG_STRATEGY = os.getenv("DEBUG_STRATEGY", "False").lower() == "true"
    # 回测调试工具
    DEBUG_BACKTEST = os.getenv("DEBUG_BACKTEST", "False").lower() == "true"
    # 信号调试工具
    DEBUG_SIGNALS = os.getenv("DEBUG_SIGNALS", "False").lower() == "true"
    # 指标调试工具
    DEBUG_INDICATORS = os.getenv("DEBUG_INDICATORS", "False").lower() == "true"
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
        'indicators': False,
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
    def print_if_enabled(category: str, message: str, data: Any = None, level: str = "INFO",
    horizontal_output: bool = False, show_full_content: bool = False):
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
            'data_provider': 'dim',
            'event_provider': 'dim',
            'strategy': 'dim',
            'backtest': 'dim',
            'signals': 'dim',
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
                    if isinstance(value, list):
                        if horizontal_output and show_full_content:
                            # 横向输出完整内容
                            items_str = ", ".join(str(item) for item in value)
                            print(ColoredConsole.colorize(f"{key}: [{len(value)}个项目] - {items_str}", color))
                        elif show_full_content:
                            # 纵向输出完整内容
                            print(ColoredConsole.colorize(f"{key}: [{len(value)}个项目]", color))
                            for item in value:
                                print(ColoredConsole.colorize(f"  - {item}", color))
                        else:
                            # 原有的省略显示方式
                            print(ColoredConsole.colorize(f"{key}: [{len(value)}个项目]", color))
                            if len(value) > 0:
                                for i, item in enumerate(value[:3]):  # 只显示前3个
                                    print(ColoredConsole.colorize(f"  - {item}", color))
                                if len(value) > 3:
                                    print(ColoredConsole.colorize(f"  ... 还有{len(value)-3}个项目", color))
                    else:
                        print(ColoredConsole.colorize(f"{key}: {value}", color))
            elif isinstance(data, (list, tuple)):
                print(ColoredConsole.colorize(f"数据长度: {len(data)}", color))
                if len(data) > 0:
                    if horizontal_output and show_full_content:
                        items_str = ", ".join(str(item) for item in data)
                        print(ColoredConsole.colorize(f"所有元素: {items_str}", color))
                    elif show_full_content:
                        for item in data:
                            print(ColoredConsole.colorize(f"  - {item}", color))
                    else:
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

def debug_data_provider(message: str, data: Any = None, level: str = "INFO", 
                       horizontal_output: bool = False, show_full_content: bool = False):
    DebugPrinter.show_status_once('data_provider', DebugConfig.DEBUG_DATA_PROVIDER)
    if DebugConfig.DEBUG_DATA_PROVIDER:
        DebugPrinter.print_if_enabled('data_provider', message, data, level, 
                                     horizontal_output, show_full_content)
def debug_event_provider(message: str, data: Any = None, level: str = "INFO", 
                       horizontal_output: bool = False, show_full_content: bool = False):
    DebugPrinter.show_status_once('event_provider', DebugConfig.DEBUG_EVENT_PROVIDER)
    if DebugConfig.DEBUG_EVENT_PROVIDER:
        DebugPrinter.print_if_enabled('event_provider', message, data, level, 
                                     horizontal_output, show_full_content)
def debug_strategy(message: str, data: Any = None, level: str = "INFO", 
                  horizontal_output: bool = False, show_full_content: bool = False):
    DebugPrinter.show_status_once('strategy', DebugConfig.DEBUG_STRATEGY)
    if DebugConfig.DEBUG_STRATEGY:
        DebugPrinter.print_if_enabled('strategy', message, data, level, 
                                     horizontal_output, show_full_content)

def debug_backtest(message: str, data: Any = None, level: str = "INFO", 
                  horizontal_output: bool = False, show_full_content: bool = False):
    DebugPrinter.show_status_once('backtest', DebugConfig.DEBUG_BACKTEST)
    if DebugConfig.DEBUG_BACKTEST:
        DebugPrinter.print_if_enabled('backtest', message, data, level, 
                                     horizontal_output, show_full_content)

def debug_signals(message: str, data: Any = None, level: str = "INFO", 
                  horizontal_output: bool = False, show_full_content: bool = False):
    DebugPrinter.show_status_once('signals', DebugConfig.DEBUG_SIGNALS)
    if DebugConfig.DEBUG_SIGNALS:
        DebugPrinter.print_if_enabled('signals', message, data, level, 
                                     horizontal_output, show_full_content)

def debug_indicators(message: str, data: Any = None, level: str = "INFO", 
                  horizontal_output: bool = False, show_full_content: bool = False):
    DebugPrinter.show_status_once('indicators', DebugConfig.DEBUG_INDICATORS)
    if DebugConfig.DEBUG_INDICATORS:
        DebugPrinter.print_if_enabled('indicators', message, data, level, 
                                     horizontal_output, show_full_content)

class UnifiedDebugLogger:
    """统一调试日志管理器 - 整合 debug_utils 和 progress_tracker"""
    
    def __init__(self, module_name: str, category: str = 'strategy'):
        self.module_name = module_name
        self.category = category
        self.progress_tracker = None
        self._session_active = False
    
    def start_session(self, session_name: str, description: str = ""):
        """开始调试会话"""
        from common.progress_tracker import create_progress_tracker
        self.progress_tracker = create_progress_tracker(self.module_name)
        self.progress_tracker.start_session(session_name, description)
        self._session_active = True
        
        # 显示调试状态
        DebugPrinter.show_status_once(self.category, self._is_category_enabled())
    
    def step_start(self, step_name: str, description: str = "", **kwargs):
        """开始步骤"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_step_start(step_name, description, **kwargs)
        else:
            self.info(f"开始 {step_name}: {description}")
    
    def step_info(self, step_name: str, info: str = "", **kwargs):
        """步骤信息"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_info(step_name, info, **kwargs)
        else:
            self.info(f"步骤 {step_name} 信息: {info}")

    def step_success(self, step_name: str, summary: str = "", details: dict = None, **kwargs):
        """步骤成功"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_step_success(step_name, summary, details, **kwargs)
        else:
            self.success(f"完成 {step_name}: {summary}")
    def step_skip(self, step_name: str, reason: str = "", **kwargs):
        """跳过步骤"""
        if self.progress_tracker and self._session_active:
            # 使用 log_info 方法记录跳过信息
            self.progress_tracker.log_info(f"⏭️ 跳过 {step_name}: {reason}", kwargs if kwargs else None)
        else:
            self.info(f"⏭️ 跳过 {step_name}: {reason}")
    def step_error(self, step_name: str, error_msg: str, details: dict = None, **kwargs):
        """步骤错误"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_step_error(step_name, error_msg, details, **kwargs)
        else:
            self.error(f"错误 {step_name}: {error_msg}")
    
    def data_analysis(self, data_name: str, data, analysis: dict = None):
        """数据分析日志"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_data_info(data_name, data, analysis)
        else:
            DebugPrinter.print_if_enabled(self.category, f"数据分析: {data_name}", data)
    
    def performance(self, operation: str, duration: float, details: dict = None):
        """性能日志"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_performance(operation, duration, details)
        else:
            self.info(f"性能: {operation} 耗时 {duration:.3f}s")
    
    def info(self, message: str, data=None, level: str = "INFO"):
        """信息日志"""
        DebugPrinter.print_if_enabled(self.category, message, data, level)
    
    def success(self, message: str, data=None):
        """成功日志"""
        self.info(f"✅ {message}", data, "INFO")
    
    def warning(self, message: str, data=None):
        """警告日志"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.log_warning(message, {'data': data} if data else None)
        else:
            DebugPrinter.print_if_enabled(self.category, f"⚠️ {message}", data, "WARNING")
    
    def error(self, message: str, data=None):
        """错误日志"""
        DebugPrinter.print_if_enabled(self.category, f"❌ {message}", data, "ERROR")
    
    def debug(self, message: str, data=None):
        """调试日志"""
        self.info(f"🔍 {message}", data, "DEBUG")
    
    def end_session(self, summary: str = ""):
        """结束会话"""
        if self.progress_tracker and self._session_active:
            self.progress_tracker.end_session(summary)
            self._session_active = False
    
    def _is_category_enabled(self) -> bool:
        """检查当前类别是否启用"""
        category_map = {
            'strategy': DebugConfig.DEBUG_STRATEGY,
            'signals': DebugConfig.DEBUG_SIGNALS,
            'event_provider': DebugConfig.DEBUG_EVENT_PROVIDER,
            'data_provider': DebugConfig.DEBUG_DATA_PROVIDER,
            'backtest': DebugConfig.DEBUG_BACKTEST,
        }
        return category_map.get(self.category, False)

# 便捷创建函数
def create_debug_logger(module_name: str, category: str = 'strategy') -> UnifiedDebugLogger:
    """创建统一调试日志器"""
    return UnifiedDebugLogger(module_name, category)