"""/cmd_vel (geometry_msgs/Twist) -> /cmd_vel_safe (geometry_msgs/Twist).

KTR 3.3.2: "Collision Checker'dan gecen hiz komutu /cmd_vel_safe uzerinden
Teensy'ye aktarilir." Nav2'nin velocity_smoother ciktisini (/cmd_vel) local
costmap'e gore diffdrive kinematigiyle kisa bir ufka (lookahead_time_sec)
projekte edip, robot govdesini (robot_radius_m) o yorunge boyunca gercek bir
lethal hucreyle kesisiyorsa hizi sifirlar - kesismiyorsa komutu oldugu gibi
gecirir. Costmap/TF henuz gelmemisse (baslangic anindaki gecici durum)
komut oldugu gibi gecilir, hiz kesmez - fail-open degil, sadece henuz karar
verecek veri yok demektir.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid

import tf2_ros
from tf2_ros import TransformException


def _yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class CollisionChecker(Node):

    def __init__(self):
        super().__init__('collision_checker')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('costmap_topic', '/local_costmap/costmap')
        self.declare_parameter('output_topic', '/cmd_vel_safe')
        self.declare_parameter('robot_frame', 'base_footprint')
        self.declare_parameter('lookahead_time_sec', 1.0)
        self.declare_parameter('time_step_sec', 0.1)
        self.declare_parameter('robot_radius_m', 0.65)
        self.declare_parameter('lethal_cost_threshold', 90)

        self.robot_frame = self.get_parameter('robot_frame').value
        self.lookahead_time = self.get_parameter('lookahead_time_sec').value
        self.time_step = self.get_parameter('time_step_sec').value
        self.robot_radius = self.get_parameter('robot_radius_m').value
        self.lethal_threshold = self.get_parameter('lethal_cost_threshold').value

        self.latest_costmap = None

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        costmap_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.create_subscription(
            OccupancyGrid,
            self.get_parameter('costmap_topic').value,
            self._costmap_callback,
            costmap_qos,
        )
        self.create_subscription(
            Twist,
            self.get_parameter('cmd_vel_topic').value,
            self._cmd_vel_callback,
            10,
        )
        self.safe_pub = self.create_publisher(
            Twist,
            self.get_parameter('output_topic').value,
            10,
        )

        self.get_logger().info(
            f"collision_checker basladi: {self.get_parameter('cmd_vel_topic').value} -> "
            f"{self.get_parameter('output_topic').value}, ufuk={self.lookahead_time}s, "
            f"govde yaricapi={self.robot_radius}m, lethal esik={self.lethal_threshold}"
        )

    def _costmap_callback(self, msg: OccupancyGrid):
        self.latest_costmap = msg

    def _cmd_vel_callback(self, msg: Twist):
        if self.latest_costmap is None:
            self.get_logger().warn(
                'Henuz costmap alinmadi, cmd_vel oldugu gibi iletiliyor.',
                throttle_duration_sec=5.0,
            )
            self.safe_pub.publish(msg)
            return

        try:
            tf = self.tf_buffer.lookup_transform(
                self.latest_costmap.header.frame_id, self.robot_frame, rclpy.time.Time())
        except TransformException as ex:
            self.get_logger().warn(
                f"TF alinamadi ({self.latest_costmap.header.frame_id} -> "
                f"{self.robot_frame}): {ex} - cmd_vel oldugu gibi iletiliyor.",
                throttle_duration_sec=5.0,
            )
            self.safe_pub.publish(msg)
            return

        x = tf.transform.translation.x
        y = tf.transform.translation.y
        yaw = _yaw_from_quaternion(tf.transform.rotation)

        v = msg.linear.x
        w = msg.angular.z

        blocked = False
        steps = max(1, int(self.lookahead_time / self.time_step))
        for _ in range(steps):
            x += v * math.cos(yaw) * self.time_step
            y += v * math.sin(yaw) * self.time_step
            yaw += w * self.time_step
            if self._is_lethal_nearby(x, y):
                blocked = True
                break

        if blocked:
            self.get_logger().warn(
                'Collision Checker: on yorungede engel tespit edildi, hiz sifirlandi.',
                throttle_duration_sec=2.0,
            )
            self.safe_pub.publish(Twist())
        else:
            self.safe_pub.publish(msg)

    def _is_lethal_nearby(self, x: float, y: float) -> bool:
        cm = self.latest_costmap
        res = cm.info.resolution
        if res <= 0.0:
            return False

        ox = cm.info.origin.position.x
        oy = cm.info.origin.position.y
        width = cm.info.width
        height = cm.info.height

        cx = int((x - ox) / res)
        cy = int((y - oy) / res)
        radius_cells = int(math.ceil(self.robot_radius / res))

        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                if dx * dx + dy * dy > radius_cells * radius_cells:
                    continue
                gx, gy = cx + dx, cy + dy
                if gx < 0 or gy < 0 or gx >= width or gy >= height:
                    continue
                value = cm.data[gy * width + gx]
                if value >= self.lethal_threshold:
                    return True
        return False


def main(args=None):
    rclpy.init(args=args)
    node = CollisionChecker()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
