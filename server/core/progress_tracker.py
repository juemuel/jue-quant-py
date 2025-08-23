import datetime
import pandas as pd
from typing import Dict, List, Any, Optional
from core.logger import logger
from pathlib import Path
import sys

class ColoredConsole:
    """控制台颜色输出工具类"""
    
    # ANSI 颜色代码
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'underline': '\033[4m',
        
        # 前景色
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        
        # 亮色
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
        
        # 背景色
        'bg_red': '\033[41m',
        'bg_green': '\033[42m',
        'bg_yellow': '\033[43m',
        'bg_blue': '\033[44m',
    }
    
    @classmethod
    def colorize(cls, text: str, color: str = None, bg_color: str = None, bold: bool = False) -> str:
        """给文本添加颜色"""
        if not cls._supports_color():
            return text
            
        codes = []
        if bold:
            codes.append(cls.COLORS['bold'])
        if color and color in cls.COLORS:
            codes.append(cls.COLORS[color])
        if bg_color and bg_color in cls.COLORS:
            codes.append(cls.COLORS[bg_color])
            
        if codes:
            return f"{''.join(codes)}{text}{cls.COLORS['reset']}"
        return text
    
    @classmethod
    def _supports_color(cls) -> bool:
        """检查终端是否支持颜色"""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    @classmethod
    def success(cls, text: str) -> str:
        return cls.colorize(text, 'bright_green', bold=True)
    
    @classmethod
    def error(cls, text: str) -> str:
        return cls.colorize(text, 'bright_red', bold=True)
    
    @classmethod
    def warning(cls, text: str) -> str:
        return cls.colorize(text, 'bright_yellow')
    
    @classmethod
    def info(cls, text: str) -> str:
        return cls.colorize(text, 'bright_cyan')
    
    @classmethod
    def progress(cls, text: str) -> str:
        return cls.colorize(text, 'green')
    
    @classmethod
    def highlight(cls, text: str) -> str:
        return cls.colorize(text, 'bright_white', bold=True)
    
    @classmethod
    def dim(cls, text: str) -> str:
        return cls.colorize(text, 'white')

