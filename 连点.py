import time  # 导入时间模块，用于获取时间戳和延时
import random  # 导入随机数模块，用于随机扰动CPS
import threading  # 导入线程模块，用于多线程运行
import tkinter as tk  # 导入GUI库，用于创建显示窗口
from pynput import mouse, keyboard  # 导入鼠标和键盘监听库
from pynput.mouse import Button, Controller  # 导入鼠标按钮和控制器
import os  # 导入操作系统模块，用于文件路径操作
import sys
from pathlib import Path

def get_exe_dir() -> Path:
    """获取exe/脚本所在目录，读写配置文件用"""
    if getattr(sys, "frozen", False):
        # 打包exe模式：sys.executable就是exe完整路径，取父文件夹
        return Path(sys.executable).parent
    else:
        # 源码运行模式：py脚本所在文件夹
        return Path(__file__).parent

# 配置文件路径
#SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "连点settings.txt")
SETTINGS_FILE = get_exe_dir() / "连点settings.txt"

class Settings:  # 定义设置管理类
    """管理程序配置文件的读取和保存"""
    def __init__(self):  # 构造函数
        # 默认配置
        self.topmost = True  # 窗口是否置顶（布尔值）
        self.left_click_enabled = True  # 左键连点是否开启（布尔值）
        self.right_click_enabled = False  # 右键连点是否开启（布尔值）
        self.check_interval = 1.0  # 检测间隔秒数（浮点数，范围0.1-2.0）
        self.bonus_cps = 15  # 连点增加的CPS数（整数，范围1-20）
        self.left_activation_cps = 4  # 左键触发连点的CPS阈值（整数，范围1-20）
        self.right_activation_cps = 4  # 右键触发连点的CPS阈值（整数，范围1-20）
        self.min_click_duration = 1.0  # 连点最小持续时间秒数（浮点数，范围0.05-5.0）
        self.left_cps_minus1_enabled = False  # CPS>-1开关状态（布尔值）
        self.left_cps_minus1_enabled_key = False  # 左键C CPS>-1开关绑定按键（字符串，如"f1"）
        self.left_cps_minus1_toggle_key = None  # CPS>-1切换绑定按键（字符串，如"f1"）
        self.left_cps_minus1_last_cps = 4  # CPS>-1关闭时恢复的上次CPS阈值（整数，默认4）
        self.random_cps_enabled = False  # 随机扰动CPS总开关（布尔值）
        self.left_random_cps_enabled = True  # 左键随机扰动开关（布尔值）
        self.right_random_cps_enabled = True  # 右键随机扰动开关（布尔值）
        
        self.load()  # 加载配置文件
    
    def validate_and_fix(self):  # 验证并修复配置范围函数
        """检查所有配置值是否在有效范围内，超出范围则重置为默认值"""
        fixed = False  # 标记是否修复了配置
        
        # 验证布尔值
        if not isinstance(self.topmost, bool):
            print(f"警告: topmost值无效，已重置为默认值True")
            self.topmost = True
            fixed = True
        if not isinstance(self.left_click_enabled, bool):
            print(f"警告: left_click_enabled值无效，已重置为默认值True")
            self.left_click_enabled = True
            fixed = True
        if not isinstance(self.right_click_enabled, bool):
            print(f"警告: right_click_enabled值无效，已重置为默认值False")
            self.right_click_enabled = False
            fixed = True
        
        # 验证检测间隔（0.1-2.0）
        if not isinstance(self.check_interval, (int, float)) or not (0.1 <= self.check_interval <= 2.0):
            print(f"警告: check_interval={self.check_interval}超出范围(0.1-2.0)，已重置为默认值1.0")
            self.check_interval = 1.0
            fixed = True
        
        # 验证加成CPS（1-20）
        if not isinstance(self.bonus_cps, int) or not (1 <= self.bonus_cps <= 20):
            print(f"警告: bonus_cps={self.bonus_cps}超出范围(1-20)，已重置为默认值15")
            self.bonus_cps = 15
            fixed = True
        
        # 验证左键触发阈值（1-20）
        if not isinstance(self.left_activation_cps, int) or not (1 <= self.left_activation_cps <= 20):
            print(f"警告: left_activation_cps={self.left_activation_cps}超出范围(1-20)，已重置为默认值4")
            self.left_activation_cps = 4
            fixed = True
        
        # 验证右键触发阈值（1-20）
        if not isinstance(self.right_activation_cps, int) or not (1 <= self.right_activation_cps <= 20):
            print(f"警告: right_activation_cps={self.right_activation_cps}超出范围(1-20)，已重置为默认值4")
            self.right_activation_cps = 4
            fixed = True
        
        # 验证连点时长（0.05-5.0）
        if not isinstance(self.min_click_duration, (int, float)) or not (0.05 <= self.min_click_duration <= 5.0):
            print(f"警告: min_click_duration={self.min_click_duration}超出范围(0.05-5.0)，已重置为默认值1.0")
            self.min_click_duration = 1.0
            fixed = True
        
        if fixed:  # 如果有修复
            print("配置已修复，正在保存...")
            self.save()  # 保存修复后的配置
    
        if fixed:  # 如果有修复
            print("配置已修复，正在保存...")
            self.save()  # 保存修复后的配置
    
    def load(self):  # 加载配置文件函数
        """从文件加载配置"""
        if not os.path.exists(SETTINGS_FILE):  # 如果配置文件不存在
            self.save()  # 保存默认配置
            return  # 返回
        
        try:  # 尝试读取配置文件
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:  # 打开配置文件
                for line in f:  # 逐行读取
                    line = line.strip()  # 去除首尾空格
                    if "=" not in line or line.startswith("#"):  # 如果不是配置行或注释
                        continue  # 跳过
                    key, value = line.split("=", 1)  # 分割键值对
                    key = key.strip()  # 去除键的空格
                    value = value.strip()  # 去除值的空格
                    
                    if key == "topmost":  # 如果是置顶设置
                        self.topmost = value.lower() == "true"  # 转换为布尔值
                    elif key == "left_click_enabled":  # 如果是左键连点设置
                        self.left_click_enabled = value.lower() == "true"  # 转换为布尔值
                    elif key == "right_click_enabled":  # 如果是右键连点设置
                        self.right_click_enabled = value.lower() == "true"  # 转换为布尔值
                    elif key == "check_interval":  # 如果是检测间隔设置
                        val = float(value)  # 转换为浮点数
                        self.check_interval = max(0.1, min(2.0, val))  # 限制范围0.1-2.0
                    elif key == "bonus_cps":  # 如果是加成CPS设置
                        val = int(value)  # 转换为整数
                        self.bonus_cps = max(1, min(20, val))  # 限制范围1-20
                    elif key == "left_activation_cps":  # 如果是左键触发阈值设置
                        val = int(value)  # 转换为整数
                        self.left_activation_cps = max(1, min(20, val))  # 限制范围1-20
                    elif key == "right_activation_cps":  # 如果是右键触发阈值设置
                        val = int(value)  # 转换为整数
                        self.right_activation_cps = max(1, min(20, val))  # 限制范围1-20
                    elif key == "activation_cps":  # 兼容旧配置
                        val = int(value)  # 转换为整数
                        self.left_activation_cps = max(1, min(20, val))  # 限制范围1-20
                        self.right_activation_cps = max(1, min(20, val))  # 限制范围1-20
                    elif key == "min_click_duration":  # 如果是最小持续时间设置
                        val = float(value)  # 转换为浮点数
                        self.min_click_duration = max(0.05, min(5.0, val))  # 限制范围0.05-5.0
                    elif key == "left_cps_minus1_enabled":  # 如果是CPS>-1开关设置
                        self.left_cps_minus1_enabled = value.lower() == "true"  # 转换为布尔值
                    elif key == "left_cps_minus1_toggle_key":  # 如果是CPS>-1绑定按键设置
                        self.left_cps_minus1_toggle_key = value if value else None  # 保存按键字符串
                    elif key == "left_cps_minus1_last_cps":  # 如果是CPS>-1上次阈值设置
                        val = int(value)  # 转换为整数
                        self.left_cps_minus1_last_cps = max(1, min(20, val))  # 限制范围1-20
                    elif self.left_cps_minus1_toggle_key and key == self.left_cps_minus1_toggle_key:  # 如果是绑定按键的状态值（如f1=true）
                        self.left_cps_minus1_enabled_key = value.lower() == "true"  # 转换为布尔值
                    elif key == "random_cps_enabled":  # 如果是随机扰动总开关设置
                        self.random_cps_enabled = value.lower() == "true"  # 转换为布尔值
                    elif key == "left_random_cps_enabled":  # 如果是左键随机扰动开关设置
                        self.left_random_cps_enabled = value.lower() == "true"  # 转换为布尔值
                    elif key == "right_random_cps_enabled":  # 如果是右键随机扰动开关设置
                        self.right_random_cps_enabled = value.lower() == "true"  # 转换为布尔值
        except Exception as e:  # 如果读取失败
            print(f"加载配置失败: {e}")  # 打印错误信息
            self.save()  # 保存默认配置
        
        self.validate_and_fix()  # 加载后验证配置范围
    
    def save(self):  # 保存配置文件函数
        """保存配置到文件"""
        try:  # 尝试写入配置文件
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:  # 打开配置文件
                f.write(f"# 窗口是否置顶（true/false）\n")  # 写入注释
                f.write(f"topmost={str(self.topmost).lower()}\n")  # 写入置顶设置（确保小写）
                f.write(f"# 左键连点是否开启（true/false）\n")  # 写入注释
                f.write(f"left_click_enabled={str(self.left_click_enabled).lower()}\n")  # 写入左键设置
                f.write(f"# 右键连点是否开启（true/false）\n")  # 写入注释
                f.write(f"right_click_enabled={str(self.right_click_enabled).lower()}\n")  # 写入右键设置
                f.write(f"# 检测间隔秒数（0.1-2.0）\n")  # 写入注释
                f.write(f"check_interval={float(self.check_interval)}\n")  # 写入检测间隔（确保浮点数）
                f.write(f"# 连点增加的CPS数（1-20）\n")  # 写入注释
                f.write(f"bonus_cps={int(self.bonus_cps)}\n")  # 写入加成CPS（确保整数）
                f.write(f"# 左键触发连点的CPS阈值（1-20）\n")  # 写入注释
                f.write(f"left_activation_cps={int(self.left_activation_cps)}\n")  # 写入左键触发阈值（确保整数）
                f.write(f"# 右键触发连点的CPS阈值（1-20）\n")  # 写入注释
                f.write(f"right_activation_cps={int(self.right_activation_cps)}\n")  # 写入右键触发阈值（确保整数）
                f.write(f"# 连点最小持续时间秒数（0.1-5.0）\n")  # 写入注释
                f.write(f"min_click_duration={float(self.min_click_duration)}\n")  # 写入最小持续时间（确保浮点数）
                f.write(f"# CPS>-1开关状态（true/false）\n")  # 写入注释
                f.write(f"left_cps_minus1_enabled={str(self.left_cps_minus1_enabled).lower()}\n")  # 写入CPS>-1开关
                f.write(f"# CPS>-1切换绑定按键（如f1,f2等，为空则无）\n")  # 写入注释
                f.write(f"left_cps_minus1_toggle_key={self.left_cps_minus1_toggle_key if self.left_cps_minus1_toggle_key else ''}\n")  # 写入绑定按键
                f.write(f"{self.left_cps_minus1_toggle_key if self.left_cps_minus1_toggle_key else ''}{"="}{str(self.left_cps_minus1_enabled_key).lower()}\n")  # 写入绑定按键
                f.write(f"# CPS>-1关闭时恢复的上次CPS阈值（1-20）\n")  # 写入注释
                f.write(f"left_cps_minus1_last_cps={int(self.left_cps_minus1_last_cps)}\n")  # 写入上次CPS阈值
                f.write(f"# 随机扰动CPS总开关（true/false）\n")  # 写入注释
                f.write(f"random_cps_enabled={str(self.random_cps_enabled).lower()}\n")  # 写入随机扰动总开关
                f.write(f"# 左键随机扰动开关（true/false）\n")  # 写入注释
                f.write(f"left_random_cps_enabled={str(self.left_random_cps_enabled).lower()}\n")  # 写入左键随机扰动开关
                f.write(f"# 右键随机扰动开关（true/false）\n")  # 写入注释
                f.write(f"right_random_cps_enabled={str(self.right_random_cps_enabled).lower()}\n")  # 写入右键随机扰动开关
            return True  # 保存成功返回True
        except Exception as e:  # 如果写入失败
            print(f"保存配置失败: {e}")  # 打印错误信息
            return False  # 保存失败返回False

