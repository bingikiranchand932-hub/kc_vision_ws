#include "kc_vision_hardware/kc_vision_system.hpp" 

#include <chrono>
#include <cmath>
#include <limits>
#include <memory>
#include <vector>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace kc_vision_hardware
{
using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

CallbackReturn KCVisionSystemHardware::on_init(const hardware_interface::HardwareComponentInterfaceParams & params)
{
  if (hardware_interface::SystemInterface::on_init(params) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  node_ = std::make_shared<rclcpp::Node>("kc_vision_hardware_interface");

  // Resize arrays for 2 wheels
  hw_commands_velocity_.resize(info_.joints.size(), 0.0);
  hw_states_position_.resize(info_.joints.size(), 0.0);
  hw_states_velocity_.resize(info_.joints.size(), 0.0);
  
  hw_imu_orientation_.resize(4, 0.0);
  hw_imu_angular_velocity_.resize(3, 0.0);
  hw_imu_linear_acceleration_.resize(3, 0.0);

  return CallbackReturn::SUCCESS;
}

CallbackReturn KCVisionSystemHardware::on_configure(const rclcpp_lifecycle::State & /*previous_state*/)
{
  return CallbackReturn::SUCCESS;
}

CallbackReturn KCVisionSystemHardware::on_cleanup(const rclcpp_lifecycle::State & /*previous_state*/)
{
  hw_commands_velocity_.assign(hw_commands_velocity_.size(), 0.0);
  hw_states_position_.assign(hw_states_position_.size(), 0.0);
  hw_states_velocity_.assign(hw_states_velocity_.size(), 0.0);
  return CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> KCVisionSystemHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (uint i = 0; i < info_.joints.size(); i++) {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_states_position_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_states_velocity_[i]));
  }

  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "orientation.x", &hw_imu_orientation_[0]));
  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "orientation.y", &hw_imu_orientation_[1]));
  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "orientation.z", &hw_imu_orientation_[2]));
  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "orientation.w", &hw_imu_orientation_[3]));
  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "linear_acceleration.x", &hw_imu_linear_acceleration_[0]));
  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "linear_acceleration.y", &hw_imu_linear_acceleration_[1]));
  state_interfaces.emplace_back(hardware_interface::StateInterface("imu_sensor", "linear_acceleration.z", &hw_imu_linear_acceleration_[2]));

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> KCVisionSystemHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (uint i = 0; i < info_.joints.size(); i++) {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_commands_velocity_[i]));
  }
  return command_interfaces;
}

CallbackReturn KCVisionSystemHardware::on_activate(const rclcpp_lifecycle::State & /*previous_state*/)
{
  for (auto & command : hw_commands_velocity_) command = 0.0;

  auto qos = rclcpp::QoS(rclcpp::KeepLast(1)).transient_local().reliable();
  wheel_cmd_pub_ = node_->create_publisher<std_msgs::msg::Float32MultiArray>("/wheel_commands", qos);
  
  wheel_state_sub_ = node_->create_subscription<std_msgs::msg::Float32MultiArray>(
    "/wheel_states", 10, std::bind(&KCVisionSystemHardware::wheel_state_callback, this, std::placeholders::_1));
  
  imu_sub_ = node_->create_subscription<sensor_msgs::msg::Imu>(
    "/imu/data_raw", 10, std::bind(&KCVisionSystemHardware::imu_callback, this, std::placeholders::_1));

  return CallbackReturn::SUCCESS;
}

CallbackReturn KCVisionSystemHardware::on_deactivate(const rclcpp_lifecycle::State & /*previous_state*/)
{
  auto stop_msg = std_msgs::msg::Float32MultiArray();
  stop_msg.data = {0.0, 0.0};
  wheel_cmd_pub_->publish(stop_msg);
  
  wheel_cmd_pub_.reset();
  wheel_state_sub_.reset();
  imu_sub_.reset();
  return CallbackReturn::SUCCESS;
}

hardware_interface::return_type KCVisionSystemHardware::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  rclcpp::spin_some(node_);
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type KCVisionSystemHardware::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  auto cmd_msg = std_msgs::msg::Float32MultiArray();
  cmd_msg.data.resize(2);

  // Send Left and Right target velocities (rad/s) to the Pico
  cmd_msg.data[0] = (float)hw_commands_velocity_[0]; 
  cmd_msg.data[1] = (float)hw_commands_velocity_[1]; 

  wheel_cmd_pub_->publish(cmd_msg);
  return hardware_interface::return_type::OK;
}

void KCVisionSystemHardware::wheel_state_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
{
  if (msg->data.size() != 4) {
    RCLCPP_WARN_THROTTLE(node_->get_logger(), *node_->get_clock(), 1000, "Expected 4 elements, got %zu", msg->data.size());
    return;
  }
  
  // Data array from Pico: [Left_Vel, Right_Vel, Left_Pos, Right_Pos]
  hw_states_velocity_[0] = msg->data[0]; 
  hw_states_velocity_[1] = msg->data[1]; 
  hw_states_position_[0] = msg->data[2]; 
  hw_states_position_[1] = msg->data[3]; 
}

void KCVisionSystemHardware::imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg)
{
  hw_imu_orientation_[0] = msg->orientation.x;
  hw_imu_orientation_[1] = msg->orientation.y;
  hw_imu_orientation_[2] = msg->orientation.z;
  hw_imu_orientation_[3] = msg->orientation.w;
  hw_imu_linear_acceleration_[0] = msg->linear_acceleration.x;
  hw_imu_linear_acceleration_[1] = msg->linear_acceleration.y;
  hw_imu_linear_acceleration_[2] = msg->linear_acceleration.z;
}

}  // namespace kc_vision_hardware

PLUGINLIB_EXPORT_CLASS(
  kc_vision_hardware::KCVisionSystemHardware,
  hardware_interface::SystemInterface)