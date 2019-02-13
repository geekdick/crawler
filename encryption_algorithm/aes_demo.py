import base64
from Crypto.Cipher import AES


class AesDemo(object):

    def __init__(self, salt):
        self.salt = salt
        self.aes = AES.new(self.add_to_16(salt), AES.MODE_ECB)

    # 加密方法
    def encrypt_oracle(self, content):
        # 先进行aes加密
        encrypt_aes = self.aes.encrypt(self.add_to_16(content))
        # 用base64转成字符串形式
        encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')  # 执行加密并转码返回bytes
        return encrypted_text

    # 解密方法
    def decrypt_oracle(self, content):
        # 优先逆向解密base64成bytes
        base64_decrypted = base64.decodebytes(content.encode(encoding='utf-8'))
        # 执行解密密并转码返回str
        decrypted_text = str(self.aes.decrypt(base64_decrypted), encoding='utf-8').replace('\0', '')
        return decrypted_text

    # str不是16的倍数那就补足为16的倍数
    @staticmethod
    def add_to_16(value):
        while len(value) % 16 != 0:
            value += '\0'
        return str.encode(value)  # 返回bytes


if __name__ == '__main__':
    aes = AesDemo(salt='123456')
    content = 'abcd4321'
    encrypt_result = aes.encrypt_oracle(content)
    print(encrypt_result)
    print(aes.decrypt_oracle(encrypt_result))
