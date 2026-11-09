import math, rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from turtlesim.msg import Pose
from tf2_ros import TransformBroadcaster

class Difusor(Node):
    """Publica en tf2 la pose de turtle1 como world -> turtle1."""
    def __init__(self):
        super().__init__('difusor_tf_tortuga')
        self.br = TransformBroadcaster(self)
        self.create_subscription(Pose, '/turtle1/pose', self.cb, 10)

    def cb(self, p):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id, t.child_frame_id = 'world', 'turtle1'
        t.transform.translation.x, t.transform.translation.y = p.x, p.y
        t.transform.rotation.z = math.sin(p.theta / 2)   # giro theta sobre z, en cuaternio
        t.transform.rotation.w = math.cos(p.theta / 2)
        self.br.sendTransform(t)

rclpy.init(); rclpy.spin(Difusor())
