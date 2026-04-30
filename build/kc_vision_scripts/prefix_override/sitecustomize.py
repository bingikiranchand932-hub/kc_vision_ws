import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/kiranchand/kc_vision_ws/install/kc_vision_scripts'
