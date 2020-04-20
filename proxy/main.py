import os
import sys

base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path)))

import time

from commands import BaseCommands
from commands.vps_os import CheckVpsOs
from commands.vps_proxy import CheckVpsProxy
from docs.project_conf import MAILLIST
from utils import mail
from utils.util import kill_process

"""
代理程序执行入口
install 重装vps　0重装全部,可指定多台　如python3 main.py install 1,2,3,4
repair 修复vps 0修复全部,可指定多台　如python3 main.py repair 1,2,3,4

"""


class ProxyManage(BaseCommands):

    def __init__(self):
        super().__init__()
        self.check_vps_proxy = CheckVpsProxy(parallel_count=100, timeout=10)
        self.check_vps_os = CheckVpsOs()

    def run(self, loop_times=5, forever_run=False):
        while True:
            # 检查代理情况
            send_mail = self.send_mail()
            vps_useful_result = self.check_vps_proxy.run(loop_times=loop_times)
            logger_contents = self.gen_check_proxy_contents(vps_useful_result=vps_useful_result, loop_times=loop_times)
            send_mail(logger_contents)

            # 检查代理异常机器情况
            need_check_os_vps = vps_useful_result.get(-loop_times + 1, []) + vps_useful_result.get(
                -loop_times, [])
            send_mail(
                '对超过　{}次无法使用的vps 总计{} {}进行初步系统检查'.format(loop_times - 2, len(need_check_os_vps), need_check_os_vps))
            error_proxy_os_status = self.check_vps_os.check_multi_vps_status(vps_names=need_check_os_vps)
            logger_contents = self.gen_check_os_status(error_proxy_os_status)
            send_mail(logger_contents)

            # 即使能联网也要重装系统
            # need_check_os_vps = error_proxy_os_status.get(self.vps_status_dict.get('os_fail')) or []

            # 重新安装(重启)vps
            if need_check_os_vps:
                fail_repair_proxy = self.check_vps_os.auto_check_reinstall_multi_vps(vps_names=need_check_os_vps)
                if len(fail_repair_proxy):
                    send_mail('无法自动修复的修复的vps {}台 {}'.format(len(fail_repair_proxy), fail_repair_proxy))
                else:
                    send_mail('所有vps 均通过检测')

            # 发送邮件
            send_mail()
            if not forever_run:
                break
            time.sleep(3000)

    def send_mail(self):
        mail_content_line = []

        def add_content_line(content=None):
            if content:
                mail_content_line.append(content)
            else:
                content = ('\n'.join(mail_content_line))
                self.logger.info(content)
                mail(content=content, title='VPS定时提醒', to_addrs=MAILLIST.get('recivers'))

        return add_content_line

    @staticmethod
    def gen_check_proxy_contents(vps_useful_result, loop_times):
        logger_contents = list()
        logger_contents.append('一共经过{} 伦检测，具体情况如下'.format(loop_times))
        for fail_count, vps_names in vps_useful_result.items():
            logger_contents.append('成功{}次,有 {}台，vps分别为 {}'.format(loop_times + fail_count, len(vps_names), vps_names))

        return '\n'.join(logger_contents)

    def gen_check_os_status(self, vps_status_dict):
        logger_contents = list()
        for status, vps_names in sorted(vps_status_dict.items()):
            logger_contents.append(
                '系统 {} 有 {}台，vps分别为 {}'.format(self.vps_status_dict.get(status), len(vps_names), vps_names))

        return '\n'.join(logger_contents)


if __name__ == '__main__':
    kill_process(os.path.basename(base_path))

    proxy_manager = ProxyManage()
    proxy_manager.run(forever_run=True)
