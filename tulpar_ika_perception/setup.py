from setuptools import find_packages, setup

package_name = 'tulpar_ika_perception'

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
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='zehra',
    maintainer_email='zehradagasan09@gmail.com',
    description=(
        'TULPAR IKA slalom karar mantigi (/detections -> /parkur/slalom_target).'
    ),
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'slalom_node = tulpar_ika_perception.slalom_node:main',
            'slalom_debug = tulpar_ika_perception.slalom_debug:main',
        ],
    },
)
