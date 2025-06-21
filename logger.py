import logging

logger = logging.getLogger("myApp")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
))

logger.addHandler(file_handler)
