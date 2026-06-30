# kc_vision_ws
colcon build --symlink-install --packages-select kc_vision_bringup

chmod +x nav2_gps_waypoint_follower_demo/gps_waypoint_logger.py

ros2 launch kc_vision_bringup gps_waypoint_follower.launch.py use_rviz:=True

ros2 run nav2_gps_waypoint_follower_demo gps_waypoint_logger src/kc_vision_bringup/config/demo_waypoints.yaml 

ros2 run nav2_gps_waypoint_follower_demo gps_waypoint_logger src/kc_vision_bringup/config/demo_waypoints.yaml 

ls /dev/ttyACM*

ls /dev/ttyUSB*