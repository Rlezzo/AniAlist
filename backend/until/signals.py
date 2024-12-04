# signals.py
from blinker import signal

# 定义信号
magnet_pushed_signal = signal('magnet-pushed')  # 任务推送信号
magnet_completed_signal = signal('magnet-completed')  # 任务完成信号
