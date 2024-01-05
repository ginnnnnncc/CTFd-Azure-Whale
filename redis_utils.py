import ipaddress
from flask_redis import FlaskRedis
from redis.exceptions import LockError
from .db_utils import DBUtils

class RedisUtils:
    def __init__(self, app, user_id=0):
        self.redis_client = FlaskRedis(app)
        self.key = 'ctfd_whale_lock-' + str(user_id)
        self.lock = None

    def acquire_lock(self):
        lock = self.redis_client.lock(name=self.key, timeout=10)

        if not lock.acquire(blocking=True, blocking_timeout=2.0):
            return False

        self.lock = lock
        return True

    def release_lock(self):
        if self.lock is None:
            return False

        try:
            self.lock.release()

            return True
        except LockError:
            return False
