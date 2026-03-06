import random

import pyautogui
import cv2
import numpy as np
import time
import os

import requests

# 配置参数
TEMPLATE_IMAGE_PATH = "target_button.png"  # 目标按钮模板路径
PROCESSING_IMAGE_PATH = "jinxingzhong.png"  # 进行中提示模板路径
Normal_IMAGE_PATH = "normal.png"  # 进行中提示模板路径
CONFIDENCE_THRESHOLD = 0.7  # 匹配置信度 阈值
CHECK_INTERVAL = 1  # 检查间隔（秒）
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()  # 获取屏幕分辨率


def capture_template_compatible(template_path=TEMPLATE_IMAGE_PATH):
    """手动框选区域截图（兼容所有pyautogui版本，可指定保存路径）"""
    print(f"=== 开始截取目标图像 [{os.path.basename(template_path)}] ===")
    print("1. 将鼠标移动到目标区域的左上角位置，按 Enter 确认")
    input("按下Enter继续...")
    x1, y1 = pyautogui.position()
    print(f"左上角坐标: ({x1}, {y1})")

    print("\n2. 将鼠标移动到目标区域的右下角位置，按 Enter 确认")
    input("按下Enter继续...")
    x2, y2 = pyautogui.position()
    print(f"右下角坐标: ({x2}, {y2})")

    # 修正坐标顺序，确保有效
    left = max(0, min(x1, x2))
    top = max(0, min(y1, y2))
    width = min(SCREEN_WIDTH - left, abs(x2 - x1))
    height = min(SCREEN_HEIGHT - top, abs(y2 - y1))
    template_region = (left, top, width, height)

    # 截取并保存模板
    template_screenshot = pyautogui.screenshot(region=template_region)
    template_screenshot.save(template_path)
    print(f"\n模板图像已保存至: {template_path}")
    return template_region


def is_valid_coordinate(x, y):
    """校验坐标是否在屏幕范围内"""
    return 0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT


def find_image_on_full_screen(template_path, confidence=0.7):
    """
    全屏查找指定模板图像
    返回：(中心坐标x, 中心坐标y) 或 None
    """
    try:
        # 读取模板
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"❌ 无法读取模板图像: {template_path}，请检查文件是否存在")
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
                return (center_x, center_y, max_val)  # 返回坐标+匹配度
            else:
                print(f"❌ 未找到{os.path.basename(template_path)}，匹配度: {max_val:.2f}  坐标: ({center_x}, {center_y})")
                # print(f"❌ 匹配到{os.path.basename(template_path)}的坐标无效: ({center_x}, {center_y})")
        else:
            print(
                f"❌ 未找到{os.path.basename(template_path)}，匹配度: {max_val:.2f}  坐标: ({center_x}, {center_y})")
            # safe_click((center_x, center_y), False)
            # time.sleep(10)

        return None
    except Exception as e:
        print(f"❌ 查找{os.path.basename(template_path)}出错: {e}")
        return None
API_URL="http://8.137.155.15:6954/api/test_notify2?id=Normal^&flag=false"

def safe_click(position,flag=True):
    """安全点击（避免触发fail-safe）"""
    if not position:
        return False

    x, y = position
    try:
        # 缓慢移动鼠标到目标位置
        pyautogui.moveTo(x, y, duration=0.3)
        # 执行点击
        if(flag):
            pyautogui.click()
            print(f"✅ 成功点击按钮，位置: ({x}, {y})")
        else:
            print(f"⚠️ 模拟点击按钮，位置: ({x}, {y})")
        return True
    except pyautogui.FailSafeException:
        print(f"❌ 鼠标移动到屏幕边缘，触发安全保护")
        return False
    except Exception as e:
        print(f"❌ 点击失败: {e}")
        return False


def main():
    # 检查模板文件，不存在则引导截图
    if not os.path.exists(TEMPLATE_IMAGE_PATH):
        capture_template_compatible(TEMPLATE_IMAGE_PATH)

    # 检查"进行中"模板文件，不存在则引导截图
    if not os.path.exists(PROCESSING_IMAGE_PATH):
        print(f"\n⚠️ 未找到{PROCESSING_IMAGE_PATH}，请截取'进行中'提示的图像")
        capture_template_compatible(PROCESSING_IMAGE_PATH)

    print(f"\n=== 开始全屏监控 ===")
    print(f"屏幕分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"检查间隔: {CHECK_INTERVAL}秒 | 匹配置信度: {CONFIDENCE_THRESHOLD}")
    print("监控目标：1. target_button.png（匹配则点击） 2. jinxingzhong.png（匹配则提示）")
    print("按 Ctrl+C 停止监控...\n")

    try:
        while True:
            # 1. 先检查是否匹配"进行中"图像
            processing_result = find_image_on_full_screen(PROCESSING_IMAGE_PATH, CONFIDENCE_THRESHOLD)
            if processing_result:
                px, py, p_val = processing_result
                print(f"ℹ️ {time.strftime("[%H:%M:%S]")}正常进行中{random.randint(0,1)}，匹配度: {p_val:.2f}, 位置: ({px}, {py})")
                time.sleep(10)
            else:
                # 2. 未匹配到"进行中"，再检查目标按钮
                button_result = find_image_on_full_screen(TEMPLATE_IMAGE_PATH, CONFIDENCE_THRESHOLD)
                if button_result:
                    bx, by, b_val = button_result
                    print(f"✅ 找到目标按钮，匹配度: {b_val:.2f}, 坐标: ({bx}, {by})")
                    safe_click((bx, by))
                    time.sleep(20)
                else:
                    # 可选：关闭此提示避免刷屏 两个都没找到说明 已经完成了，或者窗口不在前台被遮挡了
                    print(f"❌ 未匹配，继续监控...")
                    time.sleep(10)
                    end_result = find_image_on_full_screen(Normal_IMAGE_PATH, CONFIDENCE_THRESHOLD)
                    if end_result:
                        px, py, p_val = end_result
                        requests.get(API_URL)
                        print(
                            f"ℹ️ {time.strftime("[%H:%M:%S]")}任务已经完成Normal{random.randint(0, 1)}，匹配度: {p_val:.2f}, 位置: ({px}, {py})")
                        user_choice = input("\n是否继续执行？(输入nq退出，其他任意键继续)：").strip().lower()
                        # 判断用户输入
                        if user_choice == 'q'or user_choice == 'n' :
                            # 这里可以添加继续执行的逻辑代码
                            print("❌ 用户选择退出，任务终止。")
                            exit(0)
                        else:
                            print("✅ 继续执行后续任务...")

            # 等待后继续检查
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n✅ 监控已手动停止")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")


if __name__ == "__main__":
    # 轻微降低鼠标操作速度，减少触发安全保护的概率
    pyautogui.PAUSE = 0.1
    main()