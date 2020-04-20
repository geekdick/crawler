import os
import re
from concurrent.futures import ThreadPoolExecutor
from urllib import parse
from urllib.parse import urlencode
import requests

from docs import project_conf
from utils.logger import logger

"""
基础类

vps_os_info: 获取vps固定信息

vps_proxy_info:获取vps代理信息
"""


class BaseCommands:

    def __init__(self):
        self.logger = logger()
        self.total_vps_count = 100
        self.proxy_dev_api = 'http://dev.task.hxsv.data.caasdata.com/?action=proxy_ips'
        self.vps_os_info_dict = dict()
        self.vps_static_status = ['vps_error', 'vps_success', 'os_success', 'os_fail', 'proxy_success', 'fail_ssh',
                                  'fail_ping']
        self.vps_status_dict = self.gen_vps_status_dict(self.vps_static_status)

    # 获取vps_names登录ssh信息
    def vps_os_info(self, vps_names=None, max_workers=None):
        vps_names = self.process_vps_names(vps_names)
        max_workers = self.get_max_thread_workers(max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as excutor:
            return list(excutor.map(self.single_vps_os_info, vps_names))

    def single_vps_os_info(self, vps_name):
        # 中间做了一层缓存,避免多次重复获取配置
        if vps_name in self.vps_os_info_dict:
            return self.vps_os_info_dict.get(vps_name)

        params = {'vpsname': vps_name, 'action': 'getinfo'}
        os_info = self.get_yunlifang_api(params)
        parse_vps_info = parse.parse_qs(os_info)
        self.logger.info('获取vps信息　{}'.format(os_info))
        vps_os_info_settings = {
            'hostname': parse_vps_info.get('ip')[0].split(':')[0],
            'username': 'root',
            'passwd': parse_vps_info.get('vpspassword')[0],
            'port': parse_vps_info.get('sshport')[0],
            'vpsname': parse_vps_info.get('vpsname')[0],
            'endtime': parse_vps_info.get('endtime')[0],
        }
        self.vps_os_info_dict[vps_name] = vps_os_info_settings
        return vps_os_info_settings

    # 根据vps_name获取对应的ip,如果vps_names为空,则返回所有vps对应的ip
    def vps_proxy_info(self, vps_names=None):
        vps_names = self.process_vps_names(vps_names)
        all_vps_proxy_dict = requests.get(self.proxy_dev_api).json()
        vps_proxy_dict = dict()
        for vps_name in vps_names:
            vps_ip = all_vps_proxy_dict.get(vps_name)
            if vps_ip:
                vps_proxy_dict[vps_name] = vps_ip
        return vps_proxy_dict

    # 生成vps_name,如果为100台,且格式为1
    def process_vps_names(self, vps_names=None, total_vps_count=100):
        if not total_vps_count:
            total_vps_count = self.total_vps_count
        if vps_names:

            vps_names = [vps_names] if isinstance(vps_names, str) else vps_names
            if str(vps_names[0]).isdigit():
                vps_names = ['huox{:0>3}'.format(int(i)) for i in vps_names]
                vps_names = [vps_names] if isinstance(vps_names, str) else vps_names
        else:
            vps_names = ['huox{:0>3}'.format(i) for i in range(1, total_vps_count + 1)]

        return vps_names

    @staticmethod
    def get_max_thread_workers(max_workers):
        cpu_count = os.cpu_count()

        return max(min(cpu_count, max_workers or 0), cpu_count * 2)

    # 兼容传入vps_name或者vps具体信息
    def check_vps_params(self, vps_name, vps_os_info_dict):
        if not vps_os_info_dict:
            if isinstance(vps_name, str):
                vps_os_info_dict = self.single_vps_os_info(vps_name)
            else:
                raise ValueError('传入参数错误')

        if not vps_name:
            vps_name = vps_os_info_dict.get('vpsname')

        return vps_name, vps_os_info_dict

    # 调用云立方api
    def get_yunlifang_api(self, params):
        params.update(project_conf.YUNLIFANG_BASE_PARAM)
        url = project_conf.YUNLIFANG_API + '?' + urlencode(params)
        try:
            req = requests.get(url=url, headers=project_conf.BASE_HEADERS)
            return req.text
        except Exception as e:
            self.logger.info('请求url {} 发生异常{}'.format(url, e))

    # 获取vps os_id,重装系统需要的参数
    def get_os_id(self, vps_name, vps_os_name="Centos 7.1"):
        params = {'vpsname': vps_name, 'action': 'getos'}
        result = self.get_yunlifang_api(params=params)
        os_infos = re.findall(r'\[(.*?)\],', result)
        os_info_dict = dict()
        vps_os_id = 0
        for item in os_infos:
            os_id, os_name = item.split(',')
            os_info_dict[eval(os_name)] = eval(os_id)
            if vps_os_name in os_name:
                vps_os_id = eval(os_id)

        if vps_os_id:
            self.logger.info('获取　{} os_id {}'.format(vps_os_name, vps_os_id))
            return int(vps_os_id)
        else:
            raise Exception('{} 类型os 不存在 ,请从以下几种类型选择 {}'.format(vps_os_name, os_info_dict))

    @staticmethod
    def gen_vps_status_dict(vps_status_list):
        vps_status_dict = dict()

        for index, vps_status in enumerate(vps_status_list):
            vps_status_dict[index] = vps_status
            vps_status_dict[vps_status] = index

        return vps_status_dict


if __name__ == '__main__':
    base_command = BaseCommands()
    # print(base_command.process_vps_names())
    # print(base_command.vps_proxy_info())
    # print(base_command.vps_os_info())
    print(base_command.vps_os_info(vps_names=[1, 2, 3, 5]))
    print(base_command.vps_status_dict)
    # print(base_command.get_os_id(vps_name='huox001'))
