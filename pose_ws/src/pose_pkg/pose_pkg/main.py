import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
from rknnlite.api import RKNNLite
import time
from std_msgs.msg import Float64MultiArray, MultiArrayDimension
import pyrealsense2 as rs

# 关键点索引
POSE_CONNECTIONS = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]

ANGLE_JOINTS = {
    "left_knee": (11, 13, 15), "right_knee": (12, 14, 16),
    "left_hip": (5, 11, 13), "right_hip": (6, 12, 14),
    "left_elbow": (5, 7, 9), "right_elbow": (6, 8, 10),
    "left_shoulder": (7, 5, 11), "right_shoulder": (8, 6, 12),
    "left_torso": (0, 5, 11), "right_torso": (0, 6, 12),
    "shoulder_line": (7, 5, 6), "neck_tilt": (5, 0, 6),
}

EMA_ALPHA = 0.4


# 姿态检测器类
class PoseDetectorRKNN:
    def __init__(self, model_path="/userdata/pose_ws/best.rknn", imgsz=640):
        self.imgsz = imgsz
        self.rknn = RKNNLite()
        ret = self.rknn.load_rknn(model_path)
        if ret != 0:
            print("load failed")
            exit(ret)
        ret = self.rknn.init_runtime()
        if ret != 0:
            print("Init failed")
            exit(ret)
        self.ema_angles = {name: None for name in ANGLE_JOINTS.keys()}
        self.ema_cog = None

    # 计算三维空间中三个点的夹角
    def _calculate_angle_3d(self, a, b, c):
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        if norm_ba < 1e-6 or norm_bc < 1e-6:
            return 0.0
        cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    # 对图像进行letterbox处理，保持纵横比并填充边界
    def _letterbox(self, im, new_shape, color=(114, 114, 114)):
        shape = im.shape[:2]  
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2; dh /= 2
        if shape[::-1] != new_unpad:
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return im, r, (dw, dh)

    # 处理每一帧图像，进行姿态检测和角度计算
    def process_frame(self, frame, depth_frame=None, intrinsics=None):
        img, ratio, (pad_w, pad_h) = self._letterbox(frame, (self.imgsz, self.imgsz))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img, axis=0)
        outputs = self.rknn.inference(inputs=[img])
        pred = outputs[0][0].T
        scores = pred[:, 4]
        mask = scores > 0.5
        valid_preds = pred[mask]
        angles = {}
        if len(valid_preds) > 0:
            boxes = []; confidences = []; kpts_list = []
            for row in valid_preds:
                cx, cy, w, h = row[0:4]
                boxes.append([cx - w/2, cy - h/2, w, h])
                confidences.append(float(row[4]))
                kpts_list.append(row[5:])
            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            if len(indices) > 0:
                raw_kpts = kpts_list[indices[0]].reshape(17, 3)
                best_kpts = np.zeros((17, 2))
                best_kpts_3d = np.zeros((17, 3))
                for i in range(17):
                    kpt_x, kpt_y, kpt_conf = raw_kpts[i]
                    if kpt_conf > 0.3:
                        orig_x = (kpt_x - pad_w) / ratio
                        orig_y = (kpt_y - pad_h) / ratio
                        best_kpts[i] = [orig_x, orig_y]
                        u, v = int(orig_x), int(orig_y)
                        if intrinsics and 0 <= u < intrinsics.width and 0 <= v < intrinsics.height:
                            dist = depth_frame.get_distance(u, v)
                            if dist > 0:
                                best_kpts_3d[i] = rs.rs2_deproject_pixel_to_point(intrinsics, [u, v], dist)

                for name, (a, b, c) in ANGLE_JOINTS.items():
                    if np.all(best_kpts_3d[a] == 0) or np.all(best_kpts_3d[b] == 0) or np.all(best_kpts_3d[c] == 0):
                        continue
                    raw_ang = self._calculate_angle_3d(best_kpts_3d[a], best_kpts_3d[b], best_kpts_3d[c])
                    if self.ema_angles[name] is None: self.ema_angles[name] = raw_ang
                    else: self.ema_angles[name] = EMA_ALPHA * raw_ang + (1 - EMA_ALPHA) * self.ema_angles[name]
                    angles[name] = self.ema_angles[name]
                return best_kpts, angles
        return None, {}

    def release(self):
        self.rknn.release()

# 绘制姿态关键点和角度的UI类
class PoseUI:
    def draw(self, frame, keypoints, angles):
        if keypoints is not None:
            points_2d = {i: (int(kp[0]), int(kp[1])) for i, kp in enumerate(keypoints) if kp[0] != 0}
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
        self.detector = PoseDetectorRKNN()
        self.ui = PoseUI()
        
        self.spatial = rs.spatial_filter()
        self.temporal = rs.temporal_filter()
        self.hole_filling = rs.hole_filling_filter()
        self.get_logger().info("正在启动 RealSense 相机...")
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.colorizer = rs.colorizer()
        try:
            self.profile = self.pipeline.start(self.config)
            depth_sensor = self.profile.get_device().first_depth_sensor()
            if depth_sensor.supports(rs.option.visual_preset):
                depth_sensor.set_option(rs.option.visual_preset, 4)
            self.align = rs.align(rs.stream.color)
            self.intrinsics = self.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
            self.get_logger().info("相机启动成功")
        except Exception as e:
            self.get_logger().error(f"启动相机失败: {e}"); raise e

        self.publisher_ = self.create_publisher(Image, '/pose/image', 10)
        self.publisher_depth = self.create_publisher(Image, '/pose/depth', 10)
        self.angle_publisher = self.create_publisher(Float64MultiArray, '/pose/angles', 10)
        
        self.timer = self.create_timer(0.0333, self.timer_callback)
        self.get_logger().info('pose节点已启动')

    def timer_callback(self):
        try:

            raw_frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(raw_frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
            if not color_frame or not depth_frame: return

            depth_frame = self.spatial.process(depth_frame) # 空间滤波去噪声
            depth_frame = self.temporal.process(depth_frame)    # 时间滤波稳定帧间变化
            depth_frame = self.hole_filling.process(depth_frame).as_depth_frame()   # 孔洞填充修复缺失深度

            depth_image = np.asanyarray(self.colorizer.colorize(depth_frame).get_data())
            frame = np.asanyarray(color_frame.get_data())
            keypoints, angles = self.detector.process_frame(frame, depth_frame, self.intrinsics)

            if angles:
                angle_msg = Float64MultiArray()
                angle_msg.data = [float(angles.get(name, 0.0)) for name in ANGLE_JOINTS.keys()]
                self.angle_publisher.publish(angle_msg)

            frame = self.ui.draw(frame, keypoints, angles)
            self.publisher_.publish(self.bridge.cv2_to_imgmsg(frame, 'bgr8'))
            self.publisher_depth.publish(self.bridge.cv2_to_imgmsg(depth_image, 'bgr8'))
        except Exception as e:
            if rclpy.ok(): self.get_logger().error(f'图像处理报错: {e}')

    def destroy_node(self):
        self.get_logger().info("正在关闭相机并释放资源...")
        try: self.pipeline.stop()
        except: pass
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