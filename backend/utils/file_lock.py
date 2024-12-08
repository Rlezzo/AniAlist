# file_lock.py
import os
import time

class FileLock:
    def __init__(self, lock_file_path, expiration_time=30):
        """
        初始化文件锁
        :param lock_file_path: 锁文件路径
        :param expiration_time: 锁过期时间，单位为秒
        """
        self.lock_file_path = lock_file_path
        self.expiration_time = expiration_time

        # 检查锁文件是否存在，存在则删除，确保锁是干净的
        if os.path.exists(self.lock_file_path):
            os.remove(self.lock_file_path)

    def is_locked(self):
        """
        检查锁文件是否存在且未过期
        :return: True 如果锁存在且未过期，否则 False
        """
        if os.path.exists(self.lock_file_path):
            file_mod_time = os.path.getmtime(self.lock_file_path)
            current_time = time.time()
            # 如果锁未过期，返回 True
            if current_time - file_mod_time < self.expiration_time:
                return True
        return False

    def acquire_lock(self):
        """
        创建或更新锁文件
        """
        with open(self.lock_file_path, 'w') as f:
            f.write('locked')
        # 更新锁的时间戳
        os.utime(self.lock_file_path, None)

    def release_lock(self):
        """
        释放锁（删除锁文件）
        """
        if os.path.exists(self.lock_file_path):
            os.remove(self.lock_file_path)
