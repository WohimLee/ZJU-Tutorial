import logging
import os
from logging.handlers import RotatingFileHandler

# 创建目录
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("data_gen")  # 创建或获取一个名为 data_gen 的 logger 对象

# 设置 logger 能接收的 最低日志级别。
# DEBUG 是最低级别，意味着：DEBUG、INFO、WARNING、ERROR、CRITICAL 都能被 logger 接收处理
logger.setLevel(logging.DEBUG)

error_handler = RotatingFileHandler(
    "logs/data_gen_errors.log", # 日志文件的保存路径
    maxBytes=5 * 1024 * 1024,   # 日志文件达到 5MB 时自动滚动
    backupCount=3,              # 最多保留：data_gen_errors.log, data_gen_errors.log.1, data_gen_errors.log.2, data_gen_errors.log.3
    encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] %(levelname)s - intent=%(intent)s label=%(label)s num=%(num)s index=%(index)s msg=%(message)s"
))

logger.addHandler(error_handler)
