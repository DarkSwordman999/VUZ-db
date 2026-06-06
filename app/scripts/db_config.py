# -*- coding: utf-8 -*-
import os

DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'vuz_lab5'),
    'user': os.environ.get('DB_USER', 'uliavladimirovna'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
}
