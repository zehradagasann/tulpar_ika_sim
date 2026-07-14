#include <chrono>
#include <memory>
#include <string>
#include <thread>

#include "ament_index_cpp/get_package_share_directory.hpp"
#include "behaviortree_cpp/bt_factory.h"
#include "rclcpp/rclcpp.hpp"

#include "tulpar_bt/atis_yap.hpp"
#include "tulpar_bt/devam_et.hpp"
#include "tulpar_bt/dur_ve_bekle.hpp"
#include "tulpar_bt/hedef_tespit_yap.hpp"
#include "tulpar_bt/mod_degisimi_yap.hpp"
#include "tulpar_bt/otonom_surus.hpp"
#include "tulpar_bt/stop_noktasinda_mi.hpp"
#include "tulpar_bt/tabela_algilandi_mi.hpp"
#include "tulpar_bt/wait_for_system_ready.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("tulpar_bt_executor");

  const std::string default_xml_path =
    ament_index_cpp::get_package_share_directory("tulpar_bt") +
    "/behavior_trees/ana_tree.xml";
  node->declare_parameter<std::string>("bt_xml_path", default_xml_path);
  node->declare_parameter<int>("bt_loop_duration_ms", 100);
  node->declare_parameter<int>("server_timeout_ms", 1000);
  node->declare_parameter<int>("wait_for_service_timeout_ms", 1000);

  const std::string bt_xml_path = node->get_parameter("bt_xml_path").as_string();
  const auto bt_loop_duration =
    std::chrono::milliseconds(node->get_parameter("bt_loop_duration_ms").as_int());
  const auto server_timeout =
    std::chrono::milliseconds(node->get_parameter("server_timeout_ms").as_int());
  const auto wait_for_service_timeout =
    std::chrono::milliseconds(node->get_parameter("wait_for_service_timeout_ms").as_int());

  // Nav2 bt_navigator'un kendi agacini kurarken kullandigi ayni standart
  // blackboard anahtarlari - nav2_behavior_tree::BtActionNode bunlari bekler.
  auto blackboard = BT::Blackboard::create();
  blackboard->set<rclcpp::Node::SharedPtr>("node", node);
  blackboard->set<std::chrono::milliseconds>("bt_loop_duration", bt_loop_duration);
  blackboard->set<std::chrono::milliseconds>("server_timeout", server_timeout);
  blackboard->set<std::chrono::milliseconds>(
    "wait_for_service_timeout", wait_for_service_timeout);

  BT::BehaviorTreeFactory factory;
  factory.registerNodeType<tulpar_bt::WaitForSystemReady>("WaitForSystemReady");
  factory.registerNodeType<tulpar_bt::OtonomSurus>("OtonomSurus");
  factory.registerNodeType<tulpar_bt::ModDegisimiYap>("ModDegisimiYap");
  factory.registerNodeType<tulpar_bt::DevamEt>("DevamEt");
  factory.registerNodeType<tulpar_bt::StopNoktasindaMi>("StopNoktasindaMi");
  factory.registerNodeType<tulpar_bt::DurVeBekle>("DurVeBekle");
  factory.registerNodeType<tulpar_bt::TabelaAlgilandiMi>("TabelaAlgılandiMi");
  factory.registerNodeType<tulpar_bt::HedefTespitYap>("HedefTespitYap");
  factory.registerNodeType<tulpar_bt::AtisYap>("AtisYap");

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  std::thread spin_thread([&executor]() {executor.spin();});

  // nav2_behavior_tree::BtActionNode (OtonomSurus'un temeli), node
  // constructor'inda ilgili action server'in (navigate_to_pose) ayakta
  // olmasini zorunlu tutuyor ve degilse exception firlatiyor - yani Nav2
  // henuz ayaga kalkmadiysa createTreeFromFile() patlar. WaitForSystemReady
  // agacin ICINDEKI bir node oldugu icin bu asamada devreye giremez; bu
  // yuzden agac kurulumunu burada retry dongusune sariyoruz.
  BT::Tree tree;
  bool tree_built = false;
  while (rclcpp::ok() && !tree_built) {
    try {
      RCLCPP_INFO(
        node->get_logger(), "tulpar_bt_executor: agac yukleniyor: %s", bt_xml_path.c_str());
      tree = factory.createTreeFromFile(bt_xml_path, blackboard);
      tree_built = true;
    } catch (const std::exception & e) {
      RCLCPP_WARN(
        node->get_logger(),
        "tulpar_bt_executor: agac kurulamadi (%s) - bagimli action server/servisler "
        "(orn. Nav2) henuz ayakta degil, 2s sonra tekrar denenecek",
        e.what());
      std::this_thread::sleep_for(std::chrono::seconds(2));
    }
  }

  if (!tree_built) {
    rclcpp::shutdown();
    spin_thread.join();
    return 1;
  }

  RCLCPP_INFO(node->get_logger(), "tulpar_bt_executor: agac calistiriliyor");
  BT::NodeStatus status = BT::NodeStatus::RUNNING;
  while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
    status = tree.tickOnce();
    if (status == BT::NodeStatus::RUNNING) {
      tree.sleep(bt_loop_duration);
    }
  }

  RCLCPP_INFO(
    node->get_logger(), "tulpar_bt_executor: agac sonlandi (status=%s), kapatiliyor",
    BT::toStr(status).c_str());

  rclcpp::shutdown();
  spin_thread.join();
  return 0;
}
