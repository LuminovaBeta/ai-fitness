#!/usr/bin/env python3
import json

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool, Float64MultiArray, Int32, String

# `/pose/angles` canonical field order from analyze_pushup_bag.py.
ANGLE_FIELDS = [
    'left_knee',
    'right_knee',
    'left_hip',
    'right_hip',
    'left_elbow',
    'right_elbow',
    'left_shoulder',
    'right_shoulder',
    'left_torso',
    'right_torso',
    'shoulder_line',
    'neck_tilt',
]
LEFT_ELBOW_INDEX = ANGLE_FIELDS.index('left_elbow')
RIGHT_ELBOW_INDEX = ANGLE_FIELDS.index('right_elbow')
EXPECTED_ANGLE_COUNT = len(ANGLE_FIELDS)


ELBOW_IMBALANCE_THRESHOLD = 20.0
HIP_QUALITY_THRESHOLD = 85.0
TORSO_QUALITY_THRESHOLD = 115.0
TORSO_IMBALANCE_THRESHOLD = 12.0
SHOULDER_LINE_MIN = 85.0
SHOULDER_LINE_MAX = 130.0

# 状态定义
STATE_DISABLED = -1
STATE_READY = 0
STATE_DOWN = 1
STATE_BOTTOM = 2
STATE_UP = 3
STATE_REP_COMPLETED = 4

# 错误码
ERROR_ELBOW_IMBALANCE = 301
ERROR_BODY_POSTURE = 302
ERROR_BODY_TILT = 303

# 状态机提示消息
DISABLED_MESSAGE = '检测已停用'
READY_MESSAGE = '俯卧撑预备'
DOWN_MESSAGE = '进入下压'
BOTTOM_MESSAGE = '到达最低点'
UP_MESSAGE = '开始撑起'
REP_COMPLETED_MESSAGE = '完成一次俯卧撑'


