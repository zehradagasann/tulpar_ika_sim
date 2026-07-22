from setuptools import find_packages, setup

package_name = 'tulpar_turret_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            'share/' + package_name + '/launch',
            ['launch/turret_bridge.launch.py'],
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='talha',
    maintainer_email='talha.dag2005@gmail.com',
    description=(
        '/tulpar_kamera/taret_pid + /tulpar_kamera/atis_event -> Teensy '
        'seri komutlari (TP/TT/S1/S0/L1/L0).'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'turret_bridge = tulpar_turret_bridge.turret_bridge_node:main',
        ],
    },
)
