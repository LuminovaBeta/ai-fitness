from setuptools import find_packages, setup

package_name = 'pose_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='elf',
    maintainer_email='elf@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pose_node = pose_pkg.main:main',
            'yolo_node = pose_pkg.yolo:main',
            'look_node = pose_pkg.look:main',
            'midia_node = pose_pkg.media:main',
            'cam_node = pose_pkg.cam:main'
        ],
    },
)
