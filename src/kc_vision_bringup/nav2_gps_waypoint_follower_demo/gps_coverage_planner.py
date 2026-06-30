#!/usr/bin/env python3

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
import yaml
from ament_index_python.packages import get_package_share_directory
import os
import sys
import time
import math

from nav2_gps_waypoint_follower_demo.utils.gps_utils import latLonYaw2Geopose

# Earth radius in meters for GPS-to-Cartesian conversion
EARTH_RADIUS = 6378137.0

def latlon_to_xy(lat, lon, lat0, lon0):
    """Convert Lat/Lon coordinates to a local flat XY plane in meters."""
    lat_rad = math.radians(lat0)
    x = math.radians(lon - lon0) * math.cos(lat_rad) * EARTH_RADIUS
    y = math.radians(lat - lat0) * EARTH_RADIUS
    return x, y

def xy_to_latlon(x, y, lat0, lon0):
    """Convert local XY meter coordinates back to Geographic Lat/Lon."""
    lat_rad = math.radians(lat0)
    lon = lon0 + math.degrees(x / (EARTH_RADIUS * math.cos(lat_rad)))
    lat = lat0 + math.degrees(y / EARTH_RADIUS)
    return lat, lon

class BoustrophedonPlanner:
    """
    Parse boundary GPS waypoints from YAML and generate a parallel coverage path.
    """
    def __init__(self, wps_file_path: str, sweep_spacing: float = 0.5) -> None:
        self.sweep_spacing = sweep_spacing
        with open(wps_file_path, 'r') as wps_file:
            self.wps_dict = yaml.safe_load(wps_file)
    def generate_path(self):
        """
        Calculates the boustrophedon path and returns an array of GeoPose objects with correct heading.
        """
        if len(self.wps_dict["waypoints"]) < 3:
            print("Error: Need at least 3 boundary waypoints to create a zone.")
            return []

        # 1. Use the first logged waypoint as our Local Origin (0, 0)
        origin_lat = self.wps_dict["waypoints"][0]["latitude"]
        origin_lon = self.wps_dict["waypoints"][0]["longitude"]

        # 2. Convert all GPS boundaries into Local XY Coordinates (in meters)
        xy_polygon = []
        for wp in self.wps_dict["waypoints"]:
            x, y = latlon_to_xy(wp["latitude"], wp["longitude"], origin_lat, origin_lon)
            xy_polygon.append((x, y))

        # 3. Find the bounding box of your area
        min_x = min([p[0] for p in xy_polygon])
        max_x = max([p[0] for p in xy_polygon])
        min_y = min([p[1] for p in xy_polygon])
        max_y = max([p[1] for p in xy_polygon])

        # 4. Generate the Boustrophedon sweeps in meters
        generated_xy_path = []
        current_x = min_x
        moving_up = True

        while current_x <= max_x:
            if moving_up:
                generated_xy_path.append((current_x, min_y))
                generated_xy_path.append((current_x, max_y))
            else:
                generated_xy_path.append((current_x, max_y))
                generated_xy_path.append((current_x, min_y))
            
            current_x += self.sweep_spacing
            moving_up = not moving_up 

        # 5. Convert back to GPS with DYNAMIC YAW calculation
        geopose_wps = []

        for i in range(len(generated_xy_path)):
            x, y = generated_xy_path[i]
            target_lat, target_lon = xy_to_latlon(x, y, origin_lat, origin_lon)
            
            # Arrival Waypoint (maintain heading from previous segment to prevent curves)
            if i > 0:
                prev_x, prev_y = generated_xy_path[i-1]
                arrival_yaw = math.atan2(y - prev_y, x - prev_x)
                geopose_wps.append(latLonYaw2Geopose(target_lat, target_lon, arrival_yaw))
            
            # Departure Waypoint (turn in place to face next segment)
            if i < len(generated_xy_path) - 1:
                next_x, next_y = generated_xy_path[i+1]
                departure_yaw = math.atan2(next_y - y, next_x - x)
                geopose_wps.append(latLonYaw2Geopose(target_lat, target_lon, departure_yaw))
            
        print(f"Coverage Planner: Generated {len(geopose_wps)} interior waypoints at {self.sweep_spacing}m spacing.")
        return geopose_wps


class GpsWpCommander():
    """
    Class to use nav2 to follow the generated boustrophedon waypoints
    """
    def __init__(self, wps_file_path):
        self.navigator = BasicNavigator("basic_navigator")
        # Initialize the planner. Change this value to control the distance between tracks.
        self.planner = BoustrophedonPlanner(wps_file_path, sweep_spacing=0.2)

    def start_wpf(self):
        """
        Function to start the waypoint following
        """
        self.navigator.waitUntilNav2Active(localizer='robot_localization')
        
        # Get the dynamically generated coverage path instead of just the boundaries
        wps = self.planner.generate_path()
        
        self.navigator.followGpsWaypoints(wps)
        while (not self.navigator.isTaskComplete()):
            time.sleep(0.1)
            
        print("Mower completed the area coverage successfully!")


def main():
    rclpy.init()
# allow to pass the waypoints file as an argument
    try:
        default_yaml_file_path = os.path.join(get_package_share_directory(
            "kc_vision_bringup"), "config", "demo_waypoints.yaml")
    except Exception:
        default_yaml_file_path = os.path.expanduser("~/kc_vision_ws/src/kc_vision_bringup/config/demo_waypoints.yaml")
    
    if len(sys.argv) > 1:
        yaml_file_path = sys.argv[1]
    else:
        yaml_file_path = default_yaml_file_path

    gps_wpf = GpsWpCommander(yaml_file_path)
    gps_wpf.start_wpf()


if __name__ == "__main__":
    main()