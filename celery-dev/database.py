
import os
import sys
import inspect
from peewee import *
from playhouse.pool import PooledPostgresqlExtDatabase

from config import CeleryConfig
config = CeleryConfig()

db_user = config.DB_APPS_USER
db = PooledPostgresqlExtDatabase(config.DB_APPS_CONFIG)
