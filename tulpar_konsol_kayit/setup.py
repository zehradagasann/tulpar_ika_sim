from setuptools import find_packages, setup

package_name = 'tulpar_konsol_kayit'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/olay_gunlugu.launch.py',
            'launch/bag_kayit.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='talha',
    maintainer_email='talha.dag2005@gmail.com',
    description=(
        '5Hz konsol heartbeat + /sign_detected, /detections, '
        '/tulpar_bt/atis_event olaylarini SQLite olay gunlugune yazar.'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'olay_gunlugu = tulpar_konsol_kayit.olay_gunlugu_node:main',
        ],
    },
)
