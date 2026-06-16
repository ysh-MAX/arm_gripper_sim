from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'e05_pro'

# 递归拿到所有内容，过滤掉文件夹，只保留文件
def get_resource_files(base_dir):
    file_list = []
    for path in glob(f"{base_dir}/**/*", recursive=True):
        if os.path.isfile(path):
            rel_dir = os.path.dirname(path)
            install_target = os.path.join('share', package_name, rel_dir)
            file_list.append((install_target, [path]))
    return file_list

mesh_install = get_resource_files("meshes")

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob("launch/*.py")),
        *mesh_install,
        (os.path.join('share', package_name, 'config'), glob("config/*.yaml")),
        (os.path.join('share', package_name, 'urdf'), glob("urdf/*.xacro")),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yu',
    maintainer_email='yu@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
