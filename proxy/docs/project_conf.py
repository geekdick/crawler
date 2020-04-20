MAILLIST = {
    'recivers': [
        'wanggeyou@huox.tv',
        'liuxuejun@huox.tv',
        'zhaohui@huox.tv',
    ],
}

YUNLIFANG_API = 'http://api.yunlifang.cn/api/cloudapi.asp'

YUNLIFANG_BASE_PARAM = {
    "userid": "13718291025",
    "userstr": "924c8a062c0bb750c87064fc596e3639",
    "attach": "ceshi",
    "openX": "执行"
}

BASE_HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/67.0.3396.62 Safari/537.36'}

TEST_API_LIST = ['http://www.baidu.com/index.php?tn=baidudg']

PING_COMANDS = ['ping baidu.com -c 10']

if __name__ == '__main__':
    import random

    print(random.sample(TEST_API_LIST, 1))