class CPSDisplayWindow:  # 定义CPS显示窗口类
    def __init__(self, clicker):  # 构造函数，clicker是连点器对象
        self.clicker = clicker  # 保存连点器引用，用于交互
        self.settings = clicker.settings  # 获取设置对象引用
        self.root = tk.Tk()  # 创建tkinter主窗口
        self.root.title("CPS监控")  # 设置窗口标题
        self.root.geometry("200x100")  # 设置窗口大小为200x100像素
        self.root.attributes("-topmost", self.settings.topmost)  # 根据配置设置窗口是否置顶
        self.root.overrideredirect(True)  # 移除窗口边框和标题栏
        
        # 设置窗口背景色为深灰色
        self.root.configure(bg="#2b2b2b")
        # 设置窗口透明度为85%
        self.root.attributes("-alpha", 0.85)
        
        # 创建左键CPS显示区域（Frame容器）
        self.left_frame = tk.Frame(self.root, bg="#2b2b2b")  # 创建容器，背景色深灰
        self.left_frame.pack(expand=True)  # 放置容器，居中扩展
        
        # 创建左键基础CPS标签
        self.left_cps_base = tk.Label(
            self.left_frame,  # 放在左键容器中
            text="左键: 0.00",  # 初始显示文字
            font=("Arial", 14, "bold"),  # 字体：Arial 14号 加粗
            fg="#00ff00",  # 文字颜色：绿色
            bg="#2b2b2b"  # 背景色：深灰
        )
        self.left_cps_base.pack(side="left")  # 靠左放置
        
        # 创建左键加成CPS标签（显示+15）
        self.left_cps_bonus = tk.Label(
            self.left_frame,  # 放在左键容器中
            text="",  # 初始为空
            font=("Arial", 14, "bold"),  # 字体：Arial 14号 加粗
            fg="#ff4444",  # 文字颜色：红色
            bg="#2b2b2b"  # 背景色：深灰
        )
        self.left_cps_bonus.pack(side="left")  # 靠左放置（在基础标签右边）
        
        # 创建右键CPS显示区域（Frame容器）
        self.right_frame = tk.Frame(self.root, bg="#2b2b2b")  # 创建容器
        self.right_frame.pack()  # 放置容器
        
        # 创建右键基础CPS标签
        self.right_cps_base = tk.Label(
            self.right_frame,  # 放在右键容器中
            text="右键: 0.00",  # 初始显示文字
            font=("Arial", 14, "bold"),  # 字体：Arial 14号 加粗
            fg="#ffaa00",  # 文字颜色：橙色
            bg="#2b2b2b"  # 背景色：深灰
        )
        self.right_cps_base.pack(side="left")  # 靠左放置
        
        # 创建右键加成CPS标签（显示+15）
        self.right_cps_bonus = tk.Label(
            self.right_frame,  # 放在右键容器中
            text="",  # 初始为空
            font=("Arial", 14, "bold"),  # 字体：Arial 14号 加粗
            fg="#ff4444",  # 文字颜色：红色
            bg="#2b2b2b"  # 背景色：深灰
        )
        self.right_cps_bonus.pack(side="left")  # 靠左放置
        
        # 创建状态标签
        self.status_label = tk.Label(
            self.root,  # 放在主窗口
            text="状态: 待机",  # 初始显示待机
            font=("Arial", 10),  # 字体：Arial 10号
            fg="#aaaaaa",  # 文字颜色：浅灰
            bg="#2b2b2b"  # 背景色：深灰
        )
        self.status_label.pack()  # 放置标签
        
        # 拖动窗口相关变量
        self.offset_x = 0  # 鼠标点击时相对于窗口左上角的X偏移
        self.offset_y = 0  # 鼠标点击时相对于窗口左上角的Y偏移
        self.is_dragging = False  # 标记是否正在拖动
        
        # 绑定鼠标事件实现拖动
        self.root.bind("<Button-1>", self.start_drag)  # 鼠标左键按下时调用start_drag
        self.root.bind("<B1-Motion>", self.do_drag)  # 鼠标左键按住移动时调用do_drag
        
        # 创建右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)  # 创建菜单，tearoff=0表示不显示分割线
        
        # 置顶子菜单
        self.menu.add_command(label="置顶", command=self.toggle_topmost)  # 添加置顶选项
        
        # 左键连点子菜单
        self.menu.add_command(label=f"左键连点: {'开启' if self.settings.left_click_enabled else '关闭'}", command=self.toggle_left_click)  # 添加左键连点开关
        
        # 右键连点子菜单
        self.menu.add_command(label=f"右键连点: {'开启' if self.settings.right_click_enabled else '关闭'}", command=self.toggle_right_click)  # 添加右键连点开关
        
        # 分隔线
        self.menu.add_separator()  # 添加分割线
        
        # 检测间隔子菜单
        self.check_interval_menu = tk.Menu(self.menu, tearoff=0)  # 创建检测间隔子菜单
        for interval in [0.1, 0.2, 0.5, 1.0, 2.0]:  # 遍历可选间隔值
            is_selected = interval == self.settings.check_interval  # 判断是否是当前选中值
            label = f"✓ {interval}秒" if is_selected else f"  {interval}秒"  # 选中项添加标记
            self.check_interval_menu.add_command(label=label, command=lambda i=interval: self.set_check_interval(i))  # 添加间隔选项
        self.menu.add_cascade(label="检测间隔", menu=self.check_interval_menu)  # 添加检测间隔子菜单
        
        # 加成CPS子菜单
        self.bonus_cps_menu = tk.Menu(self.menu, tearoff=0)  # 创建加成CPS子菜单
        for cps in [5, 10, 12, 15]:  # 遍历可选加成CPS值
            is_selected = cps == self.settings.bonus_cps  # 判断是否是当前选中值
            label = f"✓ +{cps}" if is_selected else f"  +{cps}"  # 选中项添加标记
            self.bonus_cps_menu.add_command(label=label, command=lambda c=cps: self.set_bonus_cps(c))  # 添加加成选项
        self.menu.add_cascade(label="加成CPS", menu=self.bonus_cps_menu)  # 添加加成CPS子菜单
        
               # 左键触发阈值子菜单
        self.left_activation_cps_menu = tk.Menu(self.menu, tearoff=0)  # 创建左键触发阈值子菜单
        
        # CPS>-1选项的子菜单
        self.left_cps_minus1_submenu = tk.Menu(self.left_activation_cps_menu, tearoff=0)  # 创建CPS>-1子菜单
        self.left_cps_minus1_submenu.add_command(
            label=f"{'开启' if self.settings.left_cps_minus1_enabled else '关闭'}",
            command=self.toggle_left_cps_minus1
        )  # 添加切换开关选项
        self.left_cps_minus1_submenu.add_command(
            label=f"绑定按键: {self.settings.left_cps_minus1_toggle_key.upper() if self.settings.left_cps_minus1_toggle_key else '无'}",
            command=self.bind_left_cps_minus1_key
        )  # 添加绑定按键选项
        
        # 添加CPS>-1选项（带子菜单）- 放在最前面，与其他阈值同级
        is_minus1_selected = self.settings.left_activation_cps == -1  # 判断是否选中CPS>-1
        minus1_label = f"✓ CPS>-1" if is_minus1_selected else f"  CPS>-1"  # 设置标签
        self.left_activation_cps_menu.add_cascade(label=minus1_label, menu=self.left_cps_minus1_submenu)  # 添加带子菜单的选项
        
        # 随机扰动CPS子菜单（放在左键触发阈值菜单中）
        self.left_random_cps_menu = tk.Menu(self.left_activation_cps_menu, tearoff=0)  # 创建左键随机扰动子菜单
        self.left_random_cps_menu.add_command(
            label=f"{'开启' if self.settings.left_random_cps_enabled else '关闭'}",
            command=self.toggle_left_random_cps
        )  # 添加切换开关选项
        self.left_activation_cps_menu.add_cascade(label="随机扰动CPS", menu=self.left_random_cps_menu)  # 添加随机扰动子菜单
        
        # 添加其他阈值选项
        for cps in [1, 2, 3, 4, 5, 10]:  # 遍历可选触发阈值
            is_selected = cps == self.settings.left_activation_cps  # 判断是否是当前选中值
            label = f"✓ CPS>{cps}" if is_selected else f"  CPS>{cps}"  # 选中项添加标记
            self.left_activation_cps_menu.add_command(label=label, command=lambda c=cps: self.set_left_activation_cps(c))  # 添加阈值选项
        
        self.menu.add_cascade(label="左键触发阈值", menu=self.left_activation_cps_menu)  # 添加左键触发阈值子菜单
        
        # 右键触发阈值子菜单
        self.right_activation_cps_menu = tk.Menu(self.menu, tearoff=0)  # 创建右键触发阈值子菜单
        for cps in [1, 2, 3, 4, 5, 6]:  # 遍历可选触发阈值
            is_selected = cps == self.settings.right_activation_cps  # 判断是否是当前选中值
            label = f"✓ CPS>{cps}" if is_selected else f"  CPS>{cps}"  # 选中项添加标记
            self.right_activation_cps_menu.add_command(label=label, command=lambda c=cps: self.set_right_activation_cps(c))  # 添加阈值选项
        
        # 右键随机扰动子菜单（放在右键触发阈值菜单中）
        self.right_random_cps_menu = tk.Menu(self.right_activation_cps_menu, tearoff=0)  # 创建右键随机扰动子菜单
        self.right_random_cps_menu.add_command(
            label=f"{'开启' if self.settings.right_random_cps_enabled else '关闭'}",
            command=self.toggle_right_random_cps
        )  # 添加切换开关选项
        self.right_activation_cps_menu.add_cascade(label="随机扰动CPS", menu=self.right_random_cps_menu)  # 添加随机扰动子菜单
        
        self.menu.add_cascade(label="右键触发阈值", menu=self.right_activation_cps_menu)  # 添加右键触发阈值子菜单
        
        # 连点时长子菜单
        self.click_duration_menu = tk.Menu(self.menu, tearoff=0)  # 创建连点时长子菜单
        for duration in [0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0]:  # 遍历可选连点时长
            is_selected = duration == self.settings.min_click_duration  # 判断是否是当前选中值
            label = f"✓ {duration}秒" if is_selected else f"  {duration}秒"  # 选中项添加标记
            self.click_duration_menu.add_command(label=label, command=lambda d=duration: self.set_min_click_duration(d))  # 添加时长选项
        self.menu.add_cascade(label="连点时长", menu=self.click_duration_menu)  # 添加连点时长子菜单
        
        # 分隔线
        self.menu.add_separator()  # 添加分割线
        
        # 随机扰动CPS子菜单
        self.random_cps_menu = tk.Menu(self.menu, tearoff=0)  # 创建随机扰动子菜单
        self.random_cps_menu.add_command(
            label=f"{'开启' if self.settings.random_cps_enabled else '关闭'}",
            command=self.toggle_random_cps
        )  # 添加切换开关选项
        self.menu.add_cascade(label="随机扰动CPS", menu=self.random_cps_menu)  # 添加随机扰动子菜单
        
        # 关闭选项
        self.menu.add_command(label="关闭", command=self.close_window)  # 添加关闭选项
        self.root.bind("<Button-3>", self.show_menu)  # 鼠标右键点击时显示菜单
        
    def start_drag(self, event):  # 开始拖动函数，event是鼠标事件对象
        """开始拖动"""
        self.offset_x = event.x  # 记录鼠标点击位置相对于窗口左上角的X偏移
        self.offset_y = event.y  # 记录鼠标点击位置相对于窗口左上角的Y偏移
        self.is_dragging = True  # 标记开始拖动
        
    def do_drag(self, event):  # 执行拖动函数
        """执行拖动"""
        if self.is_dragging:  # 如果正在拖动
            x = self.root.winfo_x() + event.x - self.offset_x  # 计算新X坐标：当前窗口X + 鼠标移动距离
            y = self.root.winfo_y() + event.y - self.offset_y  # 计算新Y坐标：当前窗口Y + 鼠标移动距离
            self.root.geometry(f"+{x}+{y}")  # 移动窗口到新位置
            
    def show_menu(self, event):  # 显示右键菜单函数
        """显示右键菜单"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)  # 在鼠标位置弹出菜单
        finally:
            self.menu.grab_release()  # 释放菜单焦点
            
    def toggle_left_click(self):  # 切换左键连点开关函数
        """切换左键连点开关"""
        self.settings.left_click_enabled = not self.settings.left_click_enabled  # 取反开关状态
        self.clicker.left_click_enabled = self.settings.left_click_enabled  # 同步到连点器对象
        self.settings.save()  # 保存配置
        self.menu.entryconfig(1, label=f"左键连点: {'开启' if self.settings.left_click_enabled else '关闭'}")  # 更新菜单文本
        print(f"左键连点已{'开启' if self.settings.left_click_enabled else '关闭'}")  # 打印提示信息
        
    def toggle_right_click(self):  # 切换右键连点开关函数
        """切换右键连点开关"""
        self.settings.right_click_enabled = not self.settings.right_click_enabled  # 取反开关状态
        self.clicker.right_click_enabled = self.settings.right_click_enabled  # 同步到连点器对象
        self.settings.save()  # 保存配置
        self.menu.entryconfig(2, label=f"右键连点: {'开启' if self.settings.right_click_enabled else '关闭'}")  # 更新菜单文本
        print(f"右键连点已{'开启' if self.settings.right_click_enabled else '关闭'}")  # 打印提示信息
        
    def toggle_topmost(self):  # 切换置顶状态函数
        """切换置顶状态"""
        self.settings.topmost = not self.settings.topmost  # 取反置顶状态
        self.root.attributes("-topmost", self.settings.topmost)  # 应用置顶状态
        self.settings.save()  # 保存配置
    
    def set_check_interval(self, interval):  # 设置检测间隔函数
        """设置检测间隔"""
        self.settings.check_interval = interval  # 设置检测间隔
        self.clicker.check_interval = interval  # 同步到连点器
        self.settings.save()  # 保存配置
        self.update_menu_selection(self.check_interval_menu, interval, [0.1, 0.2, 0.5, 1.0, 2.0], lambda v: f"{v}秒")  # 更新菜单标记
        print(f"检测间隔已设置为 {interval} 秒")  # 打印提示信息
    
    def set_bonus_cps(self, cps):  # 设置加成CPS函数
        """设置加成CPS"""
        self.settings.bonus_cps = cps  # 设置加成CPS
        self.clicker.bonus_cps = cps  # 同步到连点器
        self.settings.save()  # 保存配置
        self.update_menu_selection(self.bonus_cps_menu, cps, [5, 10, 12, 15], lambda v: f"+{v}")  # 更新菜单标记
        print(f"加成CPS已设置为 +{cps}")  # 打印提示信息
    
    def set_left_activation_cps(self, cps):  # 设置左键触发阈值函数
        """设置左键触发阈值"""
        # 如果当前是CPS>-1模式，切换到新阈值时需要保存这个阈值作为"上次选择的阈值"
        if self.settings.left_activation_cps == -1:
            self.settings.left_cps_minus1_last_cps = cps  # 保存为上次选择的阈值
        self.settings.left_activation_cps = cps  # 设置左键触发阈值
        self.clicker.left_activation_cps = cps  # 同步到连点器
        self.settings.save()  # 保存配置
        self.update_left_activation_cps_menu()  # 更新菜单显示
        print(f"左键触发阈值已设置为 CPS>{cps}")  # 打印提示信息
    
    def update_left_activation_cps_menu(self):  # 更新左键触发阈值菜单函数
        """更新左键触发阈值菜单显示"""
        # 删除所有菜单项
        self.left_activation_cps_menu.delete(0, tk.END)
        
        # 添加CPS>-1子菜单（放在最前面，与其他阈值同级）
        is_minus1_selected = self.settings.left_activation_cps == -1
        minus1_label = f"✓ CPS>-1" if is_minus1_selected else f"  CPS>-1"
        self.left_activation_cps_menu.add_cascade(label=minus1_label, menu=self.left_cps_minus1_submenu)
        
        # 添加普通阈值选项
        for cps in [1, 2, 3, 4, 5, 10]:
            is_selected = cps == self.settings.left_activation_cps
            label = f"✓ CPS>{cps}" if is_selected else f"  CPS>{cps}"
            self.left_activation_cps_menu.add_command(label=label, command=lambda c=cps: self.set_left_activation_cps(c))
        
        # 更新子菜单显示
        self.left_cps_minus1_submenu.entryconfig(0, label=f"{'开启' if self.settings.left_cps_minus1_enabled else '关闭'}")
        self.left_cps_minus1_submenu.entryconfig(1, label=f"绑定按键: {self.settings.left_cps_minus1_toggle_key.upper() if self.settings.left_cps_minus1_toggle_key else '无'}")
    def toggle_left_cps_minus1(self):  # 切换CPS>-1开关函数
        """切换CPS>-1开关状态"""
        # 如果即将关闭开关，需要恢复到上次选择的普通CPS阈值
        if self.settings.left_cps_minus1_enabled:
            last_cps = self.settings.left_cps_minus1_last_cps  # 获取上次选择的阈值
            self.settings.left_activation_cps = last_cps  # 恢复到上次选择的阈值
            self.clicker.left_activation_cps = last_cps  # 同步到连点器
            print(f"CPS>-1开关已关闭，恢复到CPS>{last_cps}")  # 打印提示信息
        else:
            # 如果即将开启开关，保存当前阈值作为"上次选择的阈值"
            if self.settings.left_activation_cps != -1:  # 只有当前不是-1时才保存
                self.settings.left_cps_minus1_last_cps = self.settings.left_activation_cps  # 保存当前阈值
            print(f"CPS>-1开关已开启")  # 打印提示信息
        
        self.settings.left_cps_minus1_enabled = not self.settings.left_cps_minus1_enabled  # 取反开关状态
        self.clicker.left_cps_minus1_enabled = self.settings.left_cps_minus1_enabled  # 同步到连点器
        self.settings.save()  # 保存配置
        self.update_left_activation_cps_menu()  # 更新菜单显示
    
    def bind_left_cps_minus1_key(self):  # 绑定CPS>-1切换按键函数
        """弹出对话框让用户按下要绑定的按键"""
        bind_window = tk.Toplevel(self.root)  # 创建绑定窗口
        bind_window.title("绑定按键")  # 设置窗口标题
        bind_window.geometry("250x100")  # 设置窗口大小
        bind_window.transient(self.root)  # 设置为子窗口
        bind_window.grab_set()  # 模态窗口
        
        tk.Label(bind_window, text="请按下要绑定的按键:", font=("Arial", 10)).pack(pady=10)  # 提示标签
        
        def on_key_press(event):
            """按键按下回调"""
            key_name = event.keysym.lower()  # 获取按键名称
            # 过滤特殊键
            if key_name in ('unknown', ''):
                return
            # 检查是否为保留按键（home和end），如果是则直接退出，不修改值
            if key_name in ('home', 'end'):
                bind_window.destroy()  # 关闭窗口，但不修改绑定值
                return
            self.settings.left_cps_minus1_toggle_key = key_name  # 保存按键
            self.clicker.left_cps_minus1_toggle_key = key_name  # 同步到连点器
            self.settings.save()  # 保存配置
            self.update_left_activation_cps_menu()  # 更新菜单显示
            print(f"CPS>-1切换按键已绑定: {key_name}")  # 打印提示信息
            bind_window.destroy()  # 关闭窗口
        
        bind_window.bind("<Key>", on_key_press)  # 绑定按键事件
        bind_window.focus_set()  # 设置焦点
        
    def set_left_cps_minus1_last_cps(self, cps):  # 设置CPS>-1恢复阈值函数
        """设置CPS>-1关闭时恢复的上次CPS阈值"""
        self.settings.left_cps_minus1_last_cps = cps  # 保存阈值
        self.settings.save()  # 保存配置
        self.update_left_activation_cps_menu()  # 更新菜单显示
        print(f"CPS>-1恢复阈值已设置为 CPS>{cps}")  # 打印提示信息
    
    def set_right_activation_cps(self, cps):  # 设置右键触发阈值函数
        """设置右键触发阈值"""
        self.settings.right_activation_cps = cps  # 设置右键触发阈值
        self.clicker.right_activation_cps = cps  # 同步到连点器
        self.settings.save()  # 保存配置
        self.update_menu_selection(self.right_activation_cps_menu, cps, [1, 2, 3, 4, 5, 6], lambda v: f"CPS>{v}")  # 更新菜单标记
        print(f"右键触发阈值已设置为 CPS>{cps}")  # 打印提示信息
    
    def set_min_click_duration(self, duration):  # 设置连点时长函数
        """设置连点最小时长"""
        self.settings.min_click_duration = duration  # 设置连点时长
        self.clicker.min_click_duration = duration  # 同步到连点器
        self.settings.save()  # 保存配置
        self.update_menu_selection(self.click_duration_menu, duration, [0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0], lambda v: f"{v}秒")  # 更新菜单标记
        print(f"连点时长已设置为 {duration} 秒")  # 打印提示信息
    
    def toggle_random_cps(self):  # 切换随机扰动CPS开关函数
        """切换随机扰动CPS总开关状态"""
        self.settings.random_cps_enabled = not self.settings.random_cps_enabled  # 取反开关状态
        self.clicker.random_cps_enabled = self.settings.random_cps_enabled  # 同步到连点器
        self.settings.save()  # 保存配置
        self.random_cps_menu.entryconfig(0, label=f"{'开启' if self.settings.random_cps_enabled else '关闭'}")  # 更新菜单文本
        print(f"随机扰动CPS已{'开启' if self.settings.random_cps_enabled else '关闭'}")  # 打印提示信息
    
    def toggle_left_random_cps(self):  # 切换左键随机扰动开关函数
        """切换左键随机扰动开关状态"""
        self.settings.left_random_cps_enabled = not self.settings.left_random_cps_enabled  # 取反开关状态
        self.clicker.left_random_cps_enabled = self.settings.left_random_cps_enabled  # 同步到连点器
        self.settings.save()  # 保存配置
        self.left_random_cps_menu.entryconfig(0, label=f"{'开启' if self.settings.left_random_cps_enabled else '关闭'}")  # 更新菜单文本
        print(f"左键随机扰动已{'开启' if self.settings.left_random_cps_enabled else '关闭'}")  # 打印提示信息
    
    def toggle_right_random_cps(self):  # 切换右键随机扰动开关函数
        """切换右键随机扰动开关状态"""
        self.settings.right_random_cps_enabled = not self.settings.right_random_cps_enabled  # 取反开关状态
        self.clicker.right_random_cps_enabled = self.settings.right_random_cps_enabled  # 同步到连点器
        self.settings.save()  # 保存配置
        self.right_random_cps_menu.entryconfig(0, label=f"{'开启' if self.settings.right_random_cps_enabled else '关闭'}")  # 更新菜单文本
        print(f"右键随机扰动已{'开启' if self.settings.right_random_cps_enabled else '关闭'}")  # 打印提示信息
    
    def update_menu_selection(self, menu, current_value, all_values, format_func):  # 更新菜单选中标记函数
        """更新菜单项的显示，标记当前选中的项"""
        for i, value in enumerate(all_values):  # 遍历所有选项
            formatted = format_func(value)  # 格式化显示文本
            if value == current_value:  # 如果是当前选中值
                menu.entryconfig(i, label=f"✓ {formatted}")  # 添加选中标记
            else:  # 如果不是当前选中值
                menu.entryconfig(i, label=f"  {formatted}")  # 添加空格对齐
        
    def close_window(self):  # 关闭窗口函数
        """关闭窗口"""
        self.settings.save()  # 保存当前配置
        self.clicker.is_running = False  # 停止连点器运行
        self.root.destroy()  # 销毁窗口
        
    def update_display(self, player_left_cps, player_right_cps, is_left_clicking, is_right_clicking):  # 更新显示内容函数
        """更新显示内容"""
        bonus_text = f"+{self.clicker.bonus_cps}"  # 获取当前配置的加成CPS文本
        
        # 左键显示
        if is_left_clicking:  # 如果左键正在连点
            self.left_cps_base.config(text=f"左键: {player_left_cps:.2f}")  # 显示玩家CPS
            self.left_cps_bonus.config(text=bonus_text)  # 显示红色加成
        else:  # 左键未连点
            self.left_cps_base.config(text=f"左键: {player_left_cps:.2f}")  # 显示玩家CPS
            self.left_cps_bonus.config(text="")  # 隐藏加成
        
        # 右键显示
        if is_right_clicking:  # 如果右键正在连点
            self.right_cps_base.config(text=f"右键: {player_right_cps:.2f}")  # 显示玩家CPS
            self.right_cps_bonus.config(text=bonus_text)  # 显示红色加成
        else:  # 右键未连点
            self.right_cps_base.config(text=f"右键: {player_right_cps:.2f}")  # 显示玩家CPS
            self.right_cps_bonus.config(text="")  # 隐藏加成
        
        status_parts = []  # 创建状态文字列表
        if is_left_clicking:  # 如果左键连点
            status_parts.append("左键连点")  # 添加左键状态
        if is_right_clicking:  # 如果右键连点
            status_parts.append("右键连点")  # 添加右键状态
        
        if status_parts:  # 如果有连点状态
            self.status_label.config(text="状态: " + "+".join(status_parts), fg="#ff4444")  # 显示连点状态，红色
        else:  # 没有连点
            self.status_label.config(text="状态: 待机", fg="#aaaaaa")  # 显示待机，灰色
        self.root.update()  # 刷新窗口显示
        
    def run(self):  # 运行GUI主循环函数
        """运行GUI主循环"""
        self.root.mainloop()  # 启动tkinter事件循环，保持窗口运行


class AutoClicker:  # 定义自动连点器类
    def __init__(self):  # 构造函数
        self.settings = Settings()  # 创建设置对象，加载配置
        self.mouse_controller = Controller()  # 创建鼠标控制器，用于模拟点击
        # 左键相关
        self.left_click_times = []  # 记录左键玩家点击的时间戳列表
        self.left_is_clicking = False  # 左键是否正在自动连点
        self.left_click_start_time = 0  # 左键连点开始的时间戳
        self.left_click_enabled = self.settings.left_click_enabled  # 左键连点开关
        # 右键相关
        self.right_click_times = []  # 记录右键玩家点击的时间戳列表
        self.right_is_clicking = False  # 右键是否正在自动连点
        self.right_click_start_time = 0  # 右键连点开始的时间戳
        self.right_click_enabled = self.settings.right_click_enabled  # 右键连点开关
        # 通用
        self.is_running = True  # 程序是否运行中
        self.last_check_time = time.time()  # 上次检测开关连点的时间戳
        self.check_interval = self.settings.check_interval  # 检测间隔秒数
        self.bonus_cps = self.settings.bonus_cps  # 连点增加的CPS数
        self.left_activation_cps = self.settings.left_activation_cps  # 左键触发连点的CPS阈值
        self.right_activation_cps = self.settings.right_activation_cps  # 右键触发连点的CPS阈值
        self.min_click_duration = self.settings.min_click_duration  # 连点最小持续时间（秒）
        self.left_cps_minus1_enabled = self.settings.left_cps_minus1_enabled  # CPS>-1开关状态
        self.left_cps_minus1_toggle_key = self.settings.left_cps_minus1_toggle_key  # CPS>-1切换绑定按键
        self.left_cps_minus1_last_cps = self.settings.left_cps_minus1_last_cps  # CPS>-1关闭时恢复的上次CPS阈值
        self.left_cps_minus1_enabled_key = self.settings.left_cps_minus1_enabled_key  # CPS>-1按键开关状态
        self.random_cps_enabled = self.settings.random_cps_enabled  # 随机扰动CPS总开关
        self.left_random_cps_enabled = self.settings.left_random_cps_enabled  # 左键随机扰动开关
        self.right_random_cps_enabled = self.settings.right_random_cps_enabled  # 右键随机扰动开关
        self.display_window = None  # GUI窗口对象引用
        self.ignore_next_click = {Button.left: False, Button.right: False}  # 标记是否忽略下一次自动点击
        self.alt_pressed = False  # 标记Alt键是否按下
        
    def on_click(self, x, y, button, pressed):  # 鼠标点击回调函数
        """检测鼠标点击事件（只记录玩家点击，忽略自动点击）"""
        if pressed:  # 如果是按下事件（不是松开）
            # 如果是自动点击，忽略并重置标记
            if self.ignore_next_click.get(button, False):  # 检查该按键是否标记为忽略
                self.ignore_next_click[button] = False  # 重置标记为不忽略
                return  # 直接返回，不记录这次点击
            
            # 记录玩家点击
            current_time = time.time()  # 获取当前时间戳
            if button == Button.left:  # 如果是左键
                self.left_click_times.append(current_time)  # 添加时间戳到左键列表
            elif button == Button.right:  # 如果是右键
                self.right_click_times.append(current_time)  # 添加时间戳到右键列表
    
    def get_realtime_cps(self):  # 实时计算CPS函数
        """实时计算玩家CPS（基于最近1秒的点击）"""
        current_time = time.time()  # 获取当前时间戳
        cutoff_time = current_time - 1.0  # 计算1秒前的时间戳
        
        # 清理1秒前的点击记录，只保留最近1秒的
        self.left_click_times = [t for t in self.left_click_times if t > cutoff_time]  # 过滤左键时间戳
        self.right_click_times = [t for t in self.right_click_times if t > cutoff_time]  # 过滤右键时间戳
        
        left_cps = len(self.left_click_times)  # 左键CPS = 最近1秒的点击次数
        right_cps = len(self.right_click_times)  # 右键CPS = 最近1秒的点击次数
        
        return left_cps, right_cps  # 返回左右键CPS
    
    def calculate_click_interval(self):  # 计算点击间隔函数
        """根据配置的加成CPS计算点击间隔"""
        interval = 1.0 / self.bonus_cps  # 间隔 = 1秒 / 加成CPS
        return interval  # 返回间隔时间（秒）
    
    def check_and_start_clicking(self, left_cps, right_cps):  # 检查并启动连点函数
        """检查并启动连点（同时处理左右键）"""
        # 检查左键连点（需要开关开启）
        if self.left_click_enabled and not self.left_is_clicking:  # 如果左键总开关开启且未在连点
            # CPS>-1模式：按键触发，只要CPS>-1（任何CPS都满足）且开关开启就触发
            if left_cps > self.left_activation_cps:  # -1时任何CPS都大于-1，满足条件
                if self.left_activation_cps == -1 and not self.left_cps_minus1_enabled:
                    pass  # CPS>-1模式但开关未开启，不触发
                else:
                    if self.left_activation_cps == -1 and self.left_cps_minus1_enabled_key:
                        print(f"左键CPS>-1模式开启，开始自动连点！")  # 打印启动信息
                    else:
                        print(f"左键CPS > {self.left_activation_cps}，开始自动连点！")  # 打印启动信息
                    self.left_is_clicking = True  # 设置左键连点状态为True
                    self.left_click_start_time = time.time()  # 记录左键连点开始时间
                    threading.Thread(target=self.start_auto_clicking, args=(Button.left, "left"), daemon=True).start()  # 启动新线程执行左键自动点击
        # 检查右键连点（需要开关开启）
        if self.right_click_enabled and right_cps > self.right_activation_cps and not self.right_is_clicking:  # 如果右键开关开启且CPS大于阈值且未在连点
            print(f"右键CPS > {self.right_activation_cps}，开始自动连点！")  # 打印启动信息
            self.right_is_clicking = True  # 设置右键连点状态为True
            self.right_click_start_time = time.time()  # 记录右键连点开始时间
            threading.Thread(target=self.start_auto_clicking, args=(Button.right, "right"), daemon=True).start()  # 启动新线程执行右键自动点击
        
        # 检查左键停止条件
        if self.left_is_clicking:  # 如果左键正在连点
            # CPS>-1模式：只有当CPS>-1开关关闭或左键总开关关闭时才停止
            if self.left_activation_cps == -1:
                if not self.left_cps_minus1_enabled or not self.left_click_enabled or not self.left_cps_minus1_enabled_key:  # CPS>-1开关或总开关关闭
                    elapsed_time = time.time() - self.left_click_start_time  # 计算左键连点已持续时间
                    if elapsed_time >= self.min_click_duration:  # 如果持续时间大于等于最小时间
                        print(f"左键CPS>-1开关关闭，停止自动连点（已持续{elapsed_time:.1f}秒）")  # 打印停止信息
                        self.left_is_clicking = False  # 设置左键连点状态为False
                    else:  # 持续时间不足
                        print(f"左键连点持续{elapsed_time:.1f}秒，未达最小持续时间，继续连点")  # 打印继续信息
            elif left_cps <= self.left_activation_cps:  # 普通CPS阈值模式
                elapsed_time = time.time() - self.left_click_start_time  # 计算左键连点已持续时间
                if elapsed_time >= self.min_click_duration:  # 如果持续时间大于等于1秒
                    print(f"左键CPS <= {self.left_activation_cps}，停止自动连点（已持续{elapsed_time:.1f}秒）")  # 打印停止信息
                    self.left_is_clicking = False  # 设置左键连点状态为False
                else:  # 持续时间不足1秒
                    print(f"左键连点持续{elapsed_time:.1f}秒，未达最小持续时间，继续连点")  # 打印继续信息
        
        # 检查右键停止条件
        if right_cps <= self.right_activation_cps and self.right_is_clicking:  # 如果右键CPS小于等于阈值且正在连点
            elapsed_time = time.time() - self.right_click_start_time  # 计算右键连点已持续时间
            if elapsed_time >= self.min_click_duration:  # 如果持续时间大于等于1秒
                print(f"右键CPS <= {self.right_activation_cps}，停止自动连点（已持续{elapsed_time:.1f}秒）")  # 打印停止信息
                self.right_is_clicking = False  # 设置右键连点状态为False
            else:  # 持续时间不足1秒
                print(f"右键连点持续{elapsed_time:.1f}秒，未达最小持续时间，继续连点")  # 打印继续信息
    
    def auto_click(self):  # 自动点击主循环函数
        """自动点击主循环"""
        print("自动连点器已启动，按 'home' 键开启连点，按 'end' 键关闭连点")  # 打印启动信息
        print("等待鼠标点击以检测CPS...")  # 打印等待信息
        
        while self.is_running:  # 主循环，程序运行时持续执行
            # 实时获取玩家CPS
            player_left_cps, player_right_cps = self.get_realtime_cps()  # 调用函数获取左右键CPS
            
            # 更新GUI显示（实时）
            if self.display_window:  # 如果GUI窗口存在
                self.display_window.update_display(  # 调用窗口更新函数
                    player_left_cps, player_right_cps,  # 传入玩家CPS
                    self.left_is_clicking, self.right_is_clicking  # 传入连点状态
                )
            
            # 根据配置的检测间隔检测是否开关连点
            current_time = time.time()  # 获取当前时间
            if current_time - self.last_check_time >= self.check_interval:  # 如果距离上次检测超过配置间隔
                self.last_check_time = current_time  # 更新上次检测时间
                
                #print(f"检测 - 玩家左键CPS: {player_left_cps:.2f}, 玩家右键CPS: {player_right_cps:.2f}")  # 打印检测信息
                
                # 同时检查左右键连点（只用玩家CPS）
                self.check_and_start_clicking(player_left_cps, player_right_cps)  # 调用检测函数，同时处理左右键
            
            time.sleep(0.05)  # 休眠50毫秒，避免CPU占用过高
    
    def start_auto_clicking(self, button, button_type):  # 开始自动点击函数
        """开始自动点击"""
        interval = self.calculate_click_interval()  # 计算点击间隔时间
        
        while self.is_running:  # 循环执行自动点击
            if button_type == "left" and not self.left_is_clicking:  # 如果是左键且连点状态为False
                break  # 退出循环
            elif button_type == "right" and not self.right_is_clicking:  # 如果是右键且连点状态为False
                break  # 退出循环
            
            # 标记忽略下一次点击（防止自动点击被计入玩家CPS）
            self.ignore_next_click[button] = True  # 设置该按键的忽略标记为True
            
            # 执行点击
            self.mouse_controller.click(button, 1)  # 模拟鼠标点击一次
            
            # 等待间隔时间（如果开启随机扰动则使用随机间隔）
            if self.random_cps_enabled:  # 检查总开关
                # 检查对应按键的开关
                is_random_enabled = False
                if button_type == "left" and self.left_random_cps_enabled:
                    is_random_enabled = True
                elif button_type == "right" and self.right_random_cps_enabled:
                    is_random_enabled = True
                
                if is_random_enabled:
                    # 应用随机扰动[-2, +2]
                    perturbation = random.uniform(-2, 2)  # 生成-2到+2的随机数
                    perturbed_cps = self.bonus_cps + perturbation  # 扰动后的CPS
                    perturbed_interval = 1.0 / perturbed_cps  # 计算扰动后的间隔
                    time.sleep(perturbed_interval)  # 休眠随机间隔时间
                else:
                    time.sleep(interval)  # 休眠固定间隔时间
            else:
                time.sleep(interval)  # 休眠固定间隔时间
    
    def on_press(self, key):  # 键盘按键回调函数
        """键盘事件监听"""
        # 检查是否是CPS>-1切换绑定按键（无论开关状态都检测，实现切换功能）
        if self.left_cps_minus1_toggle_key:
            try:
                # 将按键转换为字符串比较
                key_char = None
                if hasattr(key, 'char') and key.char:
                    key_char = key.char.lower()
                elif hasattr(key, 'name') and key.name:
                    key_char = key.name.lower()
                
                if key_char == self.left_cps_minus1_toggle_key.lower():
                    # 切换CPS>-1开关状态
                    was_enabled = self.left_cps_minus1_enabled_key
                    self.left_cps_minus1_enabled_key = not self.left_cps_minus1_enabled_key
                    self.settings.left_cps_minus1_enabled_key = self.left_cps_minus1_enabled_key
                    if was_enabled:
                        # 如果之前是开启状态，现在要关闭，恢复到上次选择的阈值
                        last_cps = self.settings.left_cps_minus1_last_cps
                        self.left_activation_cps = last_cps
                        self.settings.left_activation_cps = last_cps
                        print(f"CPS>-1模式已关闭（通过绑定按键），恢复到CPS>{last_cps}")
                    else:
                        # 如果之前是关闭状态，现在要开启，保存当前阈值
                        if self.left_activation_cps != -1:
                            self.settings.left_cps_minus1_last_cps = self.left_activation_cps
                            self.left_activation_cps = -1
                            self.settings.left_activation_cps = -1
                            print(f"CPS>-1模式已开启（通过绑定按键），保存当前阈值CPS>{self.settings.left_cps_minus1_last_cps}")
                        else:
                            # 如果当前已经是-1，直接使用保存的阈值
                            last_cps = self.settings.left_cps_minus1_last_cps
                            self.left_activation_cps = last_cps
                            self.settings.left_activation_cps = last_cps
                            print(f"CPS>-1模式已关闭（通过绑定按键），恢复到CPS>{last_cps}")
                    
                    self.settings.save()
                    if self.display_window:
                        self.display_window.update_left_activation_cps_menu()
                    return  # 处理完毕，不再执行后续逻辑
            except Exception:
                pass  # 忽略转换错误
        
        # 检查Alt+F4组合键关闭程序
        try:
            key_name = None
            if hasattr(key, 'name') and key.name:
                key_name = key.name.lower()
            
            # 检测Alt键按下状态
            if key_name in ('alt', 'alt_l', 'alt_r'):
                self.alt_pressed = True
                return  # Alt键不触发其他逻辑
            
            # 检测F4键且Alt键同时按下
            if key_name == 'f4' and self.alt_pressed:
                print("Alt+F4按下，关闭程序")
                self.is_running = False  # 停止程序运行
                if self.display_window:
                    self.display_window.close_window()  # 关闭GUI窗口
                return  # 处理完毕
        except Exception:
            pass
        
        if key == keyboard.Key.home:  # 如果按下的是HOME键
            print("HOME键按下，开启连点检测")  # 打印提示信息
            self.left_click_enabled = True  # 开启左键连点
            self.right_click_enabled = True  # 开启右键连点
            self.settings.left_click_enabled = True  # 同步到设置
            self.settings.right_click_enabled = True  # 同步到设置
            self.settings.save()  # 保存配置
            if self.display_window:  # 如果窗口存在
                self.display_window.menu.entryconfig(1, label="左键连点: 开启")  # 更新左键菜单
                self.display_window.menu.entryconfig(2, label="右键连点: 开启")  # 更新右键菜单
        elif key == keyboard.Key.end:  # 如果按下的是END键
            print("END键按下，关闭连点检测")  # 打印提示信息
            self.left_click_enabled = False  # 关闭左键连点
            self.right_click_enabled = False  # 关闭右键连点
            self.left_is_clicking = False  # 停止左键连点
            self.right_is_clicking = False  # 停止右键连点
            self.settings.left_click_enabled = False  # 同步到设置
            self.settings.right_click_enabled = False  # 同步到设置
            self.settings.save()  # 保存配置
            if self.display_window:  # 如果窗口存在
                self.display_window.menu.entryconfig(1, label="左键连点: 关闭")  # 更新左键菜单
                self.display_window.menu.entryconfig(2, label="右键连点: 关闭")  # 更新右键菜单
    
    def on_release(self, key):  # 键盘按键释放 回调函数
        """键盘按键释放监听"""
        try:
            key_name = None
            if hasattr(key, 'name') and key.name:
                key_name = key.name.lower()
            
            # 检测Alt键释放，重置状态
            if key_name in ('alt', 'alt_l', 'alt_r'):
                self.alt_pressed = False
        except Exception:
            pass
    
    def run(self):  # 运行自动连点器函数
        """运行自动连点器"""
        # 创建并显示GUI窗口
        self.display_window = CPSDisplayWindow(self)  # 创建显示窗口对象，传入自身引用
        
        # 启动鼠标监听器
        mouse_listener = mouse.Listener(on_click=self.on_click)  # 创建鼠标监听器，绑定点击回调
        mouse_listener.start()  # 启动监听器
        
        # 启动键盘监听器
        keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)  # 创建键盘监听器，绑定按键回调
        keyboard_listener.start()  # 启动监听器
        
        # 在单独的线程中运行自动点击主循环
        auto_click_thread = threading.Thread(target=self.auto_click, daemon=True)  # 创建线程，运行自动点击循环
        auto_click_thread.start()  # 启动线程
        
        # 在主线程中运行GUI（tkinter必须在主线程运行）
        try:
            self.display_window.run()  # 运行GUI主循环
        except KeyboardInterrupt:  # 如果用户按下Ctrl+C
            print("程序被中断")  # 打印中断信息
        finally:  # 无论是否异常都会执行
            self.settings.save()  # 保存最终配置
            self.is_running = False  # 设置程序运行状态为False
            mouse_listener.stop()  # 停止鼠标监听器
            keyboard_listener.stop()  # 停止键盘监听器
            print("自动连点器已停止")  # 打印停止信息

if __name__ == "__main__":
    clicker = AutoClicker()
    clicker.run()