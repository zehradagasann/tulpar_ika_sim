import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from tulpar_ika_msgs.msg import SignDetection

from tulpar_ika_perception.stage_decision import decide_stage, combine_speed


class StageDecisionNode(Node):

    def __init__(self) -> None:
        super().__init__("stage_decision_node")

        self._last_terrain_speed = "medium"
        self._last_stage_decision = None

        self._sign_sub = self.create_subscription(
            SignDetection, "/sign_detected", self._on_sign, 10,
        )
        self._terrain_sub = self.create_subscription(
            String, "/terrain_speed", self._on_terrain, 10,
        )
        self._pub = self.create_publisher(String, "/speed_decision", 10)

        self.get_logger().info("StageDecisionNode basladi.")

    def _on_terrain(self, msg: String) -> None:
        self._last_terrain_speed = msg.data
        self._publish_decision()

    def _on_sign(self, msg: SignDetection) -> None:
        self._last_stage_decision = decide_stage(msg.class_name)
        self._publish_decision()

    def _publish_decision(self) -> None:
        if self._last_stage_decision is None:
            stage_speed = "medium"
            behavior = "none"
            stage_id = "yok"
        else:
            stage_speed = self._last_stage_decision.speed_level
            behavior = self._last_stage_decision.behavior
            stage_id = self._last_stage_decision.stage_id

        final_speed = combine_speed(stage_speed, self._last_terrain_speed)

        out = String()
        out.data = final_speed + "|" + behavior
        self._pub.publish(out)

        self.get_logger().info(
            "stage=" + stage_id
            + " stage_hiz=" + stage_speed
            + " zemin_hiz=" + self._last_terrain_speed
            + " -> " + out.data
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = StageDecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
