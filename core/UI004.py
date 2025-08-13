# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
import sys
import os
import time
import multiprocessing as mp
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, 
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QScrollArea,QLineEdit,QFileDialog,
    QListWidget,QSpinBox,QMessageBox,
    QListWidgetItem, QGroupBox, QSlider
)
from PyQt6.QtGui import QPixmap, QFont,QImage,QDragEnterEvent, QDropEvent,QIcon
from PyQt6.QtCore import Qt,QEvent,QUrl
import qt_material 
from PIL import Image
import io
def get_path(relative_path):
        try:
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue] # pyinstaller打包后的路径
        except AttributeError:
            base_path = os.path.abspath(".") # 当前工作目录的路径
        return os.path.normpath(os.path.join(base_path, relative_path))
def is_hidden_file(file_path: str) -> bool:
    """判断文件是否为隐藏文件（跨平台支持）"""
    if os.name == 'nt':  # Windows系统
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
        return (attrs != -1) and (attrs & 2)  # 2对应FILE_ATTRIBUTE_HIDDEN
    else:  # Linux/macOS系统
        return os.path.basename(file_path).startswith('.')
def import_data_module(module_name, relative_path):
    import importlib.util
    """从PyInstaller打包的data中导入模块"""
    # 使用已有函数获取完整路径
    module_path = get_path(relative_path)   
    # 检查文件是否存在
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"模块不存在: {module_path}")
    # 动态导入模块
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec) # pyright: ignore[reportArgumentType]
    spec.loader.exec_module(module) # pyright: ignore[reportOptionalMemberAccess]
    return module

#这是本软件的功能：
rw=('声音转文字','文档压缩',"图片转pdf", "pdf加水印", "提取pdf文字", 
    "图片转换", "词云生成", "文件排序",'视频字幕','按比例裁图',
    '图片识字','文件加密','压缩视频','提取音频','调整视频尺寸','裁剪视频',
    '视频转GIF','视频加水印','获取视频信息','转帧','音视频合流')
