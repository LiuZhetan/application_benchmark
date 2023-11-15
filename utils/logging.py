import logging


def set_log(log:str):
    log_dict = {
        'info': logging.INFO,
        'error': logging.ERROR,
        'debug': logging.DEBUG,
    }
    if log in log_dict.keys():
        logging.basicConfig(level=log_dict[log])
    else:
        logging.basicConfig(level=logging.INFO)