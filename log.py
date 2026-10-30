import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:          # 防止重复添加 handler
        return logger

    logger.setLevel(logging.DEBUG) # 第一道过滤
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO) # 控制台过滤
    sh.setFormatter(fmt)

    # 文件
    fh = logging.FileHandler("app.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG) #文件过滤
    fh.setFormatter(fmt)

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger
