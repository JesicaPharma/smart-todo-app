from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import json
import os
from datetime import datetime

# 适配小米手机/电脑屏幕
Window.clearcolor = (0.95, 0.95, 0.95, 1)

DATA_FILE = 'tasks.json'

# --- 数据管理逻辑 (保持不变) ---
class TaskManager:
    def __init__(self):
        self.tasks = self.load_tasks()

    def load_tasks(self):
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_tasks(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def calculate_score(self, task):
        urgency_map = {'🔥 非常急': 30, '⚡️ 有点急': 20, '🐢 不急': 5}
        importance_map = {'💎 非常重要': 30, '👍 重要': 20, '💭 一般': 5}
        score = urgency_map.get(task.get('urgency'), 5) + importance_map.get(task.get('importance'), 5)
        
        try:
            created_date = datetime.strptime(task.get('created_at', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
            days_old = (datetime.now() - created_date).days
            if task['status'] == 'pending':
                score += max(0, (days_old - 2)) * 5
        except:
            pass
        return score

    def get_suggestion(self):
        pending_daily = [t for t in self.tasks if t['pool'] == 'daily' and t['status'] == 'pending']
        if not pending_daily:
            return "🎉 今日任务已完成！"
        sorted_tasks = sorted(pending_daily, key=self.calculate_score, reverse=True)
        top = sorted_tasks[0]
        return f"💡 建议优先做：{top['content']} ({top['urgency']})"

    def add_task(self, content, pool, urgency, importance):
        new_task = {
            "id": datetime.now().timestamp(),
            "content": content,
            "pool": pool,
            "urgency": urgency,
            "importance": importance,
            "status": "pending",
            "created_at": datetime.now().strftime('%Y-%m-%d')
        }
        self.tasks.append(new_task)
        self.save_tasks()

    def complete_task(self, task_id):
        for t in self.tasks:
            if t['id'] == task_id:
                t['status'] = 'completed'
                break
        self.save_tasks()

    def postpone_task(self, task_id):
        for t in self.tasks:
            if t['id'] == task_id:
                t['pool'] = 'master'
                t['status'] = 'pending'
                break
        self.save_tasks()

    def move_to_daily(self, task_id):
        for t in self.tasks:
            if t['id'] == task_id:
                t['pool'] = 'daily'
                break
        self.save_tasks()

tm = TaskManager()

# --- 界面逻辑 (已修复 id 问题) ---

class DailyScreen(Screen):
    def __init__(self, **kwargs):
        super(DailyScreen, self).__init__(**kwargs)
        # 初始化组件引用
        self.suggestion_label = None
        self.tasks_layout = None
        self._build_ui()

    def _build_ui(self):
        # 构建今日页面的 UI
        main_layout = BoxLayout(orientation='vertical')
        
        # 标题
        main_layout.add_widget(Label(text="📅 今日计划", size_hint_y=None, height=50, bold=True, font_size='18sp'))
        
        # 智能建议标签 (保存引用)
        self.suggestion_label = Label(text="", size_hint_y=None, height=40, color=(0.2, 0.2, 0.8, 1), font_size='14sp')
        main_layout.add_widget(self.suggestion_label)
        
        # 任务列表滚动区
        scroll = ScrollView()
        self.tasks_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll.add_widget(self.tasks_layout)
        main_layout.add_widget(scroll)
        
        # 按钮区域
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        btn_add = Button(text="➕ 新增任务")
        btn_add.bind(on_press=lambda x: setattr(self.manager, 'current', 'add'))
        
        btn_master = Button(text="📦 查看总池")
        btn_master.bind(on_press=lambda x: setattr(self.manager, 'current', 'master'))
        
        btn_layout.add_widget(btn_add)
        btn_layout.add_widget(btn_master)
        main_layout.add_widget(btn_layout)
        
        self.add_widget(main_layout)

    def on_enter(self):
        self.refresh_ui()

    def refresh_ui(self):
        if not self.suggestion_label or not self.tasks_layout:
            return
            
        # 更新建议
        self.suggestion_label.text = tm.get_suggestion()
        
        # 清空列表
        self.tasks_layout.clear_widgets()
        
        pending = [t for t in tm.tasks if t['pool'] == 'daily' and t['status'] == 'pending']
        pending.sort(key=tm.calculate_score, reverse=True)
        
        if not pending:
            lbl = Label(text="✅ 所有任务已完成！", size_hint_y=None, height=50, color=(0, 0.5, 0, 1), font_size='16sp')
            self.tasks_layout.add_widget(lbl)
            return

        for task in pending:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, padding=5)
            
            # 任务内容
            text_content = f"{task['content']}\n[font_size=12]{task['urgency']} | {task['importance']}[/font_size]"
            lbl = Label(text=text_content, markup=True, halign='left', valign='middle', size_hint_x=0.7)
            lbl.bind(size=lbl.setter(text_size))
            
            # 完成按钮
            btn_done = Button(text="✅", size_hint_x=0.15)
            # 使用默认参数避免闭包问题
            btn_done.bind(on_press=lambda instance, tid=task['id']: self.on_done(tid))
            
            # 推迟按钮
            btn_delay = Button(text="⏰", size_hint_x=0.15)
            btn_delay.bind(on_press=lambda instance, tid=task['id']: self.on_delay(tid))
            
            box.add_widget(lbl)
            box.add_widget(btn_done)
            box.add_widget(btn_delay)
            self.tasks_layout.add_widget(box)

    def on_done(self, tid):
        tm.complete_task(tid)
        self.refresh_ui()
    
    def on_delay(self, tid):
        tm.postpone_task(tid)
        self.refresh_ui()

class AddScreen(Screen):
    def __init__(self, **kwargs):
        super(AddScreen, self).__init__(**kwargs)
        self.content_input = None
        self.result_label = None
        self.pool_spinner = None
        self.urgency_spinner = None
        self.imp_spinner = None
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="➕ 新增任务", size_hint_y=None, height=50, font_size='18sp'))
        
        self.content_input = TextInput(hint_text='输入任务内容...', multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.content_input)
        
        # 选择器
        self.pool_spinner = Spinner(text="📅 今日计划池", values=("📅 今日计划池", "📦 总任务池"), size_hint_y=None, height=50)
        layout.add_widget(self.pool_spinner)
        
        self.urgency_spinner = Spinner(text="⚡️ 有点急", values=("🔥 非常急", "⚡️ 有点急", "🐢 不急"), size_hint_y=None, height=50)
        layout.add_widget(self.urgency_spinner)
        
        self.imp_spinner = Spinner(text="👍 重要", values=("💎 非常重要", "👍 重要", "💭 一般"), size_hint_y=None, height=50)
        layout.add_widget(self.imp_spinner)
        
        btn_submit = Button(text="保存", size_hint_y=None, height=50)
        btn_submit.bind(on_press=lambda x: self.add_task_action())
        layout.add_widget(btn_submit)
        
        self.result_label = Label(text="", size_hint_y=None, height=30, color=(1, 0, 0, 1))
        layout.add_widget(self.result_label)
        
        btn_back = Button(text="返回", size_hint_y=None, height=50)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'daily'))
        layout.add_widget(btn_back)
        
        self.add_widget(layout)

    def on_enter(self):
        if self.content_input:
            self.content_input.text = ""
        if self.result_label:
            self.result_label.text = ""

    def add_task_action(self):
        if not self.content_input: return
        content = self.content_input.text
        pool = self.pool_spinner.text if self.pool_spinner else "📦 总任务池"
        urgency = self.urgency_spinner.text if self.urgency_spinner else "🐢 不急"
        importance = self.imp_spinner.text if self.imp_spinner else "💭 一般"
        
        if content:
            pool_key = 'daily' if '今日' in pool else 'master'
            tm.add_task(content, pool_key, urgency, importance)
            self.content_input.text = ""
            if self.result_label:
                self.result_label.text = "✅ 添加成功!"
                self.result_label.color = (0, 0.5, 0, 1)
        else:
            if self.result_label:
                self.result_label.text = "❌ 请输入内容"
                self.result_label.color = (1, 0, 0, 1)

