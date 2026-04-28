import logging, sys
from loguru import logger

# Удаляем стандартный stdout-sink, чтобы поставить свой формат
logger.remove()
logger.add(
    sys.stderr,
    level="WARNING",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}",
    enqueue=True,   # безопасно для async
    backtrace=True, # вкл. подробный стек при исключениях
    diagnose=True,  # показывает содержимое локальных переменных
)

# Чтобы сторонние библиотеки (httpx, discord и т.п.) писали через Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

__all__ = ["logger"]

