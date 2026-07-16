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
        'TULPAR İKA algılama ve görüntü işleme düğümleri.'
    ),

    license='Apache-2.0',

    entry_points={
        'console_scripts': [
            (
                'interface_test_publisher = '
                'tulpar_ika_perception.'
                'interface_test_publisher:main'
            ),
            (
                'webcam_publisher = '
                'tulpar_ika_perception.'
                'webcam_publisher:main'
            ),
            (
                'image_preprocessor = '
                'tulpar_ika_perception.'
                'image_preprocessor:main'
            ),
        ],
    },
)
