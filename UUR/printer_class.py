import os
import glob
import subprocess
from typing import List

class ThermoPrinter:
    """
    Windows 用热敏打印包装
    参数
    ----
    port : 打印机端口字符串
    cpp_bin_path : 存放 *.exe 的文件夹；可含子目录
    """
    def __init__(self, port: str, cpp_bin_path: str = "./cpp_bin"):
        self.port = port
        self.cpp_bin_path = os.path.abspath(cpp_bin_path)
    # ---------- 工具 ----------
    def _exe(self, name: str) -> str:
        "默认路径：<cpp_bin_path>/<name>.exe"
        return os.path.join(self.cpp_bin_path, f"{name}.exe")
    def _search_exe(self, name: str) -> str | None:
        "递归两级搜索 name*.exe（忽略大小写）"
        pattern = os.path.join(self.cpp_bin_path, "**", f"{name}*.exe")
        matches = glob.glob(pattern, recursive=True)
        return matches[0] if matches else None
    def _run(self, args: List[str]) -> None:
        exe_path = args[0]
        # 如果缺失就递归找
        if not os.path.isfile(exe_path):
            alt = self._search_exe(os.path.splitext(os.path.basename(exe_path))[0])
            if alt:
                print(f"[Printer] 找到备选可执行文件: {alt}")
                args[0] = exe_path = alt
            else:
                print(f"[Printer] 未找到可执行文件: {exe_path}")
                return  # 不抛异常，主程序继续
        try:
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[Printer] 命令返回非零状态码: {e.returncode}")
        except FileNotFoundError:
            print(f"[Printer] 无法执行: {exe_path}")
    # ---------- 对外 API ----------
    def print_text_utf8(self, text: str):
        self._run([self._exe("PrintTextUTF8"), self.port, f"{text}\n"])
    # 如果以后需要其他功能，可照样调用 _exe
    def feed_lines(self, lines: int):
        self._run([self._exe("FeedLines"), self.port, str(lines)])
    def feed_and_full_cut(self):
        self._run([self._exe("FeedAndFullCut"), self.port])
    def print_image(self, image_path):
        self._run([self._exe("PrintRasterImage"), self.port, str(image_path)])