class MasterScreen(Screen):
    def __init__(self, **kwargs):
        super(MasterScreen, self).__init__(**kwargs)
        self.master_layout = None
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="📦 总任务仓库", size_hint_y=None, height=50, font_size='18sp'))
        
        scroll = ScrollView()
        self.master_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll.add_widget(self.master_layout)
        layout.add_widget(scroll)
        
        btn_back = Button(text="返回", size_hint_y=None, height=50)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'daily'))
        layout.add_widget(btn_back)
        
        self.add_widget(layout)

    def on_enter(self):
        self.refresh_ui()
    
    def refresh_ui(self):
        if not self.master_layout: return
        self.master_layout.clear_widgets()
        master_tasks = [t for t in tm.tasks if t['pool'] == 'master' and t['status'] == 'pending']
        
        if not master_tasks:
            self.master_layout.add_widget(Label(text="总池为空", halign='center'))
            return
            
        for task in master_tasks:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=5)
            lbl = Label(text=task['content'], halign='left', valign='middle')
            lbl.bind(size=lbl.setter(text_size))
            
            btn_move = Button(text="📅 移入今日", size_hint_x=0.3)
            btn_move.bind(on_press=lambda instance, tid=task['id']: self.on_move(tid))
            
            box.add_widget(lbl)
            box.add_widget(btn_move)
            self.master_layout.add_widget(box)
            
    def on_move(self, tid):
        tm.move_to_daily(tid)
        self.refresh_ui()
        # 提示用户去今日页看
        self.manager.current = 'daily'

class SmartTodoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DailyScreen(name='daily'))
        sm.add_widget(AddScreen(name='add'))
        sm.add_widget(MasterScreen(name='master'))
        return sm

if __name__ == '__main__':
    SmartTodoApp().run()