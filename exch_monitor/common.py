"""
Common functions
"""
import os

DATE_FORMAT_TZ = '%Y-%m-%d %H:%M:%S +0800'

def is_server():
    # add a env var on server IS_SERVER: Y
    return os.getenv('IS_SERVER', 'N') == 'Y'