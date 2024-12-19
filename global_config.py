#!/usr/bin/env python
# Linux setup utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import os
import json

DEFAULT_CONFIG_ROOT  = os.path.expanduser("~/.creekside/linux_setup")
DEFAULT_CONFIG_FILE  = os.path.join(DEFAULT_CONFIG_ROOT,"cfg/config.json")
DEFAULT_LOG_PATH     = os.path.join(DEFAULT_CONFIG_ROOT,"log")

DEFAULT_CONFIG = {
    "log": {
        "path": DEFAULT_LOG_PATH
    },
}


class GlobalConfig:
    _instance = None

    def __new__(cls, config_path=DEFAULT_CONFIG_FILE):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
            cls._instance._initialize(config_path)
        return cls._instance

    def _initialize(self, config_path):
        self.config_path = os.path.expanduser(config_path)
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if os.path.exists(self.config_path):
            # Load existing configuration
            with open(self.config_path, 'r') as file:
                self.config_data = json.load(file)
        else:
            # Initialize configuration with default values
            self.config_data = DEFAULT_CONFIG.copy()
            with open(self.config_path, 'w') as file:
                json.dump(self.config_data, file, indent=4)

    def get(self, key, default=None):
        keys = key.split()
        subdict = self.config_data
        for k in keys:
            if isinstance(subdict, dict) and k in subdict:
                subdict = subdict[k]
            else:
                return default
        return subdict

    def search(self, path):
        #Check if a configuration path exists in the config_data dictionary
        #:param path: Configuration path
        #:return: True if the path exists, False otherwise
        keys = path.split()
        d = self.config_data
        for key in keys:
            if key in d:
                d = d[key]
            else:
                return False
        return True
    
    # Set a configuration value by key path, such as "log path"
    def set(self, key, value):
        keys = key.split()
        config = self.config_data
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()

    def _save_config(self):
        with open(self.config_path, 'w') as file:
            json.dump(self.config_data, file, indent=4)