import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import pyrealsense2 as rs
import numpy as np

class MinimalRealSenseNode(Node):
    def __init__(self):
        super().__init__('minimal_realsense_node')
        self.bridge = CvBridge()

        # 创建发布者
        # 发布彩色图像和硬件对齐后的深度图像
        self.color_pub = self.create_publisher(Image, '/camera/color/image_raw', 10)
        self.depth_pub = self.create_publisher(Image, '/camera/aligned_depth_to_color/image_raw', 10)

        # 初始化RealSense
        self.pipeline = rs.pipeline()
        config = rs.config()

        # 640x480 @30fps
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        self.get_logger().info("正在启动 RealSense D455...")
        try:
            self.profile = self.pipeline.start(config)
        except Exception as e:
            self.get_logger().error(f"无法启动相机，请检查 USB 连接: {e}")
            raise e

        # 把深度图的像素对齐到彩色图的视角上
        self.align = rs.align(rs.stream.color)

        # 创建定时器 (30Hz)
        self.timer = self.create_timer(0.0333, self.timer_callback)
        self.get_logger().info("RealSense 节点已启动！正在发布对齐后的深度图与彩色图。")

    def timer_callback(self):
        try:
            frames = self.pipeline.wait_for_frames()

            # 执行硬件对齐
            aligned_frames = self.align.process(frames)

            # 获取对齐后的深度帧和彩色帧
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                return

            # 将RealSense数据转换为Numpy数组
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # 转换为 ROS2 Image 消息并发布
            # 彩色图使用 'bgr8'
            color_msg = self.bridge.cv2_to_imgmsg(color_image, encoding='bgr8')
            depth_msg = self.bridge.cv2_to_imgmsg(depth_image, encoding='16UC1')

            # 添加Header信息
            timestamp = self.get_clock().now().to_msg()
            color_msg.header.stamp = timestamp
            color_msg.header.frame_id = "camera_link"
            depth_msg.header.stamp = timestamp
            depth_msg.header.frame_id = "camera_link"

            self.color_pub.publish(color_msg)
            self.depth_pub.publish(depth_msg)

        except Exception as e:
            if rclpy.ok():
                self.get_logger().error(f"帧处理异常: {e}")

    def destroy_node(self):
        self.get_logger().info("正在关闭 RealSense 管道并释放资源...")
        self.pipeline.stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MinimalRealSenseNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()