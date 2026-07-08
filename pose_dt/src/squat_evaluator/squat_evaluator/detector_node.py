#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Int32, String, Bool
import json

class SquatDetectorNode(Node):
    def __init__(self):
        super().__init__('squat_detector_node')

        # --- 运行状态标志 ---
        self.is_enabled = False  # 默认不工作，等待主控程序发送 True 启用

        # --- 订阅器 ---
        # 1. 订阅由姿态估计模块发布的话题
        self.angle_sub = self.create_subscription(
            Float64MultiArray,
            '/pose/angles',
            self.angle_callback,
            10
        )
        # 2. 订阅控制话题 (启用/停用)
        self.control_sub = self.create_subscription(
            Bool,
            '/squat/control',
            self.control_callback,
            10
        )

        # --- 发布器 ---
        # 1. 完成个数
        self.rep_pub = self.create_publisher(Int32, '/squat/rep_completed', 10)
        # 2. 当前状态 (JSON格式包含状态码和说明)
        self.state_pub = self.create_publisher(String, '/squat/state', 10)
        # 3. 错误动作 (JSON格式包含错误码和说明)
        self.error_pub = self.create_publisher(String, '/squat/errors', 10)

        # --- 状态机与计数器 ---
        self.state = 0
        self.rep_count = 0

        # 错误提示冷却时间（秒）
        self.last_error_time = 0.0
        self.error_cooldown = 1.5

        self.get_logger().info("深蹲检测节点已启动，等待 /squat/control 启用信号...")

    def control_callback(self, msg):
        """处理外部的启用/停用信号"""
        self.is_enabled = msg.data
        if self.is_enabled:
            self.get_logger().info("收到启用信号，深蹲检测器已激活。")
            self.publish_state(0, "站立预备")
        else:
            self.get_logger().info("收到停用信号，清空缓存并停止检测。")
            # 停用时清除所有缓存和计数
            self.state = 0
            self.rep_count = 0
            self.last_error_time = 0.0
            self.publish_state(-1, "检测已停用")

    def publish_state(self, code, msg_text):
        """标准化发布状态话题"""
        msg = String()
        # ensure_ascii=False 保证中文字符正常输出而不是转义
        msg.data = json.dumps({"code": code, "msg": msg_text}, ensure_ascii=False)
        self.state_pub.publish(msg)

    def publish_error(self, code, msg_text):
        """标准化发布错误话题"""
        msg = String()
        msg.data = json.dumps({"code": code, "msg": msg_text}, ensure_ascii=False)
        self.error_pub.publish(msg)

    def angle_callback(self, msg):
        """处理接收到的角度数组"""
        # 如果未启用，直接丢弃数据
        if not self.is_enabled:
            return

        if len(msg.data) < 4:
            self.get_logger().warn("接收到的角度数据长度不足 4，丢弃该帧。")
            return

        left_knee, right_knee, left_hip, right_hip = msg.data[0:4]

        self.detect_errors(left_knee, right_knee, left_hip, right_hip)
        self.update_fsm(left_knee, right_knee, left_hip, right_hip)

    def detect_errors(self, l_knee, r_knee, l_hip, r_hip):
        """并发错误检测守护逻辑"""
        current_time = self.get_clock().now().nanoseconds / 1e9

        # 如果还在冷却时间内，暂不发布新错误
        if current_time - self.last_error_time < self.error_cooldown:
            return

        error_code = None
        error_msg = None

        # 错误 1: 躯干过度前倾 (状态码: 101)
        if l_hip < 50.0 or r_hip < 50.0:
            error_code = 101
            #error_msg = "躯干过度前倾，请挺胸并保持背部中立！"

        # 错误 2: 发力不平衡 (状态码: 102)
        elif abs(l_knee - r_knee) > 20.0 or abs(l_hip - r_hip) > 20.0:
            error_code = 102
            error_msg = "发力不平衡，身体重心可能偏移，请保持左右同步！"

        # 如果检测到错误，则发布并重置冷却计时器
        if error_code is not None:
            self.publish_error(error_code, error_msg)
            self.last_error_time = current_time
            self.get_logger().warn(f"触发错误: {error_code} - {error_msg}")

    def update_fsm(self, l_knee, r_knee, l_hip, r_hip):
        """深蹲主状态机"""
        # STATE 0: 站立预备
        if self.state == 0:
            if l_knee < 140.0 and r_knee < 140.0:
                self.state = 1
                self.publish_state(1, "下蹲阶段")
                self.get_logger().info("进入 STATE 1: 下蹲")

        # STATE 1: 下蹲阶段
        elif self.state == 1:
            if l_knee < 105.0 and r_knee < 105.0 and l_hip < 95.0 and r_hip < 95.0:
                self.state = 2
                self.publish_state(2, "到达最低点")
                self.get_logger().info("进入 STATE 2: 最低点")

        # STATE 2: 最低点 (等待站起)
        elif self.state == 2:
            if l_knee > 115.0 and r_knee > 115.0:
                self.state = 3
                self.publish_state(3, "站起阶段")
                self.get_logger().info("进入 STATE 3: 站起")

        # STATE 3: 站起阶段
        elif self.state == 3:
            if l_knee > 160.0 and r_knee > 160.0 and l_hip > 150.0 and r_hip > 150.0:
                self.state = 0
                self.rep_count += 1
                self.get_logger().info(f"深蹲完成! 当前总数: {self.rep_count}")
                
                # 回到站立状态
                self.publish_state(0, "站立预备")

                # 发布完成事件和当前计数
                msg = Int32()
                msg.data = self.rep_count
                self.rep_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SquatDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
