import asyncio
from urllib.parse import urlparse
import aiohttp
import logging

logger = logging.getLogger(__name__)


class AsyncRequest(object):
    def __init__(self, parallel_count=50, timeout=5):
        self.semaphore = asyncio.Semaphore(parallel_count)
        self.timeout = timeout or 5
        self.user = 'zhaohui'
        self.password = 'AHSKsxky2096'

    async def request(self, url, proxy=None, timeout=None, headers=None,
                      proxy_auth=None, parse=None, semaphore=None, session=None, method=None, report_error=None,
                      response_type=None, success_code=None):

        if not timeout or not isinstance(timeout, aiohttp.ClientTimeout):
            timeout = aiohttp.ClientTimeout(self.timeout or 5)

        if not semaphore:
            semaphore = self.semaphore

        if proxy:
            proxy = self.transform_proxy(proxy)
            proxy_auth = aiohttp.BasicAuth(self.user, self.password)

        # 强烈建议用session,3.5.4暂时没找到直接用get方法
        if not session:
            session = aiohttp

        if not method:
            method = 'GET'

        # 返回类型有text,content,json,暂时没有做类型检查
        if not response_type:
            response_type = 'text'

        if not success_code:
            success_code = [200, 201]

        url, headers = self.transform_url(url, headers)
        async with semaphore:
            try:
                async with session.request(method=method, url=url, proxy=proxy,
                                           proxy_auth=proxy_auth, timeout=timeout) as resp:
                    if resp.status in success_code:
                        if hasattr(resp, response_type):
                            func = getattr(resp, response_type, resp.text)
                        text = await func()

                        if parse and callable(parse):
                            return parse(text)
                        else:
                            return text

                    else:
                        raise Exception('发现反扒')

            except Exception as e:
                error_msg = '获取链接 {} 发现异常 {}'.format(url, e)
                if proxy:
                    error_msg += '代理{}'.format(proxy)
                logger.error(error_msg)
                if report_error:
                    raise

    # 单纯处理代理格式
    @staticmethod
    def transform_proxy(proxy):
        split_proxy = proxy.split(':')
        if len(split_proxy) == 3:
            proxy = '{}:{}'.format(*split_proxy[:-1])
        return 'http://' + proxy

    # 单纯封装url
    @staticmethod
    def transform_url(url=None, kwargs=None):
        host = urlparse(url).netloc

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/68.0.3440.75 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'Host': host
        }
        if isinstance(kwargs, dict):
            for k, v in kwargs.items():
                headers[k] = v
        return url, headers


def main():
    loop = asyncio.get_event_loop()
    # test_api='https://m.weibo.cn/api/container/getIndex?type=uid&value=1618385593'
    test_api = 'http://dev.task.hxsv.data.caasdata.com/?action=proxy_ips'
    cp = AsyncRequest()
    print(loop.run_until_complete(cp.request(url=test_api, response_type='json')))


if __name__ == '__main__':
    main()
