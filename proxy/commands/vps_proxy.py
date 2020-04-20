import asyncio

from commands import BaseCommands
import time
import aiohttp
from collections import defaultdict

from docs.project_conf import TEST_API_LIST
from utils.check_proxy import AsyncRequest
import random

""""
检测vps代理可用性
:parallel_count 协程并发数，默认是50
:timeout 请求超时时间
:loop_times 对代理进行几次检测，小于等于0会无限伦询
:interval_time 每次伦询间隔时间，最小0.1s
:parse_html 对异步请求页面的处理，比如返回响应内容或者是返回代理信息，默认返回代理信息

"""


class CheckVpsProxy(BaseCommands):

    def __init__(self, parallel_count=50, timeout=5, interval_time=5, loop_times=5):
        super().__init__()
        self.test_api = random.sample(TEST_API_LIST, 1)[0]
        self.proxy_dev_api = 'http://dev.task.hxsv.data.caasdata.com/?action=proxy_ips'
        self.async_request = AsyncRequest(parallel_count=parallel_count, timeout=timeout)
        self.interval_time = interval_time or 5
        self.loop_times = loop_times or 5

    # loop_times小于等于0会无线循环
    def run(self, vps_names=None, loop_times=None, interval_time=None, parse_html=None):
        if loop_times is None:
            loop_times = self.loop_times

        if interval_time is None:
            interval_time = self.interval_time

        loop = asyncio.get_event_loop()
        vps_score = defaultdict(int)
        has_loop_count = 1
        while 1:
            proxy_dict = self.vps_proxy_info(vps_names=vps_names)
            self.logger.info('获取到 vps 代理信息为 {}'.format(proxy_dict))
            all_useful_proxy = loop.run_until_complete(self.check_proxy(proxy_dict=proxy_dict, parse_html=parse_html))
            self.logger.info('第{} 伦,检测可用代理有{}'.format(has_loop_count, len(all_useful_proxy)))
            for vps_name in proxy_dict:
                if vps_name not in all_useful_proxy:
                    vps_score[vps_name] -= 1
                else:
                    vps_score[vps_name] -= 0
            if loop_times == has_loop_count:
                break
            has_loop_count += 1
            time.sleep(max(interval_time, 0.1))
        vps_useful_result = self.count_proxy_quality(vps_score)
        return vps_useful_result

    async def check_proxy(self, proxy_dict, parse_html=None):

        if not parse_html:
            def callback(item):
                return lambda _: item

            parse_html = callback

        async with aiohttp.ClientSession() as session:
            completed, pending = await asyncio.wait(
                [self.async_request.request(session=session, url=self.test_api, proxy=item[1], parse=parse_html(item))
                 for item in proxy_dict.items()])

        useful_proxy = dict()
        for item in completed:
            proxy = item.result()
            if proxy:
                vps_name, ip = proxy
                useful_proxy[vps_name] = ip

        return useful_proxy

    @staticmethod
    def count_proxy_quality(vps_score):
        proxy_quality = defaultdict(list)
        for vps_name, score in vps_score.items():
            proxy_quality[score].append(vps_name)
        return proxy_quality


if __name__ == '__main__':
    command = CheckVpsProxy(parallel_count=100)
    # print(command.run(loop_times=1, interval_time=0))
    # print(command.run(loop_times=1))
    command.run(vps_names='huox038')