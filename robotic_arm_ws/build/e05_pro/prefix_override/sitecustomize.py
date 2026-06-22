import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/yu/Desktop/robotic_arm_ws/install/e05_pro'
