import base64
from Crypto.Cipher import AES


class AesDemo(object):

    def __init__(self, salt):
        """
        AES
        除了MODE_SIV模式key长度为：32, 48, or 64,
        其余key长度为16, 24 or 32
        详细见AES内部文档
        CBC模式传入iv参数
        本例使用常用的ECB模式
        """
        if len(salt) > 32:
            salt = salt[:32]
        self.key = self.add_to_16(salt)
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
    rsa_demo = AesDemo(salt='12345sdfsdfcwefcdsfvdsvfcdscvfdsvc6')
    text = 'abcd4321sdfsd'
    encrypt_result = rsa_demo.encrypt_oracle(text)
    print(encrypt_result)
    print(rsa_demo.decrypt_oracle(encrypt_result))
