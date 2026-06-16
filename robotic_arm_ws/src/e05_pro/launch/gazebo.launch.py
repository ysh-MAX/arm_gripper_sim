import os
import re
import xacro
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('e05_pro')
    gazebo_path = get_package_share_directory('gazebo_ros')
    rviz_config_path = os.path.join(pkg_dir, 'urdf.rviz')
    robotic_xacro = os.path.join(pkg_dir, 'urdf', 'e05.xacro')

    # ── 关键修复：去掉 XML 声明和注释 ────────────────────────────────────
    raw_description = xacro.process_file(robotic_xacro).toxml()
    
    # 1. 去掉 <?xml version="1.0" ?> 声明（这是让 gazebo_ros2_control 崩溃的元凶）
    robot_description = re.sub(r'<\?xml[^?]*\?>', '', raw_description)
    # 2. 去掉 xacro 自动生成的超长注释（缩短字符串长度）
    robot_description = re.sub(r'<!--.*?-->', '', robot_description, flags=re.DOTALL)
    robot_description = robot_description.strip()
    # ────────────────────────────────────────────────────────────────────

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_path, 'launch', 'gazebo.launch.py')
        )
    )

    # 机器人状态发布
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen',
    )

    # 在 Gazebo 中生成机器人
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'e05',
            '-topic', 'robot_description',
            '-x', '0', '-y', '0', '-z', '0.0',
        ],
        output='screen',
    )

    # joint_state_broadcaster（spawn 完成后启动）
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster',
                   '--controller-manager', '/controller_manager'],
        output='screen',
    )

    # arm 控制器（broadcaster 成功后启动）
    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_trajectory_controller',
                   '--controller-manager', '/controller_manager'],
        output='screen',
    )

    gripper_controller_spawner = Node(      # ← 新增
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller',
                '--controller-manager', '/controller_manager'],
        output='screen',
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # 事件链：spawn完成 → broadcaster → arm控制器
    load_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )
    load_arm_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        )
    )
    # arm 控制器完成 → 启动 gripper 控制器
    load_gripper_controller = RegisterEventHandler(      # ← 新增
        event_handler=OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[gripper_controller_spawner],
        )
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        TimerAction(period=3.0, actions=[spawn_entity]),
        # TimerAction(period=12.0, actions=[rviz2]),
        load_joint_state_broadcaster,
        load_arm_controller,
        load_gripper_controller,
    ])