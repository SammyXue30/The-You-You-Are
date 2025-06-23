"""
UI: 400×640 竖屏
• 角色标签彩色粗体
• 正文字幕粗体
• 倒计时红色粗体
• clear_subtitles() 供主程序复位
"""
import tkinter as tk, queue, random
POLL_MS = 50
ROLE_COLORS = {
    "YOU": "#56C1FF",
    "BRANCH_#C-137_ONLINE": "#61D836",
}
BASE_FONT = ("Menlo", 12, "bold")
ROLE_FONT = ("Menlo", 14, "bold")
class SubtitleWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("the UUR")
        self.root.geometry("400x640")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        # ── 顶部提示 ──
        self.prompt = tk.Label(self.root, font=("Menlo", 14),
                               wraplength=380, justify="center")
        self.prompt.pack(pady=(6, 0))
        # ── 倒计时（红、粗体）──
        self.counter = tk.Label(self.root, font=("Menlo", 22, "bold"),
                                fg="#CC0000")
        self.counter.pack()
        # ── 字幕区 ──
        self.text = tk.Text(self.root, width=40, height=18,
                            font=BASE_FONT, wrap="word",
                            fg="#000000", state="disabled")
        self.scroll = tk.Scrollbar(self.root, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        # tk.Button(self.root, text="Quit", command=self.root.quit
        #           ).pack(anchor="ne", padx=4, pady=4)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        # 预注册颜色
        for tag, color in ROLE_COLORS.items():
            self.text.tag_config(tag, foreground=color, font=ROLE_FONT)
        self.q: "queue.Queue[tuple[str,str]]" = queue.Queue()
        self.root.after(POLL_MS, self._poll_queue)
    # ---------- 公共 ----------
    def set_prompt(self, txt: str):
        self.prompt.config(text=txt)
        self.root.update_idletasks()
    def start_countdown(self, sec: int, template=" {} s"):
        self._count(sec, template)
    def enter_subtitles(self):
        if not self.text.winfo_ismapped():
            self.text.pack(side="left", fill="both", expand=True,
                           padx=(4, 0), pady=4)
            self.scroll.pack(side="right", fill="y", pady=4)
    def add(self, role: str, msg: str):
        """线程安全：后台线程只 put 消息"""
        self.q.put((role, msg))
    def clear_subtitles(self):
        """隐藏字幕区并清空内容"""
        self.text.pack_forget()
        self.scroll.pack_forget()
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
    # ---------- 私有 ----------
    @staticmethod
    def _rand():
        return "#" + "".join(random.choice("89ABCDEF") for _ in range(6))
    def _count(self, sec, template):
        self.counter.config(text=template.format(sec) if sec >= 0 else "")
        if sec >= 0:
            self.root.after(1000, self._count, sec - 1, template)
    def _poll_queue(self):
        try:
            while True:
                role, msg = self.q.get_nowait()
                tag = role.replace(" ", "_")
                if tag not in self.text.tag_names():
                    self.text.tag_config(tag,
                                         foreground=ROLE_COLORS.get(tag, self._rand()),
                                         font=ROLE_FONT)
                self.text.configure(state="normal")
                self.text.insert("end", f"[{role}] ", tag)
                self.text.insert("end", f"{msg}\n")
                self.text.see("end")
                self.text.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(POLL_MS, self._poll_queue)
    def start(self):
        self.root.mainloop()



