import sys
from loguru import logger
import os

# 清除默认 handler
logger.remove()

# 添加控制台输出
logger.add(
    sink=sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {name}:{function}:{line} | <level>{message}</level>"
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

# 导出 logger 和 catch
__all__ = ['logger', 'catch']
