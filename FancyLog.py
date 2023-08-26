from datetime import datetime


def log(process, msg_type, content):
    print((datetime.now().strftime("%d/%m/%y %H:%M:%S")), f'[{msg_type}]', f'[{process}]', content)
