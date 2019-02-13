import rsa


class RsaDemo(object):
    """
    生成密钥可保存.pem格式文件
    1024位的证书，加密时最大支持117个字节，解密时为128；
    2048位的证书，加密时最大支持245个字节，解密时为256。
    加密大文件时需要先用AES或者DES加密，再用RSA加密密钥，详细见文档
    文档:https://stuvel.eu/files/python-rsa-doc/usage.html#generating-keys
    """

    def __init__(self, number=1024):
        """
        :param number: 公钥、私钥
        """
        self.public_key, self.private_key = rsa.newkeys(number)

    def encrypt_oracle(self, content):
        crypto = rsa.encrypt(content.encode('utf-8'), self.public_key)
        return crypto

    def decrypt_oracle(self, content):
        decrypt_text = rsa.decrypt(content, self.private_key)
        return decrypt_text.decode('utf-8')


if __name__ == '__main__':
    rsa_demo = RsaDemo()
    text = 'abcd4321sdfsd'
    encrypt_result = rsa_demo.encrypt_oracle(text)
    print(encrypt_result)
    print(rsa_demo.decrypt_oracle(encrypt_result))
