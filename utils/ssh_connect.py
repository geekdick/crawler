# coding:utf-8

import paramiko
import requests

from docs import project_conf


class SSHConnection(object):

    def __init__(self, server_info_dict):
        self.hostname = server_info_dict.get('hostname')
        self.port = int(server_info_dict.get('port'))
        self.username = server_info_dict.get('username')
        self.passwd = server_info_dict.get('passwd')
        self.auto_close = server_info_dict.get('auto_close')
        self.timeout = server_info_dict.get('timeout') or 300
        self.__k = None
        self.__transport = None

    def connect(self):
        transport = paramiko.Transport((self.hostname, self.port))
        transport.connect(username=self.username, password=self.passwd)
        self.__transport = transport

    def close(self):
        if self.__transport:
            self.__transport.close()
            del self.__transport

    def command(self, command):
        if not self.__transport:
            self.connect()
        ssh = paramiko.SSHClient()
        ssh._transport = self.__transport
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read()
        if self.auto_close:
            self.close()
        return result

    def upload(self, local_path, target_path):
        if not self.__transport:
            self.connect()
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.put(local_path, target_path, confirm=True)
        sftp.chmod(target_path, 0o755)
        if self.auto_close:
            self.close()

    def download(self, target_path, local_path):
        if not self.__transport:
            self.connect()
        # 连接，下载
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        # 将location.py 下载至服务器 /tmp/test.py
        sftp.get(target_path, local_path)
        if self.auto_close:
            self.close()


def main():
    server_info_dict = {'port': '20067', 'username': 'root', 'endtime': '2019-03-13 10:50:53', 'vpsname': 'huox053',
                        'passwd': 'huox201408', 'hostname': '222.212.90.104'}
    sscon = SSHConnection(server_info_dict=server_info_dict)
    print(sscon.command('pwd'))
    # print(sscon.command('ping baidu.com -c 5'))
    print(sscon.command('find adsl.bash'))
    print(sscon.command('find cc'))
    print(sscon.command('crontab -l'))
    print(sscon.command('/root/proxy.bash huox053'))


if __name__ == '__main__':
    main()
