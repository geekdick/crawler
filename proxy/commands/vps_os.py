import os
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib import parse

from commands import BaseCommands
from docs.project_conf import PING_COMANDS
from utils.ssh_connect import SSHConnection
from utils.util import bytes_to_str
from datetime import datetime, timedelta
import time


class CheckVpsOs(BaseCommands):

    def __init__(self, ping_command=None):
        super().__init__()
        self.ping_command = ping_command or random.sample(PING_COMANDS, 1)[0]
        self.proxy_bash_path = os.path.join(os.path.dirname(__file__), '../docs/proxy.bash')
        if not os.path.isfile(self.proxy_bash_path):
            raise Exception('proxy bash {} 路径错误'.format(self.proxy_bash_path))

    def auto_check_reinstall_multi_vps(self, vps_names=None, max_workes=None):
        """
        对外暴露的函数：
        执行步骤为:
        一:如果不指定vps name 则检查所有vps status　否则直接对指定vps 进行重启
        二：出现问题vps 重新安装脚本
        三：新一轮检查　vps status
        四：重新安装　vps os
        五：新一轮检查　vps status
        """
        fail_vps_set = set()
        if not vps_names:
            all_vps_status = self.check_multi_vps_status(vps_names=vps_names, max_workers=max_workes)
            fail_ssh_vps = all_vps_status.get(self.vps_status_dict.get('fail_ssh'))
            fail_ping_vps = all_vps_status.get(self.vps_status_dict.get('fail_ping'))
            if fail_ssh_vps:
                fail_vps_set.update(fail_ssh_vps)
            if fail_ping_vps:
                fail_vps_set.update(fail_ping_vps)
        else:
            vps_names = self.process_vps_names(vps_names=vps_names)
            fail_vps_set.update(vps_names)
        # 重新配置环境
        self.set_multi_vps_environment(vps_names=list(fail_vps_set))

        # 重新检测问题vps
        all_vps_status = self.check_multi_vps_status(vps_names=list(fail_vps_set), max_workers=max_workes)
        os_success_vps = all_vps_status.get(self.vps_status_dict.get('os_success'))
        if os_success_vps:
            self.logger.info('重新配置环境修复成功vps 有{}'.format(os_success_vps))
            fail_vps_set = set(fail_vps_set) - set(os_success_vps)

        # 重新配置环境
        if fail_vps_set:
            self.reinstall_multi_vps(vps_names=list(fail_vps_set))
            # 重新检测问题vps
            all_vps_status = self.check_multi_vps_status(vps_names=list(fail_vps_set), max_workers=max_workes)
            os_success_vps = all_vps_status.get(self.vps_status_dict.get('os_success'))
            if os_success_vps:
                self.logger.info('重装系统修复成功vps 有{}'.format(os_success_vps))
                fail_vps_set = set(fail_vps_set) - set(os_success_vps)

        if fail_vps_set:
            self.logger.error('无法自动修复的vps {}'.format(fail_vps_set))
        else:
            self.logger.info('所有vps 经自动修复均已正常')

        return fail_vps_set

    # 多线程监测多个vps_os_status
    def check_multi_vps_status(self, vps_names=None, max_workers=None):
        max_workers = self.get_max_thread_workers(max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as excutor:
            result = list(excutor.map(self.check_single_vps_status, vps_names))

        return self.count_vps_os_status(result)

    def reinstall_multi_vps(self, vps_names=None, max_workers=None):
        max_workers = self.get_max_thread_workers(max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as excutor:
            result = list(excutor.map(self.reinstall_single_vps, vps_names))

        return result

    def set_multi_vps_environment(self, vps_names=None, max_workers=None):
        max_workers = self.get_max_thread_workers(max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as excutor:
            result = list(excutor.map(self.set_vps_environment, vps_names))

        return result

    def restart_multi_vps(self, vps_names=None, max_workers=None):
        max_workers = self.get_max_thread_workers(max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as excutor:
            result = list(excutor.map(self.restart_single_vps, vps_names))

        return result

    # 适用于单个vps检测
    def check_single_vps_status(self, vps_name=None, vps_os_info_dict=None):
        vps_name, vps_os_info_dict = self.check_vps_params(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)
        self.logger.info('开始检测vps {} 网络连接情况'.format(vps_name))
        vps_status = dict()
        vps_status['name'] = vps_name
        try:
            ssh_connect = SSHConnection(server_info_dict=vps_os_info_dict)
            result = ssh_connect.command(self.ping_command)
            if bytes_to_str(result):
                vps_status['status'] = self.vps_status_dict.get('os_success')
                self.logger.info('vps {} 远程连接成功'.format(vps_name))
            else:
                vps_status['status'] = self.vps_status_dict.get('fail_ping')
                self.logger.error('vps {} 无法ping 成功'.format(vps_name))
        except Exception as e:
            vps_status['status'] = self.vps_status_dict.get('fail_ssh')
            self.logger.error('vps {} 无法连接ssh {}'.format(vps_name, e))

        return vps_status

    def restart_single_vps(self, vps_name=None, vps_os_info_dict=None):
        try:
            vps_name, vps_os_info_dict = self.check_vps_params(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)
            self.logger.info('开始重启vps {}'.format(vps_name))
            params = {'vpsname': vps_name, 'op': 'reset', 'action': 'vpsop'}
            restart_vps_result_str = self.get_yunlifang_api(params=params)
            time.sleep(1)  # 重启会设置休眠1s
            restart_vps_result = parse.parse_qs(restart_vps_result_str)
            if restart_vps_result.get('ret')[0] == 'ok':
                self.logger.info('{} 重启指令发送成功 {}'.format(vps_name, restart_vps_result_str))
            else:
                raise Exception('返回结果为{}'.format(restart_vps_result))
        except Exception as e:
            self.logger.error('重启 vps {} 发现意外 {}'.format(vps_name, e))

    # 重装系分为三步：一：重装os,二：安装脚本,三：检查联网情况
    def reinstall_single_vps(self, vps_name=None, vps_os_info_dict=None, retry_count=5):

        self.install_single_vps(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)
        has_set_vps_environment = 0
        while retry_count:
            time.sleep(60)
            try:
                if not has_set_vps_environment:
                    has_set_vps_environment = self.set_vps_environment(vps_name=vps_name,
                                                                       vps_os_info_dict=vps_os_info_dict)
                vps_status = self.check_single_vps_status(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)
                if int(self.vps_status_dict.get('os_success')) == int(vps_status.get('status')):
                    self.logger.info('{}　重装成功'.format(vps_name))
                    return vps_name
                else:
                    raise Exception(
                        '{} 重装失败，原因是　{}'.format(vps_name, self.vps_status_dict.get(vps_status.get('status'))))
            except Exception as e:
                retry_count -= 1
                self.logger.error('重装 {}  {}失败,还有{} 次重装机会'.format(vps_name, e, retry_count))
        self.logger.info('{} 重试次数耗完,网络连接测试失败'.format(vps_name))

    def install_single_vps(self, vps_name=None, vps_os_info_dict=None):
        try:
            vps_name, vps_os_info_dict = self.check_vps_params(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)

            self.logger.info('开始重新安装vps {}'.format(vps_name))

            params = {'vpsname': vps_name, 'osid': self.get_os_id(vps_name=vps_name), 'action': 'installos'}
            reinstall_vps_result_str = self.get_yunlifang_api(params=params)
            reinstall_vps_result = parse.parse_qs(reinstall_vps_result_str)
            if reinstall_vps_result.get('ret')[0] == 'ok':
                self.logger.info('{} 系统安装指令发送成功 {}'.format(vps_name, reinstall_vps_result_str))
            else:
                raise Exception('返回结果为{}'.format(reinstall_vps_result))
        except Exception as e:
            self.logger.error('安装系统 vps {} 发现意外 {}'.format(vps_name, e))

    def renew_single_vps(self, vps_name=None, vps_os_info_dict=None, renew_months=1):
        try:
            vps_name, vps_os_info_dict = self.check_vps_params(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)
            expire_time = vps_os_info_dict.get('endtime')
            expire_time = datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
            expect_time = datetime.now() + timedelta(renew_months * 30)
            if expire_time < expect_time:
                params = {'vpsname': vps_name, 'year': '1', 'diynum': renew_months,
                          'years': 'months', 'action': 'renew'}

                renew_vps_result_str = self.get_yunlifang_api(params=params)
                renew_vps_result = parse.parse_qs(renew_vps_result_str)
                if renew_vps_result.get('ret')[0] == 'ok':
                    self.logger.info('{} 续费成功,到期时间为{}'.format(vps_name, renew_vps_result.get('endtime')[0]))
                else:
                    raise Exception()
            else:
                self.logger.info('{} vps 到期时间 {} 无需续费'.format(vps_name, expire_time))
        except Exception as e:
            self.logger.error('续费 vps {} 发现意外 {}'.format(vps_name, e))

    # 重新安装脚本
    def set_vps_environment(self, vps_name=None, vps_os_info_dict=None):
        try:
            vps_name, vps_os_info_dict = self.check_vps_params(vps_os_info_dict=vps_os_info_dict, vps_name=vps_name)
            ssh_connect = SSHConnection(server_info_dict=vps_os_info_dict)
            ssh_connect.upload(self.proxy_bash_path, '/root/proxy.bash')
            ssh_connect.command('chmod 777 /root/proxy.bash')
            ssh_connect.command('systemctl stop firewalld')
            ssh_connect.command('/root/proxy.bash  {}'.format(vps_name))
            ssh_connect.command('/root/adsl.bash')
            file_exist = bytes_to_str(ssh_connect.command('find adsl.bash'))
            crontab_exist = bytes_to_str(ssh_connect.command('crontab -l'))
            ssh_connect.close()
            if file_exist and crontab_exist:
                self.logger.info('vps {} 环境设置完成'.format(vps_name))
                return vps_name
            else:
                raise Exception('file exist {} ; crontab_exist {}'.format(file_exist, crontab_exist))
        except Exception as e:
            self.logger.exception('设置 vps {} 环境发现意外 {}'.format(vps_name, e))

    def count_vps_os_status(self, vps_status_list):
        vps_status_dict = defaultdict(list)
        for vps_status in vps_status_list:
            status = vps_status.get('status')
            name = vps_status.get('name')
            if not status == self.vps_status_dict.get('os_success'):
                vps_status_dict[self.vps_status_dict.get('os_fail')].append(name)
            vps_status_dict[status].append(name)

        return vps_status_dict


if __name__ == '__main__':
    check_vps_os = CheckVpsOs()
    # print(check_vps_os.check_multi_vps_status())
    # check_vps_os.renew_single_vps(vps_name='huox001')
    # check_vps_os.reinstall_single_vps(vps_name='huox001')
    # check_vps_os.check_single_vps_status(vps_name='huox001')
    # check_vps_os.restart_single_vps(vps_name='huox001')
    # time.sleep(5)
    check_vps_os.set_vps_environment(vps_name='huox001')
    check_vps_os.check_single_vps_status(vps_name='huox001')
    # print(check_vps_os.check_multi_vps_status())
    # print(check_vps_os.auto_check_reinstall_multi_vps(['huox001']))
    # print(check_vps_os.reinstall_multi_vps(['huox042']))
    # 'huox077', 'huox059'
