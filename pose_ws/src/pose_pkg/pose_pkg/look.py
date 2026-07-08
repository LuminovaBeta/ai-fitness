import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

import matplotlib
matplotlib.use('TkAgg')  # 强制使用 Tkinter 作为绘图后端

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import numpy as np
import collections
import csv
import time
import datetime
import os  

# 关节名称列表 (与发布端严格对应)
JOINT_NAMES = [
    "left_knee", "right_knee",
    "left_hip", "right_hip",
    "left_elbow", "right_elbow",
    "left_shoulder", "right_shoulder",
    "left_torso", "right_torso",
    "shoulder_line", "neck_tilt"
]

# 配置历史数据长度
HISTORY_LEN = 100

class AngleSubscriber(Node):
    def __init__(self):
        super().__init__('angle_visualizer_node')
        self.subscription = self.create_subscription(
            Float64MultiArray,
            '/pose/angles',
            self.listener_callback,
            10)
        
        self.current_angles = np.zeros(len(JOINT_NAMES))
        self.last_msg_time = 0.0 
        
        self.history = {
            name: collections.deque([np.nan] * HISTORY_LEN, maxlen=HISTORY_LEN) 
            for name in JOINT_NAMES
        }
        
        self.is_recording = False
        self.recorded_data = []  
        self.record_start_time = 0.0 
        
        self.get_logger().info("✅ 动态曲线可视化与录制节点已启动，正在等待数据...")

    def listener_callback(self, msg):
        if len(msg.data) == len(JOINT_NAMES):
            self.current_angles = np.array(msg.data)
            self.last_msg_time = time.time()

    def toggle_recording(self):
        if not self.is_recording:
            self.recorded_data = []  
            self.is_recording = True
            self.record_start_time = time.time() 
            self.get_logger().info("🔴 开始录制数据...")
            return True
        else:
            self.is_recording = False
            self._save_to_csv()
            return False

    def _save_to_csv(self):
        if not self.recorded_data:
            self.get_logger().warn("录制数据为空，未保存文件。")
            return
            
        save_dir = "/userdata/pose_ws/records"
        os.makedirs(save_dir, exist_ok=True)
            
        filename = f"pose_record_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(save_dir, filename)
        
        try:
            with open(filepath, mode='w', newline='') as file:
                writer = csv.writer(file)
                header = ["timestamp_unix", "timestamp_readable"] + JOINT_NAMES
                writer.writerow(header)
                writer.writerows(self.recorded_data)
            self.get_logger().info(f"💾 录制结束！数据已成功保存至: {filepath} (共 {len(self.recorded_data)} 帧)")
        except Exception as e:
            self.get_logger().error(f"保存 CSV 失败: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = AngleSubscriber()

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    plt.ion()
    fig = plt.figure(figsize=(14, 7))
    fig.canvas.manager.set_window_title("实时人体姿态角度分析系统")
    
    ax_plot = fig.add_axes([0.05, 0.12, 0.70, 0.82])
    ax_text = fig.add_axes([0.78, 0.18, 0.20, 0.77])
    ax_text.axis('off')

    lines = {}
    colors = plt.cm.tab20.colors
    for i, name in enumerate(JOINT_NAMES):
        linestyle = '--' if 'right' in name else '-'
        line, = ax_plot.plot([], [], label=name, color=colors[i], linewidth=2, linestyle=linestyle)
        lines[name] = line

    ax_plot.set_xlim(0, HISTORY_LEN)
    ax_plot.set_ylim(0, 180)
    ax_plot.set_xlabel('Frames (Time ->)')
    ax_plot.set_ylabel('Angle (Degrees)')
    
    # 更改了标题以提示用户可以点击图例
    ax_plot.set_title('Real-Time Trajectory (💡 Click Legend to Hide/Show Lines)', fontweight='bold')
    ax_plot.grid(True, linestyle=':', alpha=0.6)
    
    # 提取图例对象
    leg = ax_plot.legend(loc='upper left', fontsize=8, ncol=2)

    # ================= 新增：交互式图例 (点击隐藏/显示) =================
    legend_map = {}
    # 遍历图例中的所有线条和文字，激活它们的拾取事件 (picker)
    for legline, legtext, name in zip(leg.get_lines(), leg.get_texts(), JOINT_NAMES):
        legline.set_picker(True)
        legline.set_pickradius(5)  # 点击的宽容度 (像素)
        legtext.set_picker(True)
        
        # 将线条和文字都映射到对应的完整信息上
        legend_map[legline] = (name, legline, legtext)
        legend_map[legtext] = (name, legline, legtext)

    def on_pick(event):
        artist = event.artist
        if artist in legend_map:
            name, legline, legtext = legend_map[artist]
            
            # 切换该线条当前的可见性状态
            is_visible = not lines[name].get_visible()
            
            # 1. 控制左侧动态曲线的显示/隐藏
            lines[name].set_visible(is_visible)
            # 2. 控制右侧实时文本的显示/隐藏
            text_objs[name].set_visible(is_visible)
            
            # 3. 让图例变暗 (alpha=0.2) 或恢复 (alpha=1.0)，提供视觉反馈
            legline.set_alpha(1.0 if is_visible else 0.2)
            legtext.set_alpha(1.0 if is_visible else 0.2)
            
            fig.canvas.draw_idle()

    # 绑定鼠标点击事件
    fig.canvas.mpl_connect('pick_event', on_pick)
    # ===================================================================

    status_text = ax_plot.text(0.98, 0.98, '', transform=ax_plot.transAxes, 
                               color='red', fontsize=14, fontweight='bold', 
                               ha='right', va='top')
    time_text = ax_plot.text(0.98, 0.02, '', transform=ax_plot.transAxes, 
                             color='dimgray', fontsize=11, fontweight='bold', 
                             ha='right', va='bottom')

    text_objs = {}
    for i, name in enumerate(JOINT_NAMES):
        y_pos = 1.0 - (i * 0.065)
        text_objs[name] = ax_text.text(0, y_pos, f"{name}: 0°", 
                                       fontsize=11, fontweight='bold', 
                                       color=colors[i], family='monospace')

    ax_btn = fig.add_axes([0.80, 0.05, 0.15, 0.08])
    btn_record = Button(ax_btn, 'Start Record', color='lightgreen', hovercolor='palegreen')
    btn_record.label.set_fontweight('bold')

    def on_button_clicked(event):
        is_recording_now = node.toggle_recording()
        if is_recording_now:
            btn_record.color = 'salmon'
            btn_record.hovercolor = 'lightcoral'
            btn_record.label.set_text('Stop & Save')
        else:
            btn_record.color = 'lightgreen'
            btn_record.hovercolor = 'palegreen'
            btn_record.label.set_text('Start Record')
            status_text.set_text('') 
            
    btn_record.on_clicked(on_button_clicked)

    x_data = np.arange(HISTORY_LEN)
    blink_counter = 0
    try:
        while rclpy.ok() and plt.fignum_exists(fig.number):
            now_unix = time.time()
            current_time_str = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-4]
            
            if now_unix - node.last_msg_time > 0.2:
                display_angles = np.zeros(len(JOINT_NAMES))
                plot_angles = np.full(len(JOINT_NAMES), np.nan)
            else:
                display_angles = node.current_angles
                plot_angles = node.current_angles

            for i, name in enumerate(JOINT_NAMES):
                node.history[name].append(plot_angles[i])

            if node.is_recording:
                row_data = [now_unix, current_time_str] + list(display_angles)
                node.recorded_data.append(row_data)

            for i, name in enumerate(JOINT_NAMES):
                y_data = list(node.history[name])
                
                # 即使曲线和文本被隐藏，后台依然更新数据，保证恢复显示时不会出现断层
                lines[name].set_data(x_data, y_data)
                
                current_val = int(display_angles[i])
                text_objs[name].set_text(f"{name.ljust(15)}: {current_val:3d}°")
            
            if node.is_recording:
                blink_counter += 1
                if blink_counter % 10 < 5:  
                    status_text.set_text('🔴 REC')
                else:
                    status_text.set_text('')
                elapsed_time = now_unix - node.record_start_time
                time_text.set_text(f"System: {current_time_str} | REC Duration: {elapsed_time:.1f}s")
            else:
                time_text.set_text(f"System: {current_time_str}")

            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.05)
            
    except KeyboardInterrupt:
        pass
    finally:
        if node.is_recording:
            node.get_logger().warn("窗口被关闭，强制保存当前录制的数据...")
            node.toggle_recording()
            
        node.get_logger().info("正在关闭可视化节点...")
        plt.ioff()
        plt.close('all')
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join()

if __name__ == '__main__':
    main()