class ProgressTracker:
    """
    进度跟踪器 - 支持彩色输出
    支持多种调试场景：策略调试、回测调试、数据分析等
    """
    
    def __init__(self, module_name: str, enable_console: bool = True, enable_excel: bool = True, enable_colors: bool = True):
        self.module_name = module_name
        self.enable_console = enable_console
        self.enable_excel = enable_excel
        self.enable_colors = enable_colors
        
        # 日志存储
        self.step_logs = []      # 步骤日志
        self.detail_logs = []    # 详细日志
        self.error_logs = []     # 错误日志
        self.data_logs = []      # 数据相关日志
        self.performance_logs = [] # 性能日志
        
        # 步骤状态跟踪
        self.step_status = {}
        self.session_start = datetime.datetime.now()
        
        # 控制台输出配置
        self.console_config = {
            'show_progress': True,
            'show_summary': True,
            'show_errors': True,
            'max_detail_lines': 3,  # 控制台最多显示的详细信息行数
            'show_timestamps': False,  # 是否显示时间戳
            'indent_details': True,    # 是否缩进详细信息
        }
        
        # 颜色主题配置
        self.color_theme = {
            'session_start': {'color': 'bright_green', 'bold': True},  # 改为绿色
            'session_end': {'color': 'bright_green', 'bold': True},    # 改为绿色
            'step_start': {'color': 'green'},                          # 改为绿色
            'step_success': {'color': 'bright_green', 'bold': True},   # 保持绿色
            'step_error': {'color': 'bright_red', 'bold': True},       # 保持红色（失败）
            'warning': {'color': 'bright_yellow'},                     # 保持黄色（警告）
            'info': {'color': 'green'},                                # 改为绿色
            'data': {'color': 'bright_green'},                         # 改为绿色
            'performance': {'color': 'green'},                         # 改为绿色
            'detail': {'color': 'green'},                              # 改为绿色
            'summary': {'color': 'bright_green', 'bold': True}         # 改为绿色
        }
    
    def _colorize_text(self, text: str, style_key: str) -> str:
        """根据样式键给文本着色"""
        if not self.enable_colors:
            return text
            
        style = self.color_theme.get(style_key, {})
        return ColoredConsole.colorize(
            text,
            color=style.get('color'),
            bold=style.get('bold', False)
        )
    
    def _print_with_timestamp(self, text: str, style_key: str = 'info'):
        """带时间戳的控制台输出"""
        if not self.enable_console:
            return
            
        if self.console_config.get('show_timestamps', False):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] {text}"
        else:
            formatted_text = text
            
        colored_text = self._colorize_text(formatted_text, style_key)
        print(colored_text)
    
    def start_session(self, session_name: str, description: str = ""):
        """开始调试会话"""
        self.session_start = datetime.datetime.now()
        
        session_info = {
            'session_name': session_name,
            'description': description,
            'start_time': self.session_start,
            'module': self.module_name
        }
        
        if self.enable_console:
            header = f"\n{'='*60}"
            title = f"🚀 开始调试会话: {session_name}"
            if description:
                desc = f"📝 描述: {description}"
                self._print_with_timestamp(f"{header}\n{title}\n{desc}\n{'='*60}", 'session_start')
            else:
                self._print_with_timestamp(f"{header}\n{title}\n{'='*60}", 'session_start')
    
    def log_step_start(self, step_name: str, description: str = "", **kwargs):
        """记录步骤开始"""
        step_info = {
            'step_name': step_name,
            'description': description,
            'start_time': datetime.datetime.now(),
            'status': 'started',
            'details': kwargs
        }
        
        self.step_logs.append(step_info)
        self.step_status[step_name] = 'started'
        
        if self.enable_console and self.console_config.get('show_progress', True):
            if description:
                self._print_with_timestamp(f"🔄 {step_name}: {description}", 'step_start')
            else:
                self._print_with_timestamp(f"🔄 {step_name}", 'step_start')
            
            # 显示额外参数
            if kwargs and self.console_config.get('indent_details', True):
                for key, value in kwargs.items():
                    self._print_with_timestamp(f"   └─ {key}: {value}", 'detail')
    
    def log_step_success(self, step_name: str, summary: str = "", details: Dict = None, **kwargs):
        """记录步骤成功"""
        success_info = {
            'step_name': step_name,
            'summary': summary,
            'success_time': datetime.datetime.now(),
            'status': 'success',
            'details': details or {},
            'extra': kwargs
        }
        
        # 更新步骤日志
        for log in self.step_logs:
            if log['step_name'] == step_name and log['status'] == 'started':
                log.update(success_info)
                break
        else:
            self.step_logs.append(success_info)
        
        self.step_status[step_name] = 'success'
        
        if self.enable_console and self.console_config.get('show_progress', True):
            if summary:
                self._print_with_timestamp(f"✅ {step_name}: {summary}", 'step_success')
            else:
                self._print_with_timestamp(f"✅ {step_name} 完成", 'step_success')
            
            # 显示详细信息（限制行数）
            if details and self.console_config.get('indent_details', True):
                max_lines = self.console_config.get('max_detail_lines', 3)
                count = 0
                for key, value in details.items():
                    if count >= max_lines:
                        remaining = len(details) - max_lines
                        self._print_with_timestamp(f"   └─ ... 还有 {remaining} 项详细信息", 'detail')
                        break
                    self._print_with_timestamp(f"   └─ {key}: {value}", 'detail')
                    count += 1
    
    def log_step_error(self, step_name: str, error_msg: str, details: Dict = None, **kwargs):
        """记录步骤错误"""
        error_info = {
            'step_name': step_name,
            'error_msg': error_msg,
            'error_time': datetime.datetime.now(),
            'status': 'error',
            'details': details or {},
            'extra': kwargs
        }
        
        self.error_logs.append(error_info)
        self.step_status[step_name] = 'error'
        
        # 同时记录到系统日志
        logger.error(f"[{self.module_name}] {step_name}: {error_msg}")
        
        if self.enable_console and self.console_config.get('show_errors', True):
            self._print_with_timestamp(f"❌ {step_name}: {error_msg}", 'step_error')
            
            if details and self.console_config.get('indent_details', True):
                for key, value in details.items():
                    self._print_with_timestamp(f"   └─ {key}: {value}", 'detail')
    
    def log_data_info(self, data_name: str, data: Any, analysis: Dict = None):
        """记录数据信息"""
        data_analysis = analysis or self._analyze_data(data_name, data)
        
        data_info = {
            'data_name': data_name,
            'timestamp': datetime.datetime.now(),
            'analysis': data_analysis
        }
        
        self.data_logs.append(data_info)
        
        if self.enable_console:
            self._print_with_timestamp(f"📊 数据分析: {data_name}", 'data')
            if self.console_config.get('indent_details', True):
                for key, value in data_analysis.items():
                    self._print_with_timestamp(f"   └─ {key}: {value}", 'detail')
    
    def log_performance(self, operation: str, duration: float, details: Dict = None):
        """记录性能信息"""
        perf_info = {
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.datetime.now(),
            'details': details or {}
        }
        
        self.performance_logs.append(perf_info)
        
        if self.enable_console:
            self._print_with_timestamp(f"⏱️ 性能: {operation} 耗时 {duration:.3f}s", 'performance')
    
    def log_warning(self, message: str, details: Dict = None):
        """记录警告信息"""
        warning_info = {
            'message': message,
            'timestamp': datetime.datetime.now(),
            'details': details or {}
        }
        
        if self.enable_console:
            self._print_with_timestamp(f"⚠️ 警告: {message}", 'warning')
    
    def log_info(self, message: str, details: Dict = None):
        """记录一般信息"""
        info_data = {
            'message': message,
            'timestamp': datetime.datetime.now(),
            'details': details or {}
        }
        
        if self.enable_console:
            self._print_with_timestamp(f"ℹ️ 信息: {message}", 'info')
    
    def log_detail(self, category: str, message: str, details: Dict = None, level: str = 'INFO'):
        """记录详细信息"""
        detail_info = {
            'category': category,
            'message': message,
            'level': level,
            'timestamp': datetime.datetime.now(),
            'details': details or {}
        }
        
        self.detail_logs.append(detail_info)
        
        if self.enable_console:
            self._print_with_timestamp(f"📝 [{category}] {message}", 'detail')
    
    def end_session(self, summary: str = ""):
        """结束调试会话"""
        session_end = datetime.datetime.now()
        duration = (session_end - self.session_start).total_seconds()
        
        if self.enable_console and self.console_config.get('show_summary', True):
            footer = f"\n{'='*60}"
            title = f"🏁 调试会话结束"
            duration_info = f"⏱️ 总耗时: {duration:.2f}s"
            
            # 统计信息
            total_steps = len(self.step_logs)
            success_steps = len([s for s in self.step_logs if s.get('status') == 'success'])
            error_steps = len(self.error_logs)
            
            stats = f"📈 步骤统计: 总计 {total_steps}, 成功 {success_steps}, 失败 {error_steps}"
            
            if summary:
                summary_info = f"📋 总结: {summary}"
                self._print_with_timestamp(f"{footer}\n{title}\n{duration_info}\n{stats}\n{summary_info}\n{'='*60}\n", 'session_end')
            else:
                self._print_with_timestamp(f"{footer}\n{title}\n{duration_info}\n{stats}\n{'='*60}\n", 'session_end')
        
        # 如果启用Excel导出，自动导出
        if self.enable_excel:
            try:
                filename = self.export_to_excel()
                if filename and self.enable_console:
                    self._print_with_timestamp(f"📄 调试日志已导出到: {filename}", 'info')
            except Exception as e:
                if self.enable_console:
                    self._print_with_timestamp(f"❌ Excel导出失败: {str(e)}", 'step_error')
    
    def _analyze_data(self, name: str, data: Any) -> Dict:
        """分析数据并返回统计信息"""
        if isinstance(data, pd.DataFrame):
            return {
                '类型': 'DataFrame',
                '形状': f"{data.shape[0]}行 x {data.shape[1]}列",
                '列名': list(data.columns)[:5],  # 只显示前5列
                '内存使用': f"{data.memory_usage(deep=True).sum() / 1024:.1f}KB"
            }
        elif isinstance(data, (list, tuple)):
            return {
                '类型': type(data).__name__,
                '长度': len(data),
                '示例': str(data[:3]) if len(data) > 0 else '空'
            }
        elif isinstance(data, dict):
            return {
                '类型': 'dict',
                '键数量': len(data),
                '键名': list(data.keys())[:5]  # 只显示前5个键
            }
        else:
            return {
                '类型': type(data).__name__,
                '值': str(data)[:100]  # 限制长度
            }
    
    def export_to_excel(self, filename_prefix: str = None) -> Optional[str]:
        """导出调试日志到Excel文件"""
        if not self.enable_excel:
            return None
            
        try:
            # 生成文件名
            if filename_prefix:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename_prefix}_{timestamp}.xlsx"
            else:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_module_name = self.module_name.replace(" ", "_").replace("/", "_")
                filename = f"debug_log_{safe_module_name}_{timestamp}.xlsx"
            
            # 确保输出目录存在
            output_dir = Path("debug_logs")
            output_dir.mkdir(exist_ok=True)
            filepath = output_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 步骤日志
                if self.step_logs:
                    steps_df = pd.DataFrame(self.step_logs)
                    steps_df.to_excel(writer, sheet_name='步骤日志', index=False)
                
                # 错误日志
                if self.error_logs:
                    errors_df = pd.DataFrame(self.error_logs)
                    errors_df.to_excel(writer, sheet_name='错误日志', index=False)
                
                # 数据日志
                if self.data_logs:
                    # 展开分析数据
                    data_records = []
                    for log in self.data_logs:
                        record = {
                            'data_name': log['data_name'],
                            'timestamp': log['timestamp']
                        }
                        # 展开analysis字典
                        if 'analysis' in log:
                            for key, value in log['analysis'].items():
                                record[f'analysis_{key}'] = value
                        data_records.append(record)
                    
                    data_df = pd.DataFrame(data_records)
                    data_df.to_excel(writer, sheet_name='数据日志', index=False)
                
                # 性能日志
                if self.performance_logs:
                    perf_df = pd.DataFrame(self.performance_logs)
                    perf_df.to_excel(writer, sheet_name='性能日志', index=False)
                
                # 详细日志
                if self.detail_logs:
                    detail_df = pd.DataFrame(self.detail_logs)
                    detail_df.to_excel(writer, sheet_name='详细日志', index=False)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"导出Excel失败: {str(e)}")
            return None
    
    def configure_console(self, **kwargs):
        """配置控制台输出选项"""
        self.console_config.update(kwargs)
    
    def configure_colors(self, **color_overrides):
        """配置颜色主题"""
        self.color_theme.update(color_overrides)
    
    def set_color_theme(self, theme_name: str):
        """设置预定义的颜色主题"""
        themes = {
            'default': {
                'session_start': {'color': 'bright_green', 'bold': True},
                'session_end': {'color': 'bright_green', 'bold': True},
                'step_start': {'color': 'green'},
                'step_success': {'color': 'bright_green', 'bold': True},
                'step_error': {'color': 'bright_red', 'bold': True},
                'warning': {'color': 'bright_yellow'},
                'info': {'color': 'green'},
                'data': {'color': 'bright_green'},
                'performance': {'color': 'green'},
                'detail': {'color': 'green'},
                'summary': {'color': 'bright_green', 'bold': True}
            },
            'dark': {
                'session_start': {'color': 'bright_cyan', 'bold': True},
                'session_end': {'color': 'bright_cyan', 'bold': True},
                'step_start': {'color': 'cyan'},
                'step_success': {'color': 'bright_green', 'bold': True},
                'step_error': {'color': 'bright_red', 'bold': True},
                'warning': {'color': 'bright_yellow'},
                'info': {'color': 'cyan'},
                'data': {'color': 'bright_cyan'},
                'performance': {'color': 'cyan'},
                'detail': {'color': 'white'},
                'summary': {'color': 'bright_cyan', 'bold': True}
            },
            'minimal': {
                'session_start': {'color': 'white', 'bold': True},
                'session_end': {'color': 'white', 'bold': True},
                'step_start': {'color': 'white'},
                'step_success': {'color': 'green'},
                'step_error': {'color': 'red'},
                'warning': {'color': 'yellow'},
                'info': {'color': 'white'},
                'data': {'color': 'white'},
                'performance': {'color': 'white'},
                'detail': {'color': 'dim'},
                'summary': {'color': 'white', 'bold': True}
            }
        }
        
        if theme_name in themes:
            self.color_theme = themes[theme_name]

# 便捷创建函数
def create_progress_tracker(module_name: str, **kwargs) -> ProgressTracker:
    """创建进度跟踪器的便捷函数"""
    return ProgressTracker(module_name, **kwargs)

# 预设配置函数
def create_strategy_tracker(**kwargs) -> ProgressTracker:
    """创建策略调试专用进度跟踪器"""
    tracker = ProgressTracker("策略调试", **kwargs)
    tracker.configure_console(
        show_progress=True,
        show_summary=True,
        max_detail_lines=2,
        show_timestamps=False,
        indent_details=True
    )
    return tracker

def create_backtest_tracker(**kwargs) -> ProgressTracker:
    """创建回测调试专用进度跟踪器"""
    tracker = ProgressTracker("回测调试", **kwargs)
    tracker.configure_console(
        show_progress=True,
        show_summary=True,
        max_detail_lines=1,
        show_timestamps=True,
        indent_details=True
    )
    tracker.set_color_theme('dark')  # 回测使用深色主题
    return tracker