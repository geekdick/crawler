from datetime import datetime
import os
# 二进制转文本
import re
from collections import deque


def bytes_to_str(s, encoding='utf-8'):
    """Returns a str if a bytes object is given."""
    if isinstance(s, bytes):
        return s.decode(encoding)
    return s


def kill_process(path):
    command = 'ps -ef |grep {}'.format(path)
    process_list = os.popen(command).readlines()
    if process_list:
        for process in process_list:
            process_id = process.split()[1]
            if int(process_id) == int(os.getpid()):
                continue
            os.popen('kill -9 {}'.format(process_id))


def read_line(file_path, limit=10, pattern='.', reverse=True):
    previous_lines = deque(maxlen=limit)
    pattern = re.compile(r'{}'.format(pattern), re.S)
    with open(file_path) as lines:
        for line in lines:
            if re.search(pattern, line):
                previous_lines.append(line)
                if not reverse and len(previous_lines) == limit:
                    break
    return ''.join(previous_lines)


def same_time(kind='hour'):
    last_time = dict()

    def check_time(times=None):
        if not isinstance(times, datetime):
            times = datetime.now()
        this_kind_time = getattr(times, kind)
        if last_time.get(kind) == this_kind_time:
            is_same = True
        else:
            is_same = False
            last_time[kind] = this_kind_time
        return is_same

    return check_time


def test_same_time():
    same_second = same_time(kind='second')
    print(same_second())  # False,初始值为false
    time.sleep(1)
    print(same_second())  # False
    time.sleep(0.5)
    print(same_second())  # True


if __name__ == '__main__':
    import time
    test_same_time()
    # content = read_line(file_path=__file__, reverse=False, pattern='\S')
    # print(content)
