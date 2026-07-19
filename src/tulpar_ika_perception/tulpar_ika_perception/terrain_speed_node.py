import rclpy
from rclpy.node import Node
from tulpar_ika_msgs.msg import SignDetection, TerrainSpeedDecision

from tulpar_ika_perception.terrain_speed import compute_terrain_speed


class TerrainSpeedNode(Node):
    _MIN_SIGN_CONFIDENCE = 0.50

    def __init__(self) -> None:
        super().__init__("terrain_speed_node")

        self._sub = self.create_subscription(
            SignDetection,
            "/sign_detected",
            self._on_sign_detected,
            10,
        )

        self._pub = self.create_publisher(
            TerrainSpeedDecision,
            "/terrain_speed",
            10,
        )

        self.get_logger().info(
            "TerrainSpeedNode basladi. Min tabela guveni=%.2f"
            % self._MIN_SIGN_CONFIDENCE
        )

    def _on_sign_detected(self, msg: SignDetection) -> None:
        stage_id = msg.class_name.strip()
        if not stage_id:
            self.get_logger().warning("Bos class_name alindi. Mesaj yok sayildi.")
            return

        if msg.confidence < self._MIN_SIGN_CONFIDENCE:
            self.get_logger().warning(
                "Dusuk guvenli tabela yok sayildi: class_name='%s', confidence=%.3f"
                % (stage_id, msg.confidence)
            )
            return

        result = compute_terrain_speed(stage_id)
        if not result.is_known_stage:
            self.get_logger().warning(
                "Taninmayan stage etiketi alindi: '%s'. "
                "Varsayilan terrain_speed=medium yayinlanacak."
                % stage_id
            )

        out = TerrainSpeedDecision()
        out.stage_id = result.stage_id
        out.terrain_type = result.terrain_type
        out.speed_level = result.speed_level
        out.known_terrain = result.terrain_type != "normal"
        out.reason = result.reason
        self._pub.publish(out)

        self.get_logger().info(
            f"{result.reason} -> yayinlandi: {out.speed_level}"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TerrainSpeedNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
