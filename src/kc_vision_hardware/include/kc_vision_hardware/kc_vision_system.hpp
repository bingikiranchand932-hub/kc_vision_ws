#ifndef KC_VISION_HARDWARE__KC_VISION_SYSTEM_HPP_
#define KC_VISION_HARDWARE__KC_VISION_SYSTEM_HPP_

#include <memory>
#include <string>
#include <vector>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include "std_msgs/msg/float32_multi_array.hpp"
#include "sensor_msgs/msg/imu.hpp"

namespace kc_vision_hardware
{
class KCVisionSystemHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(KCVisionSystemHardware)

  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareComponentInterfaceParams & params) override;
  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_cleanup(
    const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;
  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;
  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  std::shared_ptr<rclcpp::Node> node_;

  rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr wheel_cmd_pub_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr wheel_state_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;

  // Data storage for 2 wheels (Left, Right)
  std::vector<double> hw_commands_velocity_;
  std::vector<double> hw_states_position_;
  std::vector<double> hw_states_velocity_;

  std::vector<double> hw_imu_orientation_;
  std::vector<double> hw_imu_angular_velocity_;
  std::vector<double> hw_imu_linear_acceleration_;

  void wheel_state_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg);
  void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg);
};

}  // namespace kc_vision_hardware

#endif  // KC_VISION_HARDWARE__KC_VISION_SYSTEM_HPP_