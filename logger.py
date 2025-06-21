import logging

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s"
)

app_logger = logging.getLogger("myApp")
app_logger.setLevel(logging.INFO)
app_file_handler = logging.FileHandler("app.log", encoding="utf-8")
app_file_handler.setFormatter(formatter)
app_logger.addHandler(app_file_handler)
app_logger.propagate = False

flask_file_handler = logging.FileHandler("flask.log", encoding="utf-8")
flask_file_handler.setFormatter(formatter)
flask_logger = logging.getLogger("flask")
flask_logger.setLevel(logging.INFO)
flask_logger.addHandler(flask_file_handler)
flask_logger.propagate = False
