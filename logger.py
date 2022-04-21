import logging

logger = logging.getLogger("dingdong-helper")
logger.setLevel(logging.INFO)

stock_log = logging.FileHandler('stock_log.log', 'a', encoding='utf-8')
stock_log.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(module)s - %(threadName)s - %(levelname)s - %(lineno)s line: %("
                              "message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")

stock_log.setFormatter(formatter)
console.setFormatter(formatter)

logger.addHandler(stock_log)
# logger.addHandler(console)


def log():
    return logger