# def sn():   
#     # global screen_width,screen_height
#     #多进程下global一点都不好用（,提取为顶级函数吧,不用在各层函数间传来传去了
#     #没有初始化QApplication实例,不能顶层调用（
#     return (w,h)
#网上说多次求屏幕参数和信号槽传递性能差不多，具体差异有待进一步研究。
#在qtdesiner已经设好了长宽比，如果没有异常，就不用屏幕参数了。
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
        # QTimer.singleShot(0, self.run_once)
        # # QApplication.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi, True)
        self.initUI()
    # def run_once(self):
    #     print()
    def initUI(self):
        # 获取主屏幕尺寸
        screen =QApplication.primaryScreen()
        screen_geometry = screen.geometry()   # type: ignore
        screen_width,screen_height=screen_geometry.width(),screen_geometry.height() # pyright: ignore[reportIndexIssue]
        
        # 基础缩放因子 - 可调整此值改变整体大小
        self.scale_factor = 1.2
        
        # ---------- 窗口基础设置 ----------
        self.setWindowTitle("Easy Transcriber")
        # 设置窗口大小为屏幕的80%，避免全屏可能带来的问题
        self.resize(int(screen_width * 0.88), int(screen_height * 0.75))
        # 禁止窗口缩放
        self.setFixedSize(self.size())
        self.center_window()
        # ---------- 中心组件与主布局 ----------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 去除默认边距
        
        # ---------- 左侧侧边栏 ----------
        # ---------- --------- ----------
        self.sidebar = QFrame()
        background_label = QLabel(self.sidebar)

        # 使用相对比例设置侧边栏宽度，乘以缩放因子
        sidebar_width = int(screen_width * 0.18 * self.scale_factor)
        self.sidebar.setFixedWidth(sidebar_width)

        # 加载背景图片
        pil_image = Image.open(get_path(r"pictures\微信图片_20250711152632.png"))    
        scaled_pil_image = pil_image.resize(
            (self.sidebar.width(), int(screen_height * 0.749)),
            Image.Resampling.LANCZOS
        )   
        buffer = io.BytesIO()
        scaled_pil_image.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(False)        
        background_label.setGeometry(0, 0, self.sidebar.width(), int(screen_height * 0.75))

        # 创建滚动区域
        scroll_area = QScrollArea(self.sidebar)
        scroll_area.setWidgetResizable(True)  # 让内容自适应滚动区域
        scroll_area.setStyleSheet("background-color: transparent; border: none;")  # 隐藏边框

        # 滚动区域的内容容器
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_layout.setContentsMargins(0, 0, 0, 0)  # 去除内边距
        # scroll_layout.setStyleSheet("background-color: transparent; border: none;")

        # 侧边栏按钮
        btn_names = ["声音转文字", "文档压缩", "图片转pdf", "pdf加水印", "提取pdf文字", "图片转换", "词云生成", "文件排序",'视频字幕','按比例裁图','图片识字','文件加密','关于']
        for name in btn_names:
            btn = QPushButton(name)
            btn.setStyleSheet(f"""
        QPushButton {{
            color: white; 
            background-color: transparent;  /* 完全透明背景 */
            border-radius: {3 * self.scale_factor}px;
            border: none; 
            padding: {12 * self.scale_factor}px 0;
            text-align: center;
            font-size: {14 * self.scale_factor}px;
            width: 100%;
        }}
        QPushButton:hover {{
            background-color: #393C43;  /* 悬停时显示的背景色 */
        }}
            """)
            btn.setToolTip("使用内置模型，无需联网。")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, n=name: self.handle_sidebar_click(n))
            #加lambda为编译成pyd后正确运行所必须！
            #否则：TypeError: handle_sidebar_click() takes exactly 2 positional argument (3 given)
            
            scroll_layout.addWidget(btn)


        # 设置滚动区域内容并添加到侧边栏
        scroll_area.setWidget(scroll_content)

        # 侧边栏主布局
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll_area)  # 将滚动区域加入侧边栏
        qt_material.apply_stylesheet(
            self.sidebar,  # 传入父窗口（或应用实例）
            theme='dark_teal.xml',
              # 指定仅对该组件及其子组件生效
        )

        # # ---------- 右侧主内容区 ----------
        main_content = QWidget()
        main_layout.addWidget(self.sidebar)#左菜单
        main_layout.addWidget(main_content)#右下
         
        # # 主内容区用垂直布局
        content_layout = QVBoxLayout(main_content)

        # ---------- 顶部横幅 ----------
        self.banner = QFrame()
        # 使用相对比例设置横幅高度，乘以缩放因子
        banner_height = int(screen_height * 0.4)
        self.banner.setFixedHeight(banner_height)
        # self.banner.setStyleSheet('''background-color: #393C43;''')
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(0, 0, 0, 0) 

        cackground_label = QLabel(self.banner)
        pil_image = Image.open(get_path(r"pictures\bg37 副本.png") )   
        # 高质量缩放（使用Lanczos算法）
        scaled_pil_image = pil_image.resize(
            (int(self.banner.width()*1.29), self.banner.height()),
            Image.Resampling.LANCZOS  # PIL中最高质量的缩放算法
        )   
        # 转换为Qt可使用的格式
        buffer = io.BytesIO()
        scaled_pil_image.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)
        cackground_label.setPixmap(pixmap)
        cackground_label.setScaledContents(False)  # 允许图片缩放      
        # 设置label覆盖整个frame
        cackground_label.setGeometry(0, 0, int(self.banner.width()*1.4), self.banner.height())
        content_layout.addWidget(self.banner)#右上
        # cackground_label.setContentsMargins(0, 0, 0, 0) #无效？？？？？？？？


        # ---------- 任务卡片区（滚动区域，避免内容超出） ----------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_layout.addWidget(scroll_area)

        # 滚动区域内容容器
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        card_layout = QVBoxLayout(scroll_widget)

        # 标题
        task_title = QLabel("   任务>")
        task_title.setFont(QFont("Microsoft YaHei", int(18 * self.scale_factor), QFont.Weight.Bold))
        task_title.setStyleSheet("color: white;border: none;")
        card_layout.addWidget(task_title)
        
        # 卡片网格（示例 6 个任务，2 行 3 列）
        grid = QGridLayout()
        grid.setSpacing(int(20 * self.scale_factor))

        tasks = [
            ("压缩视频",get_path(r"pictures\Bronya.png")),
            ("提取音频",get_path(r"pictures\Herta.png")),
            ("调整视频尺寸",get_path(r"pictures\icon.png")),
            ("裁剪视频",get_path(r"pictures\JingYuan.png")),
            ("视频转GIF",get_path(r"pictures\SilverWolf.png")),
            ("视频加水印",get_path(r"pictures\Yanqing.png")),
            ("获取视频信息",get_path(r"pictures\微信图片_20250729190609.png")),
            ("转帧",get_path(r"pictures\微信图片_20250729190627.png")),
            ("音视频合流",get_path(r"pictures\微信图片_20250729190633.png")),
        ]

        # 根据屏幕尺寸计算卡片大小，乘以缩放因子
        card_width = int((screen_width * 0.7 - 110) / 3) -10
        card_height = int(screen_height * 0.4 )
        
        for i, (text, img) in enumerate(tasks):
            # 卡片容器
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #2C2F33; 
                    
                    border: None;
                }}
            """)
            card.setFixedSize(card_width, card_height)

            # 安装事件过滤器以监测鼠标状态
            card.installEventFilter(self)
            # 存储卡片标识信息
            card.setProperty("task_name", text)
            
            # 卡片布局（图片 + 文字）
            card_layout_inner = QVBoxLayout(card)
            card_layout_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # 图片（示例用占位，实际替换为 QPixmap 加载）
            img_label = QLabel()
            img_size = int(card_height * 0.7)
                # 缩放（使用Lanczos算法）
            pil_image=Image.open(img)
            scaled_pil_image = pil_image.resize(
                (img_size, img_size),
                Image.Resampling.LANCZOS  
            )
            
            # 转换为Qt可使用的格式
            buffer = io.BytesIO()
            scaled_pil_image.save(buffer, format="PNG")
            qimage = QImage.fromData(buffer.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            img_label.setPixmap(QPixmap(pixmap))
            card_layout_inner.addWidget(img_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # 文字
            text_label = QLabel(text)
            text_label.setStyleSheet("color: white;border: none;")
            text_label.setFont(QFont("Microsoft YaHei", int(14 * self.scale_factor)))
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout_inner.addWidget(text_label)

             # 创建与卡片同大小的不可见按钮
            card_button = QPushButton(card)
            card_button.setFixedSize(card_width, card_height)
            card_button.setGeometry(0, 0, card_width, card_height)
            card_button.setStyleSheet("background-color: transparent; border: none;")
            card_button.setCursor(Qt.CursorShape.PointingHandCursor)  # 手型光标提示
            card_button.setToolTip("使用ffmpeg技术")
            # 绑定点击事件
            card_button.clicked.connect(lambda checked=False, t=text: self.perform_task(t))

            # 放入网格
            row = i // 3
            col = i % 3
            grid.addWidget(card, row, col)

        card_layout.addLayout(grid)
        time.sleep(1.5)
        
        # ---------- 显示窗口 ----------
        self.show()

    def handle_sidebar_click (self,n):
        if n=="声音转文字":
            self.start_child_process(getvoice,1)
        elif n=="文档压缩":
            self.start_child_process(addx,2)
        elif n=="图片转pdf":
            self.start_child_process(pi_to_pd,3)
        elif n== "pdf加水印":
            self.start_child_process(mark,4)
        elif n=="提取pdf文字":
            self.start_child_process(pdgetword,5)
        elif n=="图片转换":
            self.start_child_process(pi_to_pi,6)
        elif n== "词云生成":
            self.start_child_process(wc,7)
        elif n=="文件排序":
            self.start_child_process(od,8)
        elif n=='视频字幕':
            self.start_child_process(cover,9)
        elif n=='按比例裁图':
            self.start_child_process(rate,10)
        elif n=='图片识字':
            self.start_child_process(pigetword,11)
        elif n=='文件加密':
            self.start_child_process(aes,12)
        elif n=='关于':
            QMessageBox.information(self, "关于", 
                                '''
            Copyright (c) 2025 Easy
    Easy Transcriber is licensed under Mulan PSL v2.
    You can use this software according to the terms and conditions of the Mulan PSL v2.
    You may obtain a copy of Mulan PSL v2 at:
            http://license.coscl.org.cn/MulanPSL2
    THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
    EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
    MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
    See the Mulan PSL v2 for more details.
    本软件包含的第三方组件版权归其各自所有者所有。
        本软件开源免费，若为此付了钱请即退款。
    详细信息参见软件所在文件夹的NOTICE和LICENSE文件。
        使用说明参见软件所在文件夹的README文件。
项目网址：https://github.com/Easy-0-1/Transcriber
            ''')

    def eventFilter(self, obj, event): # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(obj, QFrame) and obj.property("task_name") is not None:
            # 鼠标进入 - 高亮
            if event.type() == QEvent.Type.Enter:
                obj.setStyleSheet(f"""
                    QFrame {{
                        background-color: #34383c;
                        border-radius: {3 * self.scale_factor}px;
                        border: {0.5 * self.scale_factor}px solid #666;
                    }}
                """)
                return True
            
            # 鼠标离开 - 恢复原样
            elif event.type() == QEvent.Type.Leave:
                obj.setStyleSheet(f"""
                    QFrame {{
                        background-color: #2C2F33;
                        border-radius: {3 * self.scale_factor}px;
                        border: none;
                    }}
                """)
                return True
        
        return super().eventFilter(obj, event)
    
    def perform_task(self, task_name):
        """处理卡片点击事件，根据任务名称执行对应操作"""
        if task_name == "压缩视频":
            self.start_child_process(press,13)
        elif task_name == "提取音频":
            self.start_child_process(grapevoice,14)
        elif task_name == "调整视频尺寸":
            self.start_child_process(pullruler,15)
        elif task_name == "裁剪视频":
            self.start_child_process(cut,16)
        elif task_name == "视频转GIF":
            self.start_child_process(ve_to_gi,17)
        elif task_name == "视频加水印":
            self.start_child_process(draw,18)
        elif task_name == "获取视频信息":
            self.start_child_process(hear,19)
        elif task_name == "转帧":
            self.start_child_process(shake,20)
        elif task_name == "音视频合流":
            self.start_child_process(together,21)

    def center_window(self):
        # 获取主屏幕的几何信息
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry() # type: ignore
        
        # 计算窗口居中位置
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        
        # 移动窗口
        self.move(window_geometry.topLeft())

    # 启动新的子窗口进程
    def start_child_process(self,target,args): 
        #print(f"执行任务: {rw[args-1]}…………")
        #这里的arg可以传一个任务名，一直传到子窗口应用，作为标题和功能分支          
        process = mp.Process(target=target,args=(args,))
        #要用元组包起来
        # process.daemon = True#守护进程，主进程结束后立即结束
        process.start()
    
# 子窗口应用 - 运行在独立进程中
def child_window(t):
    class FileFolderListWidget(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
            self.font_size = 17  # 默认字体大小
            self.initUI()
            self.q=[]
        def initUI(self):
            # 创建主布局
            main_layout = QVBoxLayout()
            
            # 创建字体大小调整滑块
            font_layout = QHBoxLayout()
            font_label = QLabel("字体大小:")
            self.font_slider = QSlider(Qt.Orientation.Horizontal)
            self.font_slider.setMinimum(8)
            self.font_slider.setMaximum(24)
            self.font_slider.setValue(self.font_size)
            self.font_slider.setTickInterval(2)
            self.font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.font_slider.valueChanged.connect(lambda x: self.change_font_size(x))
            
            font_layout.addWidget(font_label)
            font_layout.addWidget(self.font_slider)
            main_layout.addLayout(font_layout)
            
            # 创建拖放区域
            self.drop_group = QGroupBox("拖放区域")
            drop_layout = QVBoxLayout()
            if t ==4:
                self.drop_label = QLabel("拖放水印图片到此处")
            elif t==21:
                self.drop_label = QLabel("拖放音频到此处")
            elif t==18:
                self.drop_label = QLabel("拖放视频到此处")
            else:
                self.drop_label = QLabel("拖放文件或文件夹到此处\n可以拖入父文件夹，我们会自动递归遍历")

            self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drop_label.setMinimumHeight(100)
            
            drop_layout.addWidget(self.drop_label)
            self.drop_group.setLayout(drop_layout)
            
            # 创建文件列表区域
            self.file_group = QGroupBox("文件列表")
            file_layout = QVBoxLayout()
            
            # 使用QListWidget并设置字体大小
            self.file_list = QListWidget()
            self.file_list.setAlternatingRowColors(True)
            
        # 状态栏
            if t==1:
                self.status_label = QLabel("添加音视频文件")
            elif t==2:
                self.status_label = QLabel("添加.doc.ppt.xls文件")
            elif t ==5:
                self.status_label = QLabel("添加pdf文件")
            elif t==6:
                self.status_label = QLabel("添加图片，注意不是所有原格式都能转换成预期格式")
            elif t in {8,12}:
                self.status_label = QLabel("添加文件")
                #应该没人要跨文件夹排序吧？
            # elif t in (9,13,14,15,16,17,18,19,20):
            elif t==9 or 13<=t<=20:
                self.status_label = QLabel("添加视频")
            elif t in {3,4,10,11}:
            # elif t == 3 or t == 10 or t==11:
                #在t<10时，按位掩码比or 快。
                #在仅三项时，元组比前两者快。
                #我发现：
                #项多数小位运算，集合次之，项少连续直接比，最后选元组。
                self.status_label = QLabel("添加图片")   
            else:
                self.status_label = QLabel("添加音频") 

            
            file_layout.addWidget(self.file_list)
            file_layout.addWidget(self.status_label)
            self.file_group.setLayout(file_layout)
            
            # 创建按钮区域
            self.button_layout = QHBoxLayout()
            
            
            self.browse_files_button = QPushButton("选择文件")
            self.browse_files_button.clicked.connect(lambda: self.browse_files())
            if t not in {4,18,21}:
                self.browse_folder_button = QPushButton("选择文件夹")
                self.browse_folder_button.clicked.connect(lambda: self.browse_folder())
            
            self.clear_button = QPushButton("清空列表")
            self.clear_button.clicked.connect(lambda: self.clear_list())

            self.close_button = QPushButton("确认")
            self.close_button.clicked.connect(lambda: self.sure()) # pyright: ignore[reportOptionalMemberAccess]
            
            self.button_layout.addWidget(self.browse_files_button)
            if t not in {4,21,18}:
                self.button_layout.addWidget(self.browse_folder_button)
            self.button_layout.addWidget(self.clear_button)
            self.button_layout.addWidget(self.close_button)
            
            # 添加所有组件到主布局
            main_layout.addWidget(self.drop_group)
            main_layout.addWidget(self.file_group)
            main_layout.addLayout(self.button_layout)
            
            # 设置布局
            self.setLayout(main_layout)
            
            # 启用拖放
            self.setAcceptDrops(True)
            
            # 初始化样式（确保所有控件都已创建后再调用）
            self.update_styles()
        
        #这个如果能全局使用就可以使用qtmaterial了。
        def update_styles(self):
            # 更新所有控件的字体大小
            font_style = f"font-size: {self.font_size}px;"
            
            self.drop_label.setStyleSheet(f"{font_style} border: 2px dashed #aaa; padding: 20px;")
            self.file_list.setStyleSheet(font_style)
            self.status_label.setStyleSheet(f"{font_style} color: #666;")
            
            # 更新按钮字体
            for i in range(self.button_layout.count()):
                widget = self.button_layout.itemAt(i).widget() # pyright: ignore[reportOptionalMemberAccess]
                if isinstance(widget, QPushButton):
                    widget.setStyleSheet(font_style)
                    
            # 更新分组框标题字体
            self.drop_group.setStyleSheet(f"QGroupBox {{ {font_style} font-weight: bold; }}")
            self.file_group.setStyleSheet(f"QGroupBox {{ {font_style} font-weight: bold; }}")
        
        def change_font_size(self, size):
            self.font_size = size
            self.update_styles()
                
        def dragEnterEvent(self, event: QDragEnterEvent): # pyright: ignore[reportIncompatibleMethodOverride]
            if event.mimeData().hasUrls(): # pyright: ignore[reportOptionalMemberAccess]
                event.acceptProposedAction()
                
        def dropEvent(self, event: QDropEvent): # pyright: ignore[reportIncompatibleMethodOverride]
            urls = event.mimeData().urls() # pyright: ignore[reportOptionalMemberAccess]
            if urls:
                self.process_urls(urls)
                
        def process_urls(self, urls):
            if t in{4,21,18}: 
                self.file_list.clear()        
            for url in urls:
                path = url.toLocalFile()
                
                if os.path.isdir(path):
                    self.process_folder(path)
                elif os.path.isfile(path):
                    self.add_file_to_list(path)
            # self.drop_label.setText("拖放文件或文件夹到此处\n可以拖入父文件夹，我们会自动递归遍历")
                
        def process_folder(self, folder_path):
            try:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self.add_file_to_list(file_path)
            except Exception as e:
                self.add_error_item(f"错误处理文件夹 {folder_path}: {str(e)}")
                
        def add_file_to_list(self, file_path):
            if not is_hidden_file(file_path):
                item = QListWidgetItem(file_path)
                self.file_list.addItem(item)
                self.q.append(file_path)
                #只要处理正常的，否则，q和file_list可以合并。
            # else:
            #     self.add_error_item(f"已忽略隐藏文件 ：{file_path}")  
        def add_error_item(self, error_msg):
            item = QListWidgetItem(error_msg)
            item.setForeground(Qt.GlobalColor.red)
            self.file_list.addItem(item)
                
        def browse_files(self):
            file_paths, _ = QFileDialog.getOpenFileNames(self, "选择文件")
            
            if file_paths:
                urls = [QUrl.fromLocalFile(path) for path in file_paths]
                self.process_urls(urls)
                
        def browse_folder(self):
            folder_path = QFileDialog.getExistingDirectory(
                self, "选择文件夹", "", QFileDialog.Option.ShowDirsOnly
            )
            
            if folder_path:
                self.process_urls([QUrl.fromLocalFile(folder_path)])
                
        def clear_list(self):
            self.file_list.clear()
            # self.status_label.setText("就绪")#可以改成其他的。
            # self.drop_label.setText("拖放文件或文件夹到此处\n可以拖入父文件夹，我们会自动递归遍历")
            self.q.clear()
        
        def sure(self):
            gb["c1"] = self.q
            self.window().close()  # pyright: ignore[reportOptionalMemberAccess]
            if t in {4,18,21}:
                self.again_window = againWindow()
                self.again_window.setWindowTitle(rw[t-1])  
                qt_material.apply_stylesheet(self.again_window, theme='dark_teal.xml')                             
                self.again_window.show()
            elif t in {2,3,5,11,13,14,19}:
                pass
            else:
                #听说传数字比字符串效率高一些。
                self.second_window = SecondWindow()
                self.second_window.setWindowTitle(rw[t-1])

                # qt_material.apply_stylesheet(self.second_window, theme='dark_teal.xml')
                # 不用风格不统一，用了改我字号(，一个办法是运行时在属性--->兼容--->DPI--->使用系统替代 


                self.second_window.show()

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
            self.initUI()
            
        def initUI(self):
            self.setWindowTitle(rw[t-1])
                    # 获取主屏幕尺寸
            screen =QApplication.primaryScreen()
            screen_geometry = screen.geometry()   # type: ignore
            screen_width,screen_height=screen_geometry.width(),screen_geometry.height() # pyright: ignore[reportIndexIssue]
            self.resize(int(screen_width * 0.3), int(screen_height * 0.75))  # 明确设置宽高
            self.move(10, 10)  # 可选：设置初始位置
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)    
            self.central_widget = FileFolderListWidget()
            self.setCentralWidget(self.central_widget)

    class FFLWidget(QWidget):#二次拖放
        def __init__(self):
            super().__init__()
            self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
            self.font_size = 17  # 默认字体大小
            self.initUI()
            self.w=''
        def initUI(self):
            # 创建主布局
            main_layout = QVBoxLayout()
            
            # 创建字体大小调整滑块
            font_layout = QHBoxLayout()
            font_label = QLabel("字体大小:")
            self.font_slider = QSlider(Qt.Orientation.Horizontal)
            self.font_slider.setMinimum(8)
            self.font_slider.setMaximum(24)
            self.font_slider.setValue(self.font_size)
            self.font_slider.setTickInterval(2)
            self.font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.font_slider.valueChanged.connect(lambda x: self.change_font_size(x))
            
            font_layout.addWidget(font_label)
            font_layout.addWidget(self.font_slider)
            main_layout.addLayout(font_layout)
            
            # 创建拖放区域
            self.drop_group = QGroupBox("拖放区域")
            drop_layout = QVBoxLayout()
            if t ==4:
                self.drop_label = QLabel("拖放pdf到此处")
            elif t==21:
                self.drop_label = QLabel("拖放视频到此处")
            else:
                self.drop_label = QLabel("拖放水印图片到此处")

            self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drop_label.setMinimumHeight(100)
            
            drop_layout.addWidget(self.drop_label)
            self.drop_group.setLayout(drop_layout)
            
            # 创建文件列表区域
            self.file_group = QGroupBox("文件列表")
            file_layout = QVBoxLayout()
            
            # 使用QListWidget并设置字体大小
            self.file_list = QListWidget()
            self.file_list.setAlternatingRowColors(True)
            
        # 状态栏
            if 4==t:
                self.status_label = QLabel("添加pdf文件")
            elif t==21:
                self.status_label = QLabel("添加视频")
            else:
                self.status_label = QLabel("添加图片")
                       
            file_layout.addWidget(self.file_list)
            file_layout.addWidget(self.status_label)
            self.file_group.setLayout(file_layout)
            
            # 创建按钮区域
            self.button_layout = QHBoxLayout()
              
            self.browse_files_button = QPushButton("选择文件")
            self.browse_files_button.clicked.connect(lambda: self.browse_files())
            
            self.clear_button = QPushButton("清空列表")
            self.clear_button.clicked.connect(lambda: self.clear_list())

            self.close_button = QPushButton("确认")
            self.close_button.clicked.connect(lambda: self.sure()) # pyright: ignore[reportOptionalMemberAccess]
            
            self.button_layout.addWidget(self.browse_files_button)
            self.button_layout.addWidget(self.clear_button)
            self.button_layout.addWidget(self.close_button)
            
            # 添加所有组件到主布局
            main_layout.addWidget(self.drop_group)
            main_layout.addWidget(self.file_group)
            main_layout.addLayout(self.button_layout)
            
            # 设置布局
            self.setLayout(main_layout)
            
            # 启用拖放
            self.setAcceptDrops(True)
            
            # 初始化样式（确保所有控件都已创建后再调用）
            self.update_styles()
        
        #这个如果能全局使用就可以使用qtmaterial了。
        def update_styles(self):
            # 更新所有控件的字体大小
            font_style = f"font-size: {self.font_size}px;"
            
            self.drop_label.setStyleSheet(f"{font_style} border: 2px dashed #aaa; padding: 20px;")
            self.file_list.setStyleSheet(font_style)
            self.status_label.setStyleSheet(f"{font_style} color: #666;")
            
            # 更新按钮字体
            for i in range(self.button_layout.count()):
                widget = self.button_layout.itemAt(i).widget() # pyright: ignore[reportOptionalMemberAccess]
                if isinstance(widget, QPushButton):
                    widget.setStyleSheet(font_style)
                    
            # 更新分组框标题字体
            self.drop_group.setStyleSheet(f"QGroupBox {{ {font_style} font-weight: bold; }}")
            self.file_group.setStyleSheet(f"QGroupBox {{ {font_style} font-weight: bold; }}")
        
        def change_font_size(self, size):
            self.font_size = size
            self.update_styles()
                
        def dragEnterEvent(self, event: QDragEnterEvent): # pyright: ignore[reportIncompatibleMethodOverride]
            if event.mimeData().hasUrls(): # pyright: ignore[reportOptionalMemberAccess]
                event.acceptProposedAction()
                
        def dropEvent(self, event: QDropEvent): # pyright: ignore[reportIncompatibleMethodOverride]
            urls = event.mimeData().urls() # pyright: ignore[reportOptionalMemberAccess]
            if urls:
                self.process_urls(urls)
                
        def process_urls(self, urls):
            self.file_list.clear()        
            for url in urls:
                path = url.toLocalFile()
                
                if os.path.isdir(path):
                    self.process_folder(path)
                elif os.path.isfile(path):
                    self.add_file_to_list(path)
            # self.drop_label.setText("拖放文件或文件夹到此处\n可以拖入父文件夹，我们会自动递归遍历")
                
        def process_folder(self, folder_path):
            try:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self.add_file_to_list(file_path)
            except Exception as e:
                self.add_error_item(f"错误处理文件夹 {folder_path}: {str(e)}")
                
        def add_file_to_list(self, file_path):
            if not is_hidden_file(file_path):
                item = QListWidgetItem(file_path)
                self.file_list.addItem(item)
                self.w=file_path
            # else:
            #     self.add_error_item(f"已忽略隐藏文件 ：{file_path}")
                
        def add_error_item(self, error_msg):
            item = QListWidgetItem(error_msg)
            item.setForeground(Qt.GlobalColor.red)
            self.file_list.addItem(item)
                
        def browse_files(self):
            file_paths, _ = QFileDialog.getOpenFileNames(self, "选择文件")
            
            if file_paths:
                urls = [QUrl.fromLocalFile(path) for path in file_paths]
                self.process_urls(urls)
                
        def browse_folder(self):
            folder_path = QFileDialog.getExistingDirectory(
                self, "选择文件夹", "", QFileDialog.Option.ShowDirsOnly
            )
            
            if folder_path:
                self.process_urls([QUrl.fromLocalFile(folder_path)])
                
        def clear_list(self):
            self.file_list.clear()
            # self.status_label.setText("就绪")#可以改成其他的。
            # self.drop_label.setText("拖放文件或文件夹到此处\n可以拖入父文件夹，我们会自动递归遍历")
            self.w=''
        
        def sure(self):
            gb["c2"] = self.w 
            self.window().close() # pyright: ignore[reportOptionalMemberAccess]
            if t!=21:
                self.second_window = SecondWindow()
                self.second_window.setWindowTitle(rw[t-1])

                # qt_material.apply_stylesheet(self.second_window, theme='dark_teal.xml')
                # 不用风格不统一，用了改我字号(，一个办法是运行时在属性--->兼容--->DPI--->使用系统替代            
                self.second_window.show()


    class SecondWindow(QMainWindow): #各种控件UI(用qtdesigner制作)
        def __init__(self):
            super().__init__()
            self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
            self.ck0=None
            self.ck1=None
            self.ck2=None
            self.ck3=None
            self.init_ui()
        def init_ui(self):
            # # 获取主屏幕尺寸
            # screen =QApplication.primaryScreen()
            # screen_geometry = screen.geometry()   # type: ignore
            # screen_width,screen_height=screen_geometry.width(),screen_geometry.height() # pyright: ignore[reportIndexIssue]
            # # self.resize(int(screen_width * 0.1), int(screen_height * 0.1))  # 明确设置宽高
            # # self.setFixedSize(self.size())
            self.move(50, 30)  # 可选：设置初始位置 
            if t ==1:
                from Ui_mode import Ui_MainWindow
                # 初始化UI
                self.ui = Ui_MainWindow()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                self.ui.pushButton.clicked.connect(lambda: self.sure())#"确认"))
            elif t ==4:
                from Ui_markrotatetrainkle import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==6:
                from Ui_piform import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==8:
                from Ui_frontbebind import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
    
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==9:
                from Ui_zim import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==10:
                from Ui_cutpi import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==12:
                from Ui_key import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==15:
                from Ui_tiaoz import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==16:
                from Ui_cutvdo import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==17:
                from Ui_gif import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==18:
                from Ui_viwtmk import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==20:
                from Ui_fps import Ui_Form
                # 初始化UI
                self.ui = Ui_Form()
                self.ui.setupUi(self)  # 将UI绑定到当前窗口
                
                self.ui.pushButton.clicked.connect(lambda: self.sure())
            elif t ==7:
                self.dynamic_form = DynamicInputForm()
                self.dynamic_form.sure_button.clicked.connect(lambda: self.handle_dynamic_data())
                self.dynamic_form.move(30,30)
                self.dynamic_form.show()


        def sure(self):
            if t==1:
                if self.ui.radioButton.isChecked():# pyright: ignore[reportAttributeAccessIssue] #"大模型"))
                        self.ck0='medium.pt'       #如果放在init_ui，存的就是初始/缺省/默认值。
                else:
                    self.ck0='small.pt'
            elif t==4:
                self.ck0=self.ui.horizontalSlider.value() # pyright: ignore[reportAttributeAccessIssue]
            elif t==6:
                s=self.ui.buttonGroup.checkedButton() # pyright: ignore[reportAttributeAccessIssue]
                if s:
                    self.ck0=s.text()
            elif t==8:
                self.ck0=self.ui.lineEdit.text() # pyright: ignore[reportAttributeAccessIssue]
                self.ck1=self.ui.lineEdit_2.text() # pyright: ignore[reportAttributeAccessIssue]
            elif t==9:
                self.ck0=self.ui.plainTextEdit.toPlainText() # pyright: ignore[reportAttributeAccessIssue]
            elif t==10:
                self.ck0=self.ui.spinBox.value() # pyright: ignore[reportAttributeAccessIssue]
                self.ck1=self.ui.spinBox_2.value() # pyright: ignore[reportAttributeAccessIssue]
                s=self.ui.buttonGroup.checkedButton() # pyright: ignore[reportAttributeAccessIssue]
                d={'右下':'rd','左下':'ru','右上':'ld','左上':'rd'}
                #裁剪域--->保留域left,right,up,down。
                if s:
                    self.ck2=d[s.text()]
            elif t==12:
                self.ck0=self.ui.lineEdit.text() # pyright: ignore[reportAttributeAccessIssue]
                if self.ui.radioButton.isChecked():# pyright: ignore[reportAttributeAccessIssue] #"加密"))
                    self.ck1='e'
            elif t==15:
                self.ck0=self.ui.spinBox.value() # pyright: ignore[reportAttributeAccessIssue]
                self.ck1=self.ui.spinBox_2.value() # pyright: ignore[reportAttributeAccessIssue]
            elif t==16:
                self.ck0=self.ui.spinBox.value() # pyright: ignore[reportAttributeAccessIssue]
                self.ck1=self.ui.spinBox_2.value() # pyright: ignore[reportAttributeAccessIssue]
                self.ck2=self.ui.spinBox_3.value() # pyright: ignore[reportAttributeAccessIssue]
                self.ck3=self.ui.spinBox_4.value() # pyright: ignore[reportAttributeAccessIssue]
            elif t==17:
                self.ck0=self.ui.spinBox.value() # pyright: ignore[reportAttributeAccessIssue]
                self.ck1=self.ui.spinBox_2.value() # pyright: ignore[reportAttributeAccessIssue]
            elif t==18:
                s=self.ui.buttonGroup.checkedButton() # pyright: ignore[reportAttributeAccessIssue]
                d={'右下':'bottom-right','左下':'bottom-left','右上':'top-right','左上':'top-left'}
                #裁剪域--->保留域left,right,up,down。
                if s:
                    self.ck0=d[s.text()]
                self.ck1=self.ui.horizontalSlider.value() # pyright: ignore[reportAttributeAccessIssue]
            elif t==20:
                self.ck0=self.ui.spinBox.value() # pyright: ignore[reportAttributeAccessIssue]
                if self.ui.radioButton_2.isChecked(): # pyright: ignore[reportAttributeAccessIssue]
                    self.ck1='cpu'
                else:
                    self.ck1='gpu'
                if self.ui.radioButton_3.isChecked(): # pyright: ignore[reportAttributeAccessIssue]
                    self.ck2='e'
                else:
                    self.ck2='h'
            elif t==7:
                if self.ui.radioButton.isChecked(): # pyright: ignore[reportAttributeAccessIssue]
                    self.ck1=True
                self.ck2=(self.ui.dial.value(),self.ui.dial_2.value()) # pyright: ignore[reportAttributeAccessIssue]
                self.ck3=self.ui.comboBox.currentText() # pyright: ignore[reportAttributeAccessIssue]
                dd= {"rectangle（长方形）":'rectangle',"cardioid（心形）":'cardioid',"pentagon（五边形 ）":'pentagon'}
                if self.ck3 in dd:
                    self.ck3=dd[self.ck3]

            gb["c3"] =[self.ck0,self.ck1,self.ck2,self.ck3]
            self.close()    

            #窗口类直接.close，组件类要.window().close()获取所在窗口再关闭。
        
        def handle_dynamic_data(self):
                    """处理从DynamicInputForm接收的数据"""
                    result = {}
                    for _, group in enumerate(self.dynamic_form.input_groups, 1):
                        # 获取输入的字词
                        word = group['line_edit'].text().strip()
                        # 获取选择的频数
                        frequency = group['spin_box'].value()
                        if word:
                            result[word] = frequency
                    self.ck0=result
                    self.dynamic_form.close()
                    from Ui_wd import Ui_Form
                    # 初始化UI
                    self.ui = Ui_Form()
                    self.ui.setupUi(self)  # 将UI绑定到当前窗口
                    
                    self.ui.pushButton.clicked.connect(lambda: self.sure())
                    self.show()

    class againWindow(QMainWindow):#二次拖入文件使用
        def __init__(self):
            super().__init__()
            self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
            self.initUI()
            
        def initUI(self):
            self.setWindowTitle(rw[t-1])
                    # 获取主屏幕尺寸
            screen =QApplication.primaryScreen()
            screen_geometry = screen.geometry()   # type: ignore
            screen_width,screen_height=screen_geometry.width(),screen_geometry.height() # pyright: ignore[reportIndexIssue]
            self.resize(int(screen_width * 0.3), int(screen_height * 0.75))  # 明确设置宽高
            self.move(20, 20)  # 可选：设置初始位置
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)    
            self.central_widget = FFLWidget()
            self.setCentralWidget(self.central_widget)
                
    class DynamicInputForm(QWidget):   #word cloud专用
        def __init__(self):
            super().__init__()
            self.setWindowIcon(QIcon(get_path("pictures\\icn.ico")))
            self.input_groups = []
            self.initUI()
        def initUI(self):
            self.setWindowTitle('词云生成')
            self.resize(520, 261)
            # 创建主布局
            main_layout = QVBoxLayout(self)

            # 创建滚动区域
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)  # 使内部部件可调整大小
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 禁用水平滚动条
            
            # 创建一个容器来容纳所有输入组
            self.container = QWidget()
            self.input_layout = QVBoxLayout(self.container)

            
            # 添加初始的一组输入
            self.add_input_group()
            
            # 将容器设置为滚动区域的部件
            self.scroll_area.setWidget(self.container)
            
            # 创建添加按钮
            self.add_button = QPushButton("+ 添加一组")
            font = QFont("SimHei", 14)  # 字体为"黑体"
            font.setBold(True)  # 加粗
            self.add_button.setFont(font)
            self.add_button.clicked.connect(lambda: self.add_input_group())

            # 创建添加按钮
            self.sure_button = QPushButton("确认")
            font = QFont("SimHei", 14)  # 字体为"黑体"
            font.setBold(True)  # 加粗
            self.sure_button.setFont(font)
            
            # 将滚动区域和按钮添加到主布局
            main_layout.addWidget(self.scroll_area)
            main_layout.addWidget(self.add_button)
            main_layout.addWidget(self.sure_button)
            
            self.setLayout(main_layout)
            
        def add_input_group(self):
            """添加一组输入框和数量选择器"""
            # 创建水平布局来放置输入框和数量选择器
            group_layout = QHBoxLayout()
            
            # 创建输入框
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("左边填要显示的字词，右边选出现频数。")
            line_edit.setMinimumWidth(300)
            font = QFont("SimHei", 13)  # 字体为"黑体"
            font.setBold(True)  # 加粗
            line_edit.setFont(font)
            # 创建数量选择器
            spin_box = QSpinBox()
            spin_box.setRange(1, 100)  # 设置数值范围
            spin_box.setValue(1)  # 默认值
            spin_box.setMinimumWidth(100)
            font = QFont("SimHei", 14)  # 字体为"黑体
            font.setBold(True)  # 加粗
            spin_box.setFont(font)
            
            # 添加到水平布局
            group_layout.addWidget(line_edit)
            group_layout.addWidget(spin_box)
            
            # 创建一个框架来包含这组控件，使界面更美观
            frame = QFrame()
            # frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setLayout(group_layout)
            
            # 添加到容器布局
            self.input_layout.addWidget(frame)
            self.input_groups.append({
            'line_edit': line_edit,
            'spin_box': spin_box
        })#每加一组引用一次。


    app = QApplication(sys.argv)
    # app.setStyle('Windows')
    if t==7:
        window = SecondWindow()
        #7在second_window内部有show，因为要调用不同的class【DynamicInputForm(QWidget)】。
        #为什么要调用，是因为我用qtdesigner无法创建那样的UI
        #都放在second_window是因为都是控件输入类的。
    else:
        window = MainWindow()
        qt_material.apply_stylesheet(window, theme='dark_teal.xml')  
        window.show()
    app.exec()
global gb       
gb={}           #它可以传到child_window（）和多进程函数里面去，但多进程函数不能全局修改它。
                #如果不这么写，每个多进程函数里带一个gb={}，child_window(t)出来后会发现
                #gb还是空的。说明child_window（）的外部是本体而不是调用之处的外部。
              
#-----------------多进程执行：--------------->
def getvoice(t):
    # gb= {}           #参数汇总
    child_window(t)
    # print(gb)
    import ffmpeeg
    for i in gb['c1']:
        ffmpeeg.ffmpg(9,i,gb["c3"][0])
    # print('如果有报错信息_pickle.UnpicklingError，请往上翻看看有没有正确结果。')
    sys.exit()#应用窗口关闭后还要调用执行函数，故exit要放最后，上面只留个app.exec()
def addx(t):            
    child_window(t)
    # print(gb)
    import doc_to_docx
    doc_to_docx.begin(gb["c1"])
    sys.exit()
def pi_to_pd(t):
    child_window(t)
    # print(gb)
    import jpg_to_pdf
    jpg_to_pdf.pg(gb["c1"])
    sys.exit()
def mark(t):
    # print('作者设置了权限的情况下可能无法执行操作')
    child_window(t)
    # print(gb)
    from pdf import addimg
    for i in gb['c1']:
        addimg(i,gb["c2"],gb["c3"][0])  
        #c2-->str;   c1,c3-->list
    sys.exit()
def pdgetword(t):
    child_window(t)
    # print(gb)
    from pdf import gettext
    for i in gb['c1']:
        gettext(i)
    # print('已完成')
    sys.exit()
def pi_to_pi(t):
    # print('把.png图片转为.jpg图片可在图片没有透明部分情况下不造成观感上的明显损失而显著减少储存占用。')
    child_window(t)
    # print(gb)
    from png_to_jpg import begin
    for i in gb['c1']:
        begin(i,gb['c3'][0])
    # print('已完成')
    sys.exit()
def wc(t):
    # print('手轮转到右下方为最大值。')
    child_window(t)
    # print(gb)
    from cy import c
    c(gb['c3'][0],gb['c3'][1],gb['c3'][2],gb['c3'][3])
    sys.exit()
def od(t):
    child_window(t)
    # print(gb)
    from pxmm import begin
    begin(gb['c1'],gb['c3'][0],gb['c3'][1])
    sys.exit()
def cover(t):
    child_window(t)
    # print(gb)
    from spzm1 import main
    for i in gb['c1']:
        main(i,gb['c3'][0])
    sys.exit()
def rate(t):
    child_window(t)
    # print(gb)
    from tpbl import image_clip
    for i in gb['c1']:
        image_clip(i,gb['c3'][0],gb['c3'][1],gb['c3'][2])
    sys.exit()
def pigetword(t):
    child_window(t)
    # print(gb)
    dm=import_data_module('demo3','OCR\\PaddleOCR-json-main\\demo3.pyd')
    for i in gb['c1']:
        dm.begin(i)
    sys.exit()
def aes(t):
    child_window(t)
    # print(gb)
    import aes256split as dm
    for i in gb['c1']:
        dm.begin(i,gb['c3'][0],gb['c3'][1])
    sys.exit()

def press(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(0,i)
    sys.exit()
def grapevoice(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(1,i)
    sys.exit()
def pullruler(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(2,i,gb['c3'][0],gb['c3'][1])
    sys.exit()
def cut(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(3,i,gb['c3'][0],gb['c3'][1],gb['c3'][2],gb['c3'][3])
    sys.exit()
def ve_to_gi(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(4,i,gb['c3'][0],gb['c3'][1])
    sys.exit()
def draw(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(5,i,gb['c2'],gb['c3'][0],gb['c3'][1])
    sys.exit()
def hear(t): 
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(6,i)
    sys.exit()
def shake(t):
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(7,i,gb['c3'][0],gb['c3'][1],gb['c3'][2])
    sys.exit()
def together(t): 
    child_window(t)
    # print(gb)
    from ffmpeeg import ffmpg
    for i in gb['c1']:
        ffmpg(8,i,gb['c2'][0])
    sys.exit()



    

