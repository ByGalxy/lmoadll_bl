import logging
from var.lmoadll.endpoint.console import log_queue

class QueueLoggingHandler(logging.Handler):
    def emit(self, record):
        # 将日志发送到中央队列
        level = record.levelname
        message = self.format(record)
        log_queue.put((level, message))


def setup_logging():
    # 禁止其他uvicorn日志器
    for logger_name in ["uvicorn.error", "uvicorn.access"]:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(name)s] %(message)s",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "queue_handler": {
                "()": "logs.QueueLoggingHandler",
                "formatter": "default",
                "level": "INFO"
            },
            "file_handler": {
                "class": "logging.FileHandler",
                "filename": "app.log",
                "formatter": "default",
                "level": "INFO"
            }
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["queue_handler", "file_handler"],
        "propagate": False,
                "level": "INFO"
            }
        }
    }