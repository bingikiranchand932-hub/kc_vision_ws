#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import math
import subprocess

class VirtualMowerNode(Node):
    def __init__(self):
        super().__init__('virtual_mower_node')
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10)
        
        self.last_spawn_x = None
        self.last_spawn_y = None
        self.spawn_distance_threshold = 0.15 # Spawn a decal every 15cm
        self.decal_counter = 0

        self.get_logger().info('Virtual Mower Node started. Waiting for odometry...')

    def spawn_decal(self, x, y, yaw):
        model_name = f"cut_grass_{self.decal_counter}"
        
        # A flat, dark green square, 30cm x 30cm (slightly wider than the robot)
        # Z is 0.005 so it sits slightly above the ground plane
        sdf_xml = f"""
        <sdf version="1.8">
            <model name="{model_name}">
                <static>true</static>
                <pose>0 0 0.005 0 0 0</pose>
                <link name="link">
                    <visual name="v">
                        <geometry>
                            <box><size>0.3 0.3 0.001</size></box>
                        </geometry>
                        <material>
                            <!-- Dark green to represent cut/bent grass -->
                            <ambient>0.1 0.3 0.05 1</ambient>
                            <diffuse>0.1 0.3 0.05 1</diffuse>
                        </material>
                    </visual>
                </link>
            </model>
        </sdf>
        """

        # Command to spawn via Gazebo Harmonic CLI
        # Gazebo service expects standard ignition transport format
        # Using subprocess to call the gz command line tool is robust
        cmd = [
            'gz', 'service', '-s', '/world/virtual_grass_world/create',
            '--reqtype', 'gz.msgs.EntityFactory',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '500',
            '--req', f'sdf: \'{sdf_xml}\', pose: {{position: {{x: {x}, y: {y}, z: 0.005}}, orientation: {{z: {math.sin(yaw/2)}, w: {math.cos(yaw/2)}}}}}, name: "{model_name}"'
        ]

        # Run non-blocking so we don't hold up the odom callback
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.decal_counter += 1

    def odom_callback(self, msg):
        current_x = msg.pose.pose.position.x
        current_y = msg.pose.pose.position.y
        
        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        # Initialize last position
        if self.last_spawn_x is None:
            self.last_spawn_x = current_x
            self.last_spawn_y = current_y
            self.spawn_decal(current_x, current_y, yaw)
            return

        # Calculate distance moved since last spawn
        dx = current_x - self.last_spawn_x
        dy = current_y - self.last_spawn_y
        distance = math.sqrt(dx*dx + dy*dy)

        # If we moved enough, spawn a new grass decal behind the robot
        if distance >= self.spawn_distance_threshold:
            # Shift the spawn point backward to represent the mower blade at the rear
            rear_offset = -0.15 # 15cm backward from center
            spawn_x = current_x + math.cos(yaw) * rear_offset
            spawn_y = current_y + math.sin(yaw) * rear_offset

            self.spawn_decal(spawn_x, spawn_y, yaw)
            self.last_spawn_x = current_x
            self.last_spawn_y = current_y

def main(args=None):
    rclpy.init(args=args)
    node = VirtualMowerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
