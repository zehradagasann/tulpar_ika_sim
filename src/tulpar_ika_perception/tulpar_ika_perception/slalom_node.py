import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from tulpar_ika_msgs.msg import Detection2DArray, SlalomTarget

from tulpar_ika_perception.slalom_core import ImageConeDetection, run_slalom_logic


class SlalomNode(Node):
    """/detections'i dinleyip koni ciftlerinden slalom hedefini hesaplar,
    /parkur/slalom_target'e (tulpar_ika_msgs/SlalomTarget) yayinlar.

    /detections artik tulpar_ika_msgs/Detection2DArray (eski tulpar_msgs/
    DetectionArray semasi Emin tarafindan kaldirildi, bkz. commit 6758e34)
    - BEST_EFFORT QoS ile yayinlaniyor, abonelik de BEST_EFFORT olmali,
    yoksa hicbir hata vermeden sifir veri gelir.

    header.frame_id sabit "d435if_color_optical_frame" - Emin'in kendi
    detection_publisher.py'si de ayni varsayilani kullaniyor, tutarli.
    """

    def __init__(self) -> None:
        super().__init__("slalom_node")

        self.declare_parameter("cone_class_name", "traffic_cone")
        self.declare_parameter("target_frame_id", "d435if_color_optical_frame")

        self._cone_class_name = (
            self.get_parameter("cone_class_name").get_parameter_value().string_value
        )
        self._target_frame_id = (
            self.get_parameter("target_frame_id").get_parameter_value().string_value
        )

        detections_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self._sub = self.create_subscription(
            Detection2DArray, "/detections", self._on_detections, detections_qos,
        )
        self._pub = self.create_publisher(SlalomTarget, "/parkur/slalom_target", 10)

        self.get_logger().info(
            "SlalomNode basladi. cone_class_name=%s target_frame_id=%s"
            % (self._cone_class_name, self._target_frame_id)
        )

    def _on_detections(self, msg: Detection2DArray) -> None:
        if not msg.image_width or not msg.image_height:
            self.get_logger().warning(
                "Detection2DArray.image_width/height bos, kare atlaniyor."
            )
            return

        cones = [
            ImageConeDetection(
                image_x=detection.center_px.x,
                image_y=detection.center_px.y,
                cone_color=detection.class_name,
            )
            for detection in msg.detections
            if detection.class_name == self._cone_class_name
        ]

        image_center_x = msg.image_width / 2.0
        result = run_slalom_logic(cones, image_center_x)

        out = SlalomTarget()
        out.header.stamp = msg.header.stamp
        out.header.frame_id = self._target_frame_id

        if result.target_point is not None:
            out.target_x_px = float(result.target_point[0])
            out.target_y_px = float(result.target_point[1])

        out.source_width = msg.image_width
        out.source_height = msg.image_height
        out.turn_direction = result.turn_direction
        out.speed_level = result.speed_level

        self._pub.publish(out)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SlalomNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
