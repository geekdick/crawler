import redis
from ProxyPool.proxyPool.erro import PoolEmptyError
from ProxyPool.proxyPool.setting import HOST, PORT, PASSWORD


class RedisClient(object):
    def __init__(self, host=HOST, port=PORT):
        if PASSWORD:
            self._db = redis.Redis(host=host, port=port, password=PASSWORD)
        else:
            self._db = redis.Redis(host=host, port=port)

    def get(self, count=1):
        """
        获取count元素
        """
        proxies = self._db.lrange("proxies", 0, count - 1)
        self._db.ltrim("proxies", count, -1)
        return proxies

    def put(self, proxy):
        """
        左边存入一个元素
        """
        self._db.lpush("proxies", proxy)

    def pop(self):
        """
        右边弹出元素
        """
        try:
            return self._db.rpop("proxies").decode('utf-8')
        except:
            raise PoolEmptyError

    @property
    def queue_len(self):
        """
        获取列表长度
        """
        return self._db.llen("proxies")

    def flush(self):
        """
        刷新缓存
        """
        self._db.flushall()


if __name__ == '__main__':
    conn = RedisClient()
    print(conn.pop())