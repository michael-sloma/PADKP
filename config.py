import json
import os
import sys


def _get_config_file_path():
    if sys.platform == 'win32':
        dir = os.path.join(os.environ['APPDATA'], 'PADKP')
    else:
        dir = os.getcwd()
    if not os.path.exists(dir):
        os.mkdir(dir)
    return os.path.join(dir, 'PADKP_config.json')


def load_saved_config():
    path = _get_config_file_path()
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    else:
        return {}


def write_config(config):
    if config:
        path = _get_config_file_path()
        with open(path, 'w') as f:
            json.dump(config, f)
