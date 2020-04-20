import logging
import os
import sys
import time
import weakref
from copy import deepcopy
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler


class MultiTimeRotatingFileHandle(TimedRotatingFileHandler):

    def __init__(self, filename, when, interval, backup_count, encoding=None, delay=False, utc=False,
                 at_time=None, handel_file_callback=None):

        TimedRotatingFileHandler.__init__(self, filename, when=when, interval=interval, backupCount=backup_count,
                                          encoding=encoding, delay=delay, utc=utc, atTime=at_time)
        self.handel_file_callback = handel_file_callback

    def computeRollover(self, current_time):
        # 将时间取整
        t_str = time.strftime(self.suffix, time.localtime(current_time))
        t = time.mktime(time.strptime(t_str, self.suffix))
        return TimedRotatingFileHandler.computeRollover(self, t)

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.

        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dst_then = time_tuple[-1]
            if dst_now != dst_then:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dfn = self.rotation_filename(self.baseFilename + "." +
                                     time.strftime(self.suffix, time_tuple))
        if not os.path.exists(dfn):
            try:
                if os.path.exists(self.baseFilename):
                    self.rotate(self.baseFilename, dfn)
            except FileNotFoundError:
                # 这里会出异常：未找到日志文件，原因是其他进程对该日志文件重命名了，忽略即可，当前日志不会丢失
                pass

        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                try:
                    if os.path.isfile(s):
                        if self.handel_file_callback and callable(self.handel_file_callback):
                            self.handel_file_callback(s)
                    if os.path.exists(s):
                        os.remove(s)
                except Exception as e:
                    print(e)
        if not self.delay:
            self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at


class MultiRotatingFileHandler(RotatingFileHandler):

    def __init__(self, filename, max_bytes, backup_count=0, encoding=None, delay=False, handel_file_callback=None):

        RotatingFileHandler.__init__(self, filename, maxBytes=max_bytes, backupCount=backup_count,
                                     encoding=encoding, delay=delay)
        self.handel_file_callback = handel_file_callback

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d" % (self.baseFilename, i))
                dfn = self.rotation_filename("%s.%d" % (self.baseFilename,
                                                        i + 1))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        try:
                            if os.path.isfile(dfn):
                                if self.handel_file_callback and callable(self.handel_file_callback):
                                    self.handel_file_callback(dfn)
                                if os.path.exists(dfn):
                                    os.remove(dfn)
                        except Exception as e:
                            print(e)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename + ".1")

            if not os.path.exists(dfn):
                try:
                    if os.path.exists(self.baseFilename):
                        self.rotate(self.baseFilename, dfn)
                except FileNotFoundError:
                    # 这里会出异常：未找到日志文件，原因是其他进程对该日志文件重命名了，忽略即可，当前日志不会丢失
                    pass
        if not self.delay:
            self.stream = self._open()


logger_cache = dict()


class Logger(object):
    """"
    相比于标准库logger增加多进程兼容,对timerote和file rotate进行一层封装
    logger_type:定义一类log文件的文件夹名字,默认default
    prefix:log文件前缀名字,默认是当前运行脚本名字
    file_level:文件handle等级,默认是logger_type是default为error,否则为debug,error,所以error和debug各存一份
    level:日志打印等级,默认debug
    use_file_rotate:是否使用file rotate

    实际工作中配置参数可以单独抽离出来,做到灵活定制
    """

    __logger_cache = weakref.WeakValueDictionary()
    __base_dirname = 'logger_file'
    time_rotate_file_handle_config = {
        'level': 'error',
        'when': 'D',
        'backup_count': 7,
        'interval': 1
    }
    file_rotate_file_handle_config = {
        'level': 'error',
        'max_bytes': 1024 * 1024 * 20,
        'backup_count': 3,

    }
    _Level_list = ['critical', 'error', 'warning', 'info', 'debug', 'notset']

    def __new__(cls, prefix, logger_type, **kwargs):
        if prefix in logger_cache:
            return logger_cache[prefix]
        else:
            self = super().__new__(cls)
            self.log = self.get_logger(prefix=prefix, logger_type=logger_type, **kwargs)
            logger_cache[prefix] = self
            return self

    def get_logger(self, logger_type, prefix, file_levels=None, spec_config=None, use_file_rotate=False, level=None):

        if not level:
            level = 'debug'
        if not spec_config:
            spec_config = {
                'level': level
            }

        if not file_levels:
            if logger_type == 'default':
                file_levels = ['error']
            else:
                file_levels = ['debug', 'error']
        prefix = self.get_prefix(prefix)
        # 历史原因,有些logger实例没有初始化logger_type,所以同一进程下不同logger需要logger_type和prefix均不同
        loggers = logging.getLogger(name=prefix)
        loggers.handlers = []
        loggers.setLevel(spec_config.get('level').upper())
        for levels in file_levels:
            if use_file_rotate:
                config = deepcopy(self.file_rotate_file_handle_config)

            else:
                config = deepcopy(self.time_rotate_file_handle_config)
            config.update(spec_config)
            config.update({
                'level': levels
            })
            file_path = self.get_logger_file_path(prefix=prefix, logger_type=logger_type, level=config.get('level'))
            file_handle = self.add_handler(file_path=file_path, **config)
            loggers.addHandler(file_handle)
        stream_handle = self.add_handler(spec_config.get('level'))
        loggers.addHandler(stream_handle)
        return loggers

    @classmethod
    def get_logger_file_path(cls, prefix=None, logger_type=None, level='debug'):
        if not logger_type:
            logger_type = 'default'
        prefix = cls.get_prefix(prefix)
        file_name = '_'.join([prefix, level])
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.sep.join([cls.__base_dirname, logger_type]))
        dir_path = os.path.join(dir_path, level)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        file_path = os.path.join(dir_path, os.path.basename(file_name))
        return file_path

    @classmethod
    def get_prefix(cls, prefix):
        if not prefix:
            prefix = os.path.basename(sys.argv[0]).split('.')[0]
        return prefix

    @classmethod
    def add_handler(cls, level=None, when=None, backup_count=None, interval=None, file_path=None, max_bytes=None,
                    handel_file_callback=None):
        formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        if max_bytes:
            handler = MultiRotatingFileHandler(filename=file_path, max_bytes=max_bytes, backup_count=backup_count)
        elif when:
            handler = MultiTimeRotatingFileHandle(filename=file_path, interval=interval, when=when,
                                                  backup_count=backup_count, handel_file_callback=handel_file_callback)
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level.upper())
        return handler


def logger(logger_type=None, prefix=None, use_file_rotate=False, **kwargs):
    if not logger_type:
        logger_type = 'default'
    if not prefix:
        prefix = os.path.basename(sys.argv[0]).split('.')[0]
    return Logger(prefix=prefix, logger_type=logger_type, use_file_rotate=use_file_rotate, **kwargs).log


def test_file_rotate():
    a = logger(use_file_rotate=True)
    time.sleep(10)
    for i in range(1000):
        a.error('测试 file rotate {}'.format(i))


def test_logger():
    a = logger()
    b = logger()
    c = logger()
    print(id(a))
    print(id(b))
    print(id(c))


def test_get_logger_file_path():
    print(Logger.get_logger_file_path())


if __name__ == '__main__':
    # test_logger()
    test_file_rotate()
