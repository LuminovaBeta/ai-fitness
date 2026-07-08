import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
from std_msgs.msg import Float64MultiArray
import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


POSE_CONNECTIONS = [
    (11, 13), (13, 15),  # 左臂
    (12, 14), (14, 16),  # 右臂
    (11, 12),            # 双肩
    (11, 23), (12, 24),  # 躯干
    (23, 24),            # 双髋
    (23, 25), (25, 27),  # 左腿
    (24, 26), (26, 28)   # 右腿
]


ANGLE_JOINTS = {
    "left_knee": (23, 25, 27), "right_knee": (24, 26, 28),
    "left_hip": (11, 23, 25), "right_hip": (12, 24, 26),
    "left_elbow": (11, 13, 15), "right_elbow": (12, 14, 16),
    "left_shoulder": (13, 11, 23), "right_shoulder": (14, 12, 24),
    "left_torso": (0, 11, 23), "right_torso": (0, 12, 24),
    "shoulder_line": (13, 11, 12), "neck_tilt": (11, 0, 12),
    "right_bending": (12, 24, 26), "left_bending": (11, 23, 25)
}

EMA_ALPHA = 1

class PoseDetectorMediaPipeLocal:
    def __init__(self, model_path): 
        self.ema_angles = {name: None for name in ANGLE_JOINTS.keys()}
        
        # 1. 配置本地模型路径
        base_options = python.BaseOptions(model_asset_path=model_path)
        
        # 2. 配置运行模式为 VIDEO
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1, # 设定最多检测几个人
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 初始化检测器
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def _calculate_angle_3d(self, a, b, c):
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        if norm_ba < 1e-6 or norm_bc < 1e-6:
            return 0.0
        cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    def process_frame(self, frame):
        # 转换格式为 MediaPipe 要求的 mp.Image
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # VIDEO 模式必须传入时间戳 (毫秒)，必须递增
        timestamp_ms = int(time.time() * 1000)
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        angles = {}
        best_kpts = np.zeros((33, 2))
        best_kpts_3d = np.zeros((33, 3))
        
        if results.pose_landmarks and len(results.pose_landmarks) > 0:
            h, w, _ = frame.shape
            
            # 提取 2D 像素坐标用于画图 (取检测到的第一个人 [0])
            for i, lm in enumerate(results.pose_landmarks[0]):
                if lm.visibility > 0.3:
                    best_kpts[i] = [int(lm.x * w), int(lm.y * h)]
                    
            # 提取 3D 世界坐标用于计算真实角度
            for i, lm_world in enumerate(results.pose_world_landmarks[0]):
                best_kpts_3d[i] = [lm_world.x, lm_world.y, lm_world.z]

            # 计算各个预设的关节角度
            for name, (a, b, c) in ANGLE_JOINTS.items():
                if np.all(best_kpts_3d[a] == 0) or np.all(best_kpts_3d[b] == 0) or np.all(best_kpts_3d[c] == 0):
                    continue
                    
                raw_ang = self._calculate_angle_3d(best_kpts_3d[a], best_kpts_3d[b], best_kpts_3d[c])
                
                # EMA 滤波平滑
                if self.ema_angles[name] is None: 
                    self.ema_angles[name] = raw_ang
                else: 
                    self.ema_angles[name] = EMA_ALPHA * raw_ang + (1 - EMA_ALPHA) * self.ema_angles[name]
                
                angles[name] = self.ema_angles[name]
            
            return best_kpts, angles
            
        return None, {}

    def release(self):
        self.detector.close()


class PoseUI:
    def draw(self, frame, keypoints, angles):
        if keypoints is not None:
            points_2d = {i: (int(kp[0]), int(kp[1])) for i, kp in enumerate(keypoints) if kp[0] != 0 or kp[1] != 0}
            for p1, p2 in POSE_CONNECTIONS:
                if p1 in points_2d and p2 in points_2d:
                    cv2.line(frame, points_2d[p1], points_2d[p2], (0, 255, 255), 2)
            for point in points_2d.values():
                cv2.circle(frame, point, 4, (0, 255, 0), -1)
            for name, angle in angles.items():
                idx = ANGLE_JOINTS[name][1]
                if idx in points_2d:
                    cv2.putText(frame, f"{int(angle)}", (points_2d[idx][0] + 10, points_2d[idx][1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        return frame


class PoseNode(Node):
    def __init__(self):
        super().__init__('pose_node')
        self.bridge = CvBridge()

        MODEL_PATH = "/userdata/pose_ws/pose_landmarker_full.task"
        
        self.detector = PoseDetectorMediaPipeLocal(model_path=MODEL_PATH)
        self.ui = PoseUI()
        
        self.get_logger().info("正在启动摄像头...")
        self.cap = cv2.VideoCapture("/dev/video21") # 0 代表系统默认摄像头
        
        if not self.cap.isOpened():
            self.get_logger().error("无法打开摄像头！")
            
        self.publisher_ = self.create_publisher(Image, '/pose/image', 10)
        self.angle_publisher = self.create_publisher(Float64MultiArray, '/pose/angles', 10)
        
        # 设置处理频率，30帧/秒
        self.timer = self.create_timer(0.0333, self.timer_callback)
        self.get_logger().info('Pose 节点已启动 (使用本地 MediaPipe Task 模型)')

    def timer_callback(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                return

            # 推理并计算角度
            keypoints, angles = self.detector.process_frame(frame)

            # 发布角度数据
            if angles:
                angle_msg = Float64MultiArray()
                angle_msg.data = [float(angles.get(name, 0.0)) for name in ANGLE_JOINTS.keys()]
                self.angle_publisher.publish(angle_msg)

            # 绘制画面并发布图像
            frame = self.ui.draw(frame, keypoints, angles)
            self.publisher_.publish(self.bridge.cv2_to_imgmsg(frame, 'bgr8'))
            
        except Exception as e:
            if rclpy.ok(): 
                self.get_logger().error(f'图像处理报错: {e}')

    def destroy_node(self):
        self.get_logger().info("正在关闭相机并释放资源...")
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PoseNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass 
    finally:
        node.detector.release()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()