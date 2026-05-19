import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/zehra/Masaüstü/tulpar_ika_ws/install/tulpar_description'
