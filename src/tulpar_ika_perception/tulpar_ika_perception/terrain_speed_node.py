import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from tulpar_ika_msgs.msg import SignDetection

from tulpar_ika_perception.terrain_speed import compute_terrain_speed


class TerrainSpeedNode(Node):

    def __init__(self) -> None:
        super().__init__("terrain_speed_node")

        self._sub = self.create_subscription(
            SignDetection,
            "/sign_detected",
            self._on_sign_detected,
            10,
        )

        self._pub = self.create_publisher(
            String,
            "/terrain_speed",
            10,
        )

        self.get_logger().info("TerrainSpeedNode basladi.")

    def _on_sign_detected(self, msg: SignDetection) -> None:
        stage_id = msg.class_name
        result = compute_terrain_speed(stage_id)

        out = String()
        out.data = result.speed_level
        self._pub.publish(out)

        self.get_logger().info(
            f"{result.reason} -> yayinlandi: {result.speed_level}"
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
