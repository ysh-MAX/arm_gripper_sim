import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    # 1. 加载 MoveIt 全量配置
    moveit_config = MoveItConfigsBuilder(
        "e05", package_name="e05_moveit"
    ).to_moveit_configs()

    # 2. 启动 Gazebo 仿真环境
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch", "gazebo.launch.py"
            )
        ),
        launch_arguments={
            "world": "empty.world",
            "verbose": "false",
            "pause": "false"
        }.items()
    )

    # 3. 发布机器人 URDF 模型与 TF 树
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            moveit_config.robot_description,
            {"publish_frequency": 10.0, "use_sim_time": True}
        ],
        output="screen"
    )

    # 4. 将机器人生成到 Gazebo 中（修改后）
    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic", "robot_description", 
            "-entity", "e05_robot",
        ],
        parameters=[{"use_sim_time": True}],
        output="screen"
    )

    # 5. 模型生成完成后，延时1.5s再启动控制器（等控制器管理器初始化）
    spawn_controllers_on_spawn_finish = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[
                TimerAction(
                    period=0.3,
                    actions=[
                        Node(
                            package="controller_manager",
                            executable="spawner",
                            arguments=[
                                "joint_state_broadcaster",
                                "manipulator_controller",
                                "gripper_controller",
                                "-c", "/controller_manager",
                                "--controller-manager-timeout", "10"  # 修正：Humble正确参数名
                            ],
                            parameters=[{"use_sim_time": True}],
                            output="screen"
                        )
                    ]
                )
            ]
        )
    )

    # 6. 延时启动 MoveIt 规划节点
    start_move_group = TimerAction(
        period=3.5,
        actions=[
            Node(
                package="moveit_ros_move_group",
                executable="move_group",
                parameters=[
                    moveit_config.to_dict(),
                    {"use_sim_time": True}
                ],
                output="screen"
            )
        ]
    )

    # 7. 延时启动 Rviz2 可视化
    rviz_config_path = os.path.join(
        get_package_share_directory("e05_moveit"),
        "config",
        "moveit.rviz"
    )
    start_rviz = TimerAction(
        period=4.5,
        actions=[
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=["-d", rviz_config_path],
                parameters=[
                    moveit_config.robot_description,
                    moveit_config.robot_description_semantic,
                    moveit_config.robot_description_kinematics,
                    {"use_sim_time": True}
                ],
                output="screen"
            )
        ]
    )

    return LaunchDescription([
        gazebo_launch,
        robot_state_publisher,
        spawn_robot,
        spawn_controllers_on_spawn_finish,
        start_move_group,
        start_rviz
    ])