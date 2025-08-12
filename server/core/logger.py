import sys
import logging
from loguru import logger

debug_mode = False  # 设置为 True 启用调试模式
def custom_excepthook(type, value, traceback):
    if debug_mode:
        sys.__excepthook__(type, value, traceback)
    else:
        logger.error(f"[ERROR] {value}")

# 设置自定义异常钩子
sys.excepthook = custom_excepthook

# 清除默认 handler
logger.remove()

# 添加控制台输出
logger.add(
    sink=sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {name}:{function}:{line} | <level>{message}</level>",
)

# 同时写入日志文件（可选）
logger.add(
    sink="app.log",
    level="DEBUG",
    rotation="10 MB",
    retention="5 days"
)

# 将 catch 显式绑定到 logger 对象
catch = logger.catch

# 拦截标准 logging 模块日志
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        # 关键修改：不再传递 exc_info，防止 traceback 输出
        logger.opt(depth=depth, exception=record.exc_info if debug_mode else None).log(level, record.getMessage())


# 禁用 Uvicorn 默认日志输出
logging.getLogger("uvicorn").handlers = []
logging.getLogger("uvicorn.error").handlers = []
logging.getLogger("uvicorn.access").handlers = []
# 将所有 logging 日志重定向给 loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0)

# 导出 logger 和 catch
__all__ = ['logger', 'catch']
