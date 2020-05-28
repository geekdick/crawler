import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

def mail(title, content, to_addrs=None, from_addr=None, password=None, attachment=None):
    '''
    发送邮件函数
    :param title: 邮件标题
    :param content: 邮件内容 type: str
    :param to_addrs: 收件人  type: list
    :param from_addr: 寄件人地址
    :param password: 寄件人登录密码
    :return: None
    '''
    if not isinstance(to_addrs, list):
        to_addrs = [to_addrs]

    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    if from_addr is None:
        from_addr = 'webmaster@huox.tv'

    if password is None:
        password = 'HUOxing201408'

    if to_addrs is None:
        to_addrs = ['liuxuejun@huox.tv']

    smtp_server = 'smtp.mxhichina.com'
    msg = MIMEMultipart()
    if attachment and os.path.isfile(attachment):
        with open(attachment, 'r') as f:
            # mime = MIMEBase('text', 'txt', filenmae=attachment)
            mime = MIMEText(f.read(), _charset='utf-8')
            mime.add_header('Content-Disposition', 'attachment', filename=attachment)
            msg.attach(mime)
    msg['From'] = _format_addr('发件人 <%s>' % from_addr)
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    to_addrs_msg = [_format_addr('收件人 <%s>' % s) for s in to_addrs]
    msg['To'] = ','.join(to_addrs_msg)
    msg['Subject'] = Header(title, 'utf-8').encode()
    server = smtplib.SMTP_SSL(smtp_server, timeout=10)
    server.set_debuglevel(0)
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addrs, msg.as_string())
    server.quit()
