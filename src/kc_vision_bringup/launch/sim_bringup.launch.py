import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get the directories
    pkg_description = get_package_share_directory('kc_vision_description')
    pkg_gazebo = get_package_share_directory('kc_vision_gazebo')

    # Include the robot_state_publisher launch file
    rsp_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_description, 'launch', 'rviz.launch.py')),
        launch_arguments={'use_sim_time': 'true', 'jsp_gui': 'false'}.items()
    )

    # Include the Gazebo launch file
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo, 'launch', 'gazebo.launch.py'))
    )

    # Create and return the launch description
    ld = LaunchDescription()
    ld.add_action(rsp_launch)
    ld.add_action(gazebo_launch)
    
    return ld