class PushupDetectorNode(Node):
    def __init__(self):
        super().__init__('pushup_detector_node')

        self.is_enabled = False

        self.angle_sub = self.create_subscription(
            Float64MultiArray,
            '/pose/angles',
            self.angle_callback,
            10,
        )
        self.control_sub = self.create_subscription(
            Bool,
            '/pushup/control',
            self.control_callback,
            10,
        )

        self.error_pub = self.create_publisher(String, '/pushup/errors', 10)
        self.rep_pub = self.create_publisher(Int32, '/pushup/rep_completed', 10)
        self.state_pub = self.create_publisher(String, '/pushup/state', 10)

        # README 中建议的起落阈值大约在 135° / 100° 附近，这组值更贴近当前样本。
        self.ready_threshold = 140.0
        self.bottom_threshold = 120.0
        self.up_trigger_delta = 0.5

        self.reset_runtime_state(reset_enable_flag=False)
        self.get_logger().info('俯卧撑检测FSM已启动，等待 /pushup/control 启用信号...')

    def reset_runtime_state(self, reset_enable_flag=False):
        if reset_enable_flag:
            self.is_enabled = False
        self.state = STATE_READY
        self.rep_count = 0
        self.prev_avg_elbow = None
        self.cycle_min_elbow = None
        self.reported_errors = set()

    def transition_to(self, new_state, code, msg_text, log_text):
        self.state = new_state
        self.publish_state(code, msg_text)
        self.get_logger().info(log_text)

    def publish_state(self, code, msg_text):
        msg = String()
        msg.data = json.dumps({'code': code, 'msg': msg_text}, ensure_ascii=False)
        self.state_pub.publish(msg)
    
    def publish_error(self, code, msg_text):
        msg = String()
        msg.data = json.dumps(
            {
                'code': code,
                'msg': msg_text,
            },
            ensure_ascii=False,
        )
        self.error_pub.publish(msg)

    def control_callback(self, msg):
        self.is_enabled = msg.data
        if self.is_enabled:
            self.get_logger().info('检测器激活，开始计数。')
            self.reset_runtime_state()
            self.publish_state(STATE_READY, READY_MESSAGE)
        else:
            self.get_logger().info('检测器停用。')
            self.reset_runtime_state()
            self.publish_state(STATE_DISABLED, DISABLED_MESSAGE)

    def angle_callback(self, msg):
        if not self.is_enabled:
            return

        if len(msg.data) < EXPECTED_ANGLE_COUNT:
            # self.get_logger().warn(
            #     f'角度数据长度不足，期望 {EXPECTED_ANGLE_COUNT} 个字段，实际 {len(msg.data)} 个，丢弃该帧。'
            # )
            return

        sample = self.parse_angles(msg.data)
        avg_elbow = sample['avg_elbow']

        if self.prev_avg_elbow is None:
            self.prev_avg_elbow = avg_elbow
            self.cycle_min_elbow = avg_elbow
            return

        self.update_fsm(avg_elbow, sample)
        self.prev_avg_elbow = avg_elbow

    def parse_angles(self, data):
        sample = {}
        for index, field_name in enumerate(ANGLE_FIELDS):
            sample[field_name] = float(data[index])

        sample['avg_elbow'] = (sample['left_elbow'] + sample['right_elbow']) / 2.0
        sample['avg_hip'] = (sample['left_hip'] + sample['right_hip']) / 2.0
        sample['avg_torso'] = (sample['left_torso'] + sample['right_torso']) / 2.0
        return sample

    def report_quality_issues(self, sample):
        issues = []

        if abs(sample['left_elbow'] - sample['right_elbow']) > ELBOW_IMBALANCE_THRESHOLD:
            issues.append((ERROR_ELBOW_IMBALANCE, '左右发力不同步'))

        if (
            sample['avg_hip'] < HIP_QUALITY_THRESHOLD
            or sample['avg_torso'] < TORSO_QUALITY_THRESHOLD
        ):
            issues.append((ERROR_BODY_POSTURE, '塌腰或翘臀'))

        if (
            sample['shoulder_line'] < SHOULDER_LINE_MIN
            or sample['shoulder_line'] > SHOULDER_LINE_MAX
            or abs(sample['left_torso'] - sample['right_torso']) > TORSO_IMBALANCE_THRESHOLD
        ):
            issues.append((ERROR_BODY_TILT, '身体倾斜'))

        for code, msg in issues:
            if code not in self.reported_errors:
                self.get_logger().error(f'动作质量问题: {msg}')
                self.publish_error(code, msg)
                self.reported_errors.add(code)

    def update_fsm(self, avg_elbow, sample):
        delta_elbow = avg_elbow - self.prev_avg_elbow

        if self.state == STATE_READY:
            if avg_elbow <= self.ready_threshold and delta_elbow < 0:
                self.cycle_min_elbow = avg_elbow
                self.transition_to(
                    STATE_DOWN,
                    STATE_DOWN,
                    DOWN_MESSAGE,
                    f'FSM: 下压开始, avg_elbow={avg_elbow:.1f}'
                )

        elif self.state == STATE_DOWN:
            self.cycle_min_elbow = min(self.cycle_min_elbow, avg_elbow)
            if avg_elbow <= self.bottom_threshold:
                self.reported_errors.clear()

                self.transition_to(
                    STATE_BOTTOM,
                    STATE_BOTTOM,
                    BOTTOM_MESSAGE,
                    f'FSM: 到达底部, min_elbow={self.cycle_min_elbow:.1f}'
                )

        elif self.state == STATE_BOTTOM:
            self.cycle_min_elbow = min(self.cycle_min_elbow, avg_elbow)

            self.report_quality_issues(sample)

            if delta_elbow >= self.up_trigger_delta:
                self.transition_to(
                    STATE_UP,
                    STATE_UP,
                    UP_MESSAGE,
                    f'FSM: 开始撑起, delta={delta_elbow:.1f}'
                    )

        elif self.state == STATE_UP:
            if avg_elbow >= self.ready_threshold:
                self.complete_rep(avg_elbow)

    def complete_rep(self, avg_elbow):
        self.rep_count += 1
        self.get_logger().info(f'FSM: 俯卧撑完成! 当前总数: {self.rep_count}')

        self.publish_state(STATE_REP_COMPLETED, REP_COMPLETED_MESSAGE)

        msg = Int32()
        msg.data = self.rep_count
        self.rep_pub.publish(msg)

        self.transition_to(
            STATE_READY,
            STATE_READY,
            READY_MESSAGE,
            'FSM: 恢复预备，等待下一次下压'
        )
        self.cycle_min_elbow = avg_elbow


def main(args=None):
    rclpy.init(args=args)
    node = PushupDetectorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

