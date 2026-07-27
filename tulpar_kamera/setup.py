from setuptools import setup

package_name = 'tulpar_kamera'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Emin Kuyucu',
    maintainer_email='emnkyc63@gmail.com',
    description='Tulpar IKA kamera node u: WebRTC yayini + YOLO/PID hedef tespiti',
    license='MIT',
    entry_points={
        'console_scripts': [
            'kamera_node = tulpar_kamera.kamera_node:main',
            'arka_kamera_node = tulpar_kamera.arka_kamera_node:main',
            'signaling_server = tulpar_kamera.signaling_server:cli',
        ],
    },
)
