#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node

from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped


class CoveragePlanner(Node):

    def __init__(self):
        super().__init__('coverage_planner')

        self.navigator = BasicNavigator()

        # ===== YOUR MEASURED AREA =====

        self.xmin = -1.005
        self.xmax =  1.994

        self.ymin = 0.985
        self.ymax = 4.016

        # mower cutting width
        self.cut_width = 0.15

        # 20% overlap
        self.spacing = self.cut_width * 0.8

        self.get_logger().info(
            f"Stripe spacing = {self.spacing:.3f} m"
        )

        self.run_coverage()


    def create_pose(self, x, y, yaw):

        pose = PoseStamped()

        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y

        pose.pose.orientation.z = math.sin(yaw/2.0)
        pose.pose.orientation.w = math.cos(yaw/2.0)

        return pose


    def run_coverage(self):

        y = self.ymin + self.spacing

        lane = 1
        left_to_right = True

        while y <= self.ymax - self.spacing:

            if left_to_right:

                goal_x = self.xmax
                yaw = 0.0

            else:

                goal_x = self.xmin
                yaw = math.pi

            self.get_logger().info(
                f"Lane {lane}: goal ({goal_x:.2f}, {y:.2f})"
            )

            goal = self.create_pose(
                goal_x,
                y,
                yaw
            )

            self.navigator.goToPose(goal)

            while not self.navigator.isTaskComplete():
                time.sleep(0.2)

            result = self.navigator.getResult()

            self.get_logger().info(
                f"Lane {lane} completed"
            )

            left_to_right = not left_to_right
            y += self.spacing
            lane += 1

        self.get_logger().info("Coverage Completed")


def main(args=None):

    rclpy.init(args=args)

    node = CoveragePlanner()

    rclpy.spin_once(node, timeout_sec=1.0)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()