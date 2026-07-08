#!/usr/bin/env python3
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float64MultiArray, Int32, String


STATE_DISABLED = -1
STATE_READY_CLOSED = 0
STATE_OPENING_SYNC = 1
STATE_OPEN_APEX = 2
STATE_CLOSING_SYNC = 3
STATE_REP_COMPLETED = 4

ERROR_UPPER_BODY_ASYNC = 201
ERROR_LOWER_BODY_ASYNC = 202
ERROR_SHOULDER_LINE_TILT = 203

LEFT_HIP_INDEX = 2
RIGHT_HIP_INDEX = 3
LEFT_SHOULDER_INDEX = 6
RIGHT_SHOULDER_INDEX = 7
SHOULDER_LINE_INDEX = 10
MIN_REQUIRED_ANGLE_COUNT = 11

READY_MESSAGE = '站立预备'
DISABLED_MESSAGE = '检测已停用'
OPENING_MESSAGE = '动作启动：手脚同步打开'
OPEN_APEX_MESSAGE = '空中打开到位'
CLOSING_MESSAGE = '开始同步回收'
REP_COMPLETED_MESSAGE = '完成一次开合跳'


class JumpingJackDetectorNode(Node):
    def __init__(self):
        super().__init__('jumping_jack_detector_node')

        self.is_enabled = False

        self.angle_sub = self.create_subscription(
            Float64MultiArray,
            '/pose/angles',
            self.angle_callback,
            10
        )
        self.control_sub = self.create_subscription(
            Bool,
            '/jumping_jack/control',
            self.control_callback,
            10
        )

        self.rep_pub = self.create_publisher(Int32, '/jumping_jack/rep_completed', 10)
        self.state_pub = self.create_publisher(String, '/jumping_jack/state', 10)
        self.error_pub = self.create_publisher(String, '/jumping_jack/errors', 10)

        self.filter_alpha = 0.35

        # 手脚同步相位 FSM：要求双手和双腿都达到打开位，并在同步窗口内一起回收。
        self.closed_shoulder_threshold = 45.0
        self.open_shoulder_threshold = 130.0
        self.start_shoulder_threshold = 55.0
        self.shoulder_open_delta_threshold = 6.0
        self.shoulder_close_delta_threshold = -6.0

        self.closed_hip_threshold = 172.0
        self.open_hip_threshold = 166.0
        self.start_hip_threshold = 171.0
        self.hip_open_delta_threshold = -1.5
        self.hip_close_delta_threshold = 1.5

        self.max_open_sync_gap = 0.35
        self.max_close_sync_gap = 0.35
        self.phase_timeout = 2.0

        self.upper_body_error_threshold = 20.0
        self.lower_body_error_threshold = 16.0

        # 以 114514 bag 的站立预备段为“标准动作”基线：shoulder_line 均值约 92.4。
        self.shoulder_line_center = 92.4
        self.shoulder_line_tilt_threshold = 16.0

        self.last_error_time = 0.0
        self.error_cooldown = 1.5

        self.reset_runtime_state(reset_enable_flag=False)
        self.get_logger().info('开合跳检测节点已启动，等待 /jumping_jack/control 启用信号...')

    def reset_runtime_state(self, reset_enable_flag=False):
        if reset_enable_flag:
            self.is_enabled = False
        self.state = STATE_READY_CLOSED
        self.rep_count = 0
        self.state_enter_time = self.now_sec()
        self.filtered_angles = None
        self.prev_avg_shoulder = None
        self.prev_avg_hip = None
        self.arm_open_time = None
        self.leg_open_time = None
        self.arm_close_time = None
        self.leg_close_time = None
        self.apex_verified = False

    def clear_cycle_tracking(self):
        self.arm_open_time = None
        self.leg_open_time = None
        self.arm_close_time = None
        self.leg_close_time = None
        self.apex_verified = False

    def now_sec(self):
        return self.get_clock().now().nanoseconds / 1e9

    def transition_to(self, new_state, code, msg_text, log_text, reset_cycle=False):
        self.state = new_state
        self.state_enter_time = self.now_sec()
        if reset_cycle:
            self.clear_cycle_tracking()
        self.publish_state(code, msg_text)
        self.get_logger().info(log_text)

    def reset_to_ready(self, log_text):
        self.transition_to(STATE_READY_CLOSED, STATE_READY_CLOSED, READY_MESSAGE, log_text, reset_cycle=True)

    def control_callback(self, msg):
        self.is_enabled = msg.data
        if self.is_enabled:
            self.get_logger().info('收到启用信号，开合跳检测器已激活。')
            self.reset_runtime_state()
            self.publish_state(STATE_READY_CLOSED, READY_MESSAGE)
        else:
            self.get_logger().info('收到停用信号，清空缓存并停止检测。')
            self.reset_runtime_state()
            self.last_error_time = 0.0
            self.publish_state(STATE_DISABLED, DISABLED_MESSAGE)

    def publish_state(self, code, msg_text):
        msg = String()
        msg.data = json.dumps({'code': code, 'msg': msg_text}, ensure_ascii=False)
        self.state_pub.publish(msg)

    def publish_error(self, code, msg_text):
        msg = String()
        msg.data = json.dumps({'code': code, 'msg': msg_text}, ensure_ascii=False)
        self.error_pub.publish(msg)

    def angle_callback(self, msg):
        if not self.is_enabled:
            return

        if len(msg.data) < MIN_REQUIRED_ANGLE_COUNT:
            self.get_logger().warn('接收到的角度数据长度不足 11，丢弃该帧。')
            return

        left_hip = msg.data[LEFT_HIP_INDEX]
        right_hip = msg.data[RIGHT_HIP_INDEX]
        left_shoulder = msg.data[LEFT_SHOULDER_INDEX]
        right_shoulder = msg.data[RIGHT_SHOULDER_INDEX]
        shoulder_line = msg.data[SHOULDER_LINE_INDEX]

        left_hip, right_hip, left_shoulder, right_shoulder, shoulder_line = self.filter_motion(
            left_hip,
            right_hip,
            left_shoulder,
            right_shoulder,
            shoulder_line,
        )

        self.detect_errors(left_hip, right_hip, left_shoulder, right_shoulder, shoulder_line)
        self.update_fsm(left_hip, right_hip, left_shoulder, right_shoulder)

    def filter_motion(self, left_hip, right_hip, left_shoulder, right_shoulder, shoulder_line):
        current = [left_hip, right_hip, left_shoulder, right_shoulder, shoulder_line]
        if self.filtered_angles is None:
            self.filtered_angles = current
            return tuple(current)

        self.filtered_angles = [
            self.filter_alpha * cur + (1.0 - self.filter_alpha) * prev
            for cur, prev in zip(current, self.filtered_angles)
        ]
        return tuple(self.filtered_angles)

    def detect_errors(self, l_hip, r_hip, l_shoulder, r_shoulder, shoulder_line):
        current_time = self.now_sec()
        if current_time - self.last_error_time < self.error_cooldown:
            return

        error_code = None
        error_msg = None

        if abs(l_shoulder - r_shoulder) > self.upper_body_error_threshold:
            error_code = ERROR_UPPER_BODY_ASYNC
            error_msg = '上肢动作不协调，请保持左右手臂同步！'
        elif abs(l_hip - r_hip) > self.lower_body_error_threshold:
            error_code = ERROR_LOWER_BODY_ASYNC
            error_msg = '下肢动作不协调，身体重心可能偏移，请保持双腿同步！'
        elif abs(shoulder_line - self.shoulder_line_center) > self.shoulder_line_tilt_threshold:
            error_code = ERROR_SHOULDER_LINE_TILT
            #error_msg = '肩线倾斜过大，请保持身体稳定！'

        if error_code is not None:
            self.publish_error(error_code, error_msg)
            self.last_error_time = current_time
            self.get_logger().warn(f'触发错误: {error_code} - {error_msg}')

    def complete_rep(self):
        self.rep_count += 1
        self.get_logger().info(f'FSM: 开合跳完成! 当前总数: {self.rep_count}')
        self.publish_state(STATE_REP_COMPLETED, REP_COMPLETED_MESSAGE)

        msg = Int32()
        msg.data = self.rep_count
        self.rep_pub.publish(msg)

        self.transition_to(
            STATE_READY_CLOSED,
            STATE_READY_CLOSED,
            READY_MESSAGE,
            'FSM: 同步开合完成，回到站立预备',
            reset_cycle=True,
        )

    def sync_gap_exceeded(self, first_time, second_time, limit_sec):
        return first_time is not None and second_time is not None and abs(first_time - second_time) > limit_sec

    def update_fsm(self, left_hip, right_hip, left_shoulder, right_shoulder):
        avg_shoulder = (left_shoulder + right_shoulder) / 2.0
        avg_hip = (left_hip + right_hip) / 2.0

        # ==========================================
        # 1. 极简粗暴的姿态判定（直接使用超大容错阈值）
        # ==========================================
        # 满足这个条件，说明人确实“大张开”了（手举起超过90度，且腿张开低于167度）
        is_fully_open = (avg_shoulder >= 90.0) and (avg_hip <= 167.0)
        
        # 满足这个条件，说明人确实“收回来了”（手放低低于75度，且腿并拢高于168度）
        is_fully_closed = (avg_shoulder <= 75.0) and (avg_hip >= 168.0)

        # ==========================================
        # 2. 像深蹲一样纯粹的状态机
        # ==========================================
        
        # STATE 0: 站立预备，等待身体在空中打开
        if self.state == 0:
            if is_fully_open:
                self.state = 1
                self.publish_state(1, "到达空中打开位")
                self.get_logger().info(f"进入 STATE 1: 成功打开 (手:{avg_shoulder:.1f}/腿:{avg_hip:.1f})")

        # STATE 1: 已经在空中打开了，等待身体回收
        elif self.state == 1:
            # 只要有往回收的趋势，或者已经回到底部了，就切到状态 2
            if avg_shoulder < 100.0 or avg_hip > 162.0:
                self.state = 2
                self.publish_state(2, "开始回收")
                self.get_logger().info("进入 STATE 2: 开始回收")

        # STATE 2: 回收阶段，必须等手脚都老老实实并拢，才算真正完成一次
        elif self.state == 2:
            if is_fully_closed:
                self.state = 0
                self.rep_count += 1
                self.get_logger().info(f"开合跳完成! 当前总数: {self.rep_count}")
                
                # 回到初始状态
                self.publish_state(0, "站立预备")

                # 发布完成事件和当前计数
                msg = Int32()
                msg.data = self.rep_count
                self.rep_pub.publish(msg)

        self.prev_avg_shoulder = avg_shoulder
        self.prev_avg_hip = avg_hip


def main(args=None):
    rclpy.init(args=args)
    node = JumpingJackDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
