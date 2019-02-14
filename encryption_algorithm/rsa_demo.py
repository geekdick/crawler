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

    def sign(self, message, private_key=None, hash_method='SHA-1'):
        if not private_key:
            private_key = self.private_key
        return rsa.sign(message.encode(), private_key, hash_method)

    def verify(self, message, encrypt_message, public_key=None):
        if not public_key:
            public_key = self.public_key
        return rsa.verify(message, encrypt_message, public_key)

    @staticmethod
    def save_pem(pem_path, key_content):
        with open(pem_path, 'bw') as f:
            f.write(key_content.save_pkcs1())

    @staticmethod
    def read_pem(pem_path, is_public=True):
        with open(pem_path, 'r') as f:
            if is_public:
                return rsa.PublicKey.load_pkcs1(f.read().encode())
            else:
                return rsa.PrivateKey.load_pkcs1(f.read().encode())


if __name__ == '__main__':
    rsa_demo = RsaDemo()
    rsa_demo.save_pem('public.pem', rsa_demo.public_key)
    rsa_demo.save_pem('private.pem', rsa_demo.private_key)
    print('public_pem', rsa_demo.read_pem('public.pem'))
    print('private_pem', rsa_demo.read_pem('private.pem', is_public=False))
    text = 'abcd4321sdfsd'
    encrypt_result = rsa_demo.encrypt_oracle(text)
    print(encrypt_result)
    print(rsa_demo.decrypt_oracle(encrypt_result))
    encrypt_text = rsa_demo.sign('nihaoya', private_key=rsa_demo.read_pem('private.pem', is_public=False))
    print(encrypt_text)
    print(rsa_demo.verify('nihaoya'.encode(), encrypt_text, public_key=rsa_demo.read_pem('public.pem')))
