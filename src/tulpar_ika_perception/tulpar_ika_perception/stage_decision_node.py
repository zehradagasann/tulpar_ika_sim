import rclpy
from rclpy.node import Node
from tulpar_ika_msgs.msg import SignDetection, SpeedDecision, TerrainSpeedDecision

from tulpar_ika_perception.stage_decision import decide_stage, combine_speed


class StageDecisionNode(Node):
    _VALID_SPEEDS = {"stop", "slow", "medium", "fast"}
    _MIN_SIGN_CONFIDENCE = 0.50

    def __init__(self) -> None:
        super().__init__("stage_decision_node")

        self._last_terrain_speed = "medium"
        self._last_stage_decision = None

        self._sign_sub = self.create_subscription(
            SignDetection, "/sign_detected", self._on_sign, 10,
        )
        self._terrain_sub = self.create_subscription(
            TerrainSpeedDecision, "/terrain_speed", self._on_terrain, 10,
        )
        self._pub = self.create_publisher(SpeedDecision, "/speed_decision", 10)

        self.get_logger().info(
            "StageDecisionNode basladi. Min tabela guveni=%.2f"
            % self._MIN_SIGN_CONFIDENCE
        )

    def _on_terrain(self, msg: TerrainSpeedDecision) -> None:
        terrain_speed = msg.speed_level.strip().lower()
        if terrain_speed not in self._VALID_SPEEDS:
            self.get_logger().warning(
                "Gecersiz terrain_speed alindi: '%s'. Son gecerli deger korunuyor."
                % msg.speed_level
            )
            return

        self._last_terrain_speed = terrain_speed
        self._publish_decision()

    def _on_sign(self, msg: SignDetection) -> None:
        class_name = msg.class_name.strip()
        if not class_name:
            self.get_logger().warning("Bos class_name alindi. Mesaj yok sayildi.")
            return

        if msg.confidence < self._MIN_SIGN_CONFIDENCE:
            self.get_logger().warning(
                "Dusuk guvenli tabela yok sayildi: class_name='%s', confidence=%.3f"
                % (class_name, msg.confidence)
            )
            return

        stage_decision = decide_stage(class_name)
        if stage_decision.mission == "bilinmeyen":
            self.get_logger().warning(
                "Taninmayan stage etiketi alindi: '%s'. Son gecerli karar korunuyor."
                % class_name
            )
            return

        self._last_stage_decision = stage_decision
        self._publish_decision()

    def _publish_decision(self) -> None:
        if self._last_stage_decision is None:
            stage_speed = "stop"
            behavior = "none"
            stage_id = "yok"
        else:
            stage_speed = self._last_stage_decision.speed_level
            behavior = self._last_stage_decision.behavior
            stage_id = self._last_stage_decision.stage_id

        final_speed = combine_speed(stage_speed, self._last_terrain_speed)

        out = SpeedDecision()
        out.final_speed = final_speed
        out.behavior = behavior
        out.stage_id = stage_id
        out.stage_speed = stage_speed
        out.terrain_speed = self._last_terrain_speed
        self._pub.publish(out)

        self.get_logger().info(
            "stage=" + stage_id
            + " stage_hiz=" + stage_speed
            + " zemin_hiz=" + self._last_terrain_speed
            + " -> final_hiz=" + out.final_speed
            + " davranis=" + out.behavior
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
