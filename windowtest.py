import random
import pyautogui
import cv2
import numpy as np
import time
import os
import tkinter as tk
from tkinter import ttk
import threading

# 配置参数
TEMPLATE_IMAGE_PATH = "target_button.png"  # 目标按钮模板路径
PROCESSING_IMAGE_PATH = "jinxingzhong.png"  # 进行中提示模板路径
CONFIDENCE_THRESHOLD = 0.7  # 匹配置信度 阈值
CHECK_INTERVAL = 1  # 检查间隔（秒）
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()  # 获取屏幕分辨率

# 悬浮窗配置
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 300
WINDOW_ALPHA = 0.8  # 窗口透明度 (0-1)
WINDOW_POS_X = SCREEN_WIDTH - WINDOW_WIDTH - 20  # 初始位置：屏幕右侧
WINDOW_POS_Y = 50  # 初始位置：屏幕上方


class FloatingMonitorWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图像监控助手")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{WINDOW_POS_X}+{WINDOW_POS_Y}")
        self.root.attributes('-topmost', True)  # 始终置顶
        self.root.attributes('-alpha', WINDOW_ALPHA)  # 设置透明度
        self.root.resizable(False, False)  # 禁止调整大小

        # 允许窗口拖动
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.do_drag)
        self.root.bind('<ButtonRelease-1>', self.stop_drag)

        # 创建UI组件
        self._create_ui()

        # 保存日志的列表
        self.logs = []
        self.max_log_lines = 20  # 最大显示日志行数

    def _create_ui(self):
        # 标题栏
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(title_frame, text="图像监控状态", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        # 控制按钮
        ttk.Button(title_frame, text="清空日志", command=self.clear_logs).pack(side=tk.RIGHT, padx=2)
        ttk.Button(title_frame, text="退出", command=self.exit_app).pack(side=tk.RIGHT, padx=2)

        # 状态信息区域
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        # 关键状态显示
        self.status_label = ttk.Label(status_frame, text="状态: 初始化中...", font=("Arial", 10))
        self.status_label.pack(anchor=tk.W)

        self.match_info_label = ttk.Label(status_frame, text="匹配信息: 无", font=("Arial", 10))
        self.match_info_label.pack(anchor=tk.W)

        # 日志区域
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(log_frame, text="运行日志:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # 滚动日志框
        self.log_text = tk.Text(log_frame, height=10, width=50, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 设置文本框只读
        self.log_text.config(state=tk.DISABLED)

    def start_drag(self, event):
        """开始拖动窗口"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def do_drag(self, event):
        """执行拖动"""
        if self.is_dragging:
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        """停止拖动"""
        self.is_dragging = False

    def add_log(self, message):
        """添加日志信息到窗口"""
        # 格式化时间
        timestamp = time.strftime("[%H:%M:%S]")
        log_msg = f"{timestamp} {message}"

        # 添加到日志列表并控制长度
        self.logs.append(log_msg)
        if len(self.logs) > self.max_log_lines:
            self.logs.pop(0)

        # 更新文本框
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "\n".join(self.logs))
        self.log_text.see(tk.END)  # 滚动到最后一行
        self.log_text.config(state=tk.DISABLED)

        # 立即更新UI
        self.root.update_idletasks()

    def update_status(self, status):
        """更新状态标签"""
        self.status_label.config(text=f"状态: {status}")
        self.root.update_idletasks()

    def update_match_info(self, info):
        """更新匹配信息标签"""
        self.match_info_label.config(text=f"匹配信息: {info}")
        self.root.update_idletasks()

    def clear_logs(self):
        """清空日志"""
        self.logs = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def exit_app(self):
        """退出应用"""
        self.root.quit()
        self.root.destroy()

    def run(self):
        """运行窗口主循环"""
        self.root.mainloop()


def capture_template_compatible(template_path=TEMPLATE_IMAGE_PATH, window=None):
    """手动框选区域截图（兼容所有pyautogui版本，可指定保存路径）"""
    log_msg = f"=== 开始截取目标图像 [{os.path.basename(template_path)}] ==="
    if window:
        window.add_log(log_msg)
    else:
        print(log_msg)

    prompt1 = "1. 将鼠标移动到目标区域的左上角位置，按 Enter 确认"
    if window:
        window.add_log(prompt1)
    else:
        print(prompt1)

    input("按下Enter继续...")
    x1, y1 = pyautogui.position()
    pos1_msg = f"左上角坐标: ({x1}, {y1})"
    if window:
        window.add_log(pos1_msg)
    else:
        print(pos1_msg)

    prompt2 = "\n2. 将鼠标移动到目标区域的右下角位置，按 Enter 确认"
    if window:
        window.add_log(prompt2)
    else:
        print(prompt2)

    input("按下Enter继续...")
    x2, y2 = pyautogui.position()
    pos2_msg = f"右下角坐标: ({x2}, {y2})"
    if window:
        window.add_log(pos2_msg)
    else:
        print(pos2_msg)

    # 修正坐标顺序，确保有效
    left = max(0, min(x1, x2))
    top = max(0, min(y1, y2))
    width = min(SCREEN_WIDTH - left, abs(x2 - x1))
    height = min(SCREEN_HEIGHT - top, abs(y2 - y1))
    template_region = (left, top, width, height)

    # 截取并保存模板
    template_screenshot = pyautogui.screenshot(region=template_region)
    template_screenshot.save(template_path)
    save_msg = f"\n模板图像已保存至: {template_path}"
    if window:
        window.add_log(save_msg)
    else:
        print(save_msg)

    return template_region


def is_valid_coordinate(x, y):
    """校验坐标是否在屏幕范围内"""
    return 0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT


def find_image_on_full_screen(template_path, confidence=0.7, window=None):
    """
    全屏查找指定模板图像
    返回：(中心坐标x, 中心坐标y, 匹配度) 或 None
    """
    try:
        # 读取模板
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            error_msg = f"❌ 无法读取模板图像: {template_path}，请检查文件是否存在"
            if window:
                window.add_log(error_msg)
            else:
                print(error_msg)
            return None

        # 截取全屏
        screen = pyautogui.screenshot()
        screen_np = np.array(screen)
        screen_cv = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

        # 模板匹配
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 计算中心坐标
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        if max_val >= confidence:
            # 校验坐标有效性
            if is_valid_coordinate(center_x, center_y):
                match_msg = f"🔍 匹配到{os.path.basename(template_path)}，匹配度: {max_val:.2f}, 坐标: ({center_x}, {center_y})"
                if window:
                    window.add_log(match_msg)
                    window.update_match_info(
                        f"{os.path.basename(template_path)} | 匹配度: {max_val:.2f} | 坐标: ({center_x}, {center_y})")
                else:
                    print(match_msg)
                return (center_x, center_y, max_val)  # 返回坐标+匹配度
            else:
                error_msg = f"❌ 匹配到{os.path.basename(template_path)}的坐标无效: ({center_x}, {center_y})"
                if window:
                    window.add_log(error_msg)
                else:
                    print(error_msg)
        else:
            error_msg = f"❌ 未找到{os.path.basename(template_path)}，最高匹配度: {max_val:.2f} 坐标:({center_x},{center_y})"
            if window:
                window.add_log(error_msg)
                window.update_match_info("无匹配目标")
            else:
                print(error_msg)
        time.sleep(10)
        return None
    except Exception as e:
        error_msg = f"❌ 查找{os.path.basename(template_path)}出错: {e}"
        if window:
            window.add_log(error_msg)
        else:
            print(error_msg)
        return None


def safe_click(position, flag=True, window=None):
    """安全点击（避免触发fail-safe）"""
    if not position:
        return False

    x, y = position
    try:
        # 缓慢移动鼠标到目标位置
        pyautogui.moveTo(x, y, duration=0.3)
        # 执行点击
        if flag:
            pyautogui.click()
            success_msg = f"✅ 成功点击按钮，位置: ({x}, {y})"
            if window:
                window.add_log(success_msg)
            else:
                print(success_msg)
        else:
            info_msg = f"⚠️ 模拟点击按钮，位置: ({x}, {y})"
            if window:
                window.add_log(info_msg)
            else:
                print(info_msg)
        return True
    except pyautogui.FailSafeException:
        error_msg = f"❌ 鼠标移动到屏幕边缘，触发安全保护"
        if window:
            window.add_log(error_msg)
        else:
            print(error_msg)
        return False
    except Exception as e:
        error_msg = f"❌ 点击失败: {e}"
        if window:
            window.add_log(error_msg)
        else:
            print(error_msg)
        return False


def monitor_task(window):
    """监控任务（在独立线程中运行）"""
    # 检查模板文件，不存在则引导截图
    if not os.path.exists(TEMPLATE_IMAGE_PATH):
        capture_template_compatible(TEMPLATE_IMAGE_PATH, window)

    # 检查"进行中"模板文件，不存在则引导截图
    if not os.path.exists(PROCESSING_IMAGE_PATH):
        info_msg = f"\n⚠️ 未找到{PROCESSING_IMAGE_PATH}，请截取'进行中'提示的图像"
        window.add_log(info_msg)
        capture_template_compatible(PROCESSING_IMAGE_PATH, window)

    init_msg = f"=== 开始全屏监控 ==="
    window.add_log(init_msg)
    window.add_log(f"屏幕分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    window.add_log(f"检查间隔: {CHECK_INTERVAL}秒 | 匹配置信度: {CONFIDENCE_THRESHOLD}")
    window.add_log("监控目标：1. target_button.png（匹配则点击） 2. jinxingzhong.png（匹配则提示）")
    window.update_status("监控中...")

    try:
        while True:
            # 检查窗口是否还在运行
            if not window.root.winfo_exists():
                break

            # 1. 先检查是否匹配"进行中"图像
            processing_result = find_image_on_full_screen(PROCESSING_IMAGE_PATH, CONFIDENCE_THRESHOLD, window)
            if processing_result:
                px, py, p_val = processing_result
                info_msg = f"ℹ️ 正常进行中{random.randint(0, 1)}，匹配度: {p_val:.2f}, 位置: ({px}, {py})"
                window.add_log(info_msg)
                window.update_status("进行中...")
                time.sleep(10)
            else:
                # 2. 未匹配到"进行中"，再检查目标按钮
                button_result = find_image_on_full_screen(TEMPLATE_IMAGE_PATH, CONFIDENCE_THRESHOLD, window)
                if button_result:
                    bx, by, b_val = button_result
                    window.update_status("找到目标按钮，点击中...")
                    safe_click((bx, by), True, window)
                else:
                    # info_msg = f"❌ 未识别到目标按钮或进行中提示，继续监控..."
                    # window.add_log(info_msg)
                    window.update_status("监控中（无匹配）")

            # 等待后继续检查
            time.sleep(CHECK_INTERVAL)

    except Exception as e:
        error_msg = f"\n❌ 监控任务出错: {e}"
        window.add_log(error_msg)
        window.update_status(f"出错: {e}")


def main():
    # 创建悬浮窗口
    floating_window = FloatingMonitorWindow()

    # 轻微降低鼠标操作速度，减少触发安全保护的概率
    pyautogui.PAUSE = 0.1

    # 在新线程中运行监控任务，避免阻塞UI
    monitor_thread = threading.Thread(target=monitor_task, args=(floating_window,), daemon=True)
    monitor_thread.start()

    # 运行窗口主循环
    try:
        floating_window.run()
    except KeyboardInterrupt:
        floating_window.add_log("\n✅ 监控已手动停止")
    finally:
        floating_window.exit_app()


if __name__ == "__main__":
    main()