#!/usr/bin/python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Replace 'robot_vision' with your actual package name if different
    share_dir = get_package_share_directory('kc_vision_bringup') 
    
    # Point this to the custom yaml file we created in Step 1
    parameter_file = LaunchConfiguration('params_file')
    params_declare = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(share_dir, 'params', 'custom_ydlidar.yaml'),
        description='Path to the ROS2 parameters file to use.'
    )

    driver_node = LifecycleNode(
        package='ydlidar_ros2_driver',
        executable='ydlidar_ros2_driver_node',
        name='ydlidar_ros2_driver_node',
        output='screen',
        emulate_tty=True,
        parameters=[parameter_file],
        namespace='/',
    )
    
    # Notice: tf2_node (static_transform_publisher) is completely removed.
    # Your URDF/robot_state_publisher will handle the base_link -> lidar_1 transform.

    return LaunchDescription([
        params_declare,
        driver_node,
    ])