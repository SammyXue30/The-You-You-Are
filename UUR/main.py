"""
交互逻辑
#  → 10-s 自我介绍 → 循环对话（6-s）
* / s  → 打印寄语 ➜ 回到等待 #
Quit / Esc → 退出进程
终端持续输出进度提示
"""
import threading, time, sys
import serial
from .infra import AudioService, GroqService, ElevenService
from .core  import ConversationEngine
from .ui_cli import SubtitleWindow

import queue
from multiprocessing import Process


# ── 参数设置 ─────────────────────────────────────────────
PORT, BAUD = "COM3", 115200
INTRO_SEC, DIALOG_SEC = 10, 6
START_KEY, END_KEY = "#", "*"
SWITCH_KEY = "s"
# ── 打开串口一次，循环使用 ───────────────────────────────
try:
    SER = serial.Serial(PORT, BAUD, timeout=0)
    print(f"[Serial] {PORT} opened ({BAUD} bps)")
except serial.serialutil.SerialException:
    print(f"[Serial] Cannot open {PORT}")
    sys.exit(1)
# ── 串口读取辅助函数 ─────────────────────────────────────
def poll_key() -> str:
    # SER.reset_input_buffer()
    if SER.in_waiting:
        raw = SER.readline().decode("utf-8", errors="ignore").strip()
        # print(f"Serial read: {raw}")
        return raw.split()[-1] if raw else ""
    return ""
def detect_sharp(gui):
    while gui.root.winfo_exists():
        if poll_key() == START_KEY:
            print("[Serial] # detected – starting self-intro")
            break
        gui.root.update()
        time.sleep(0.05)


def detect_switch_while(gui):
    while gui.root.winfo_exists():

        counter = 0
        delay_time = 0.01
        delay_count = 50

        for _ in range(delay_count):
            if poll_key() == SWITCH_KEY:
                # print("[Serial] s detected – phone picked up")
                counter += 1

            time.sleep(delay_time)
        
        if counter == 0:
            break


        gui.root.update()
        time.sleep(0.05)


# ── 主程序入口 ───────────────────────────────────────────
def main():

    gui = SubtitleWindow()
    print("[App] Window shown")
    while gui.root.winfo_exists():
        # === 拿起电话阶段 ======================================
        gui.clear_subtitles()
        gui.counter.config(text="")
        gui.root.update()
        



        gui.set_prompt("Please pick up the phone")
        # detect_switch_while(gui)
        # time.sleep(2)
        # key = poll_key()
        # while key == SWITCH_KEY:
        #     print('debug')
        #     key = poll_key()
        #     time.sleep(1)
        detect_switch_while(gui)
        print('[Serial] Phone is picked up')
        gui.root.update()





        # === 展示协议等内容 ====================================




        gui.clear_subtitles()
        gui.set_prompt('''マルチバース通話センター 利用同意書
本サービスは、並行宇宙に存在する“あなた”との音声対話を体験いただくものです。
以下の内容にご同意の上、ご利用ください。
⸻
• 通話体験中、お客様の声を一時的に取得し、リアルタイム処理に使用します。
• 取得した音声情報は、体験終了後すぐに削除され、保存・記録は一切行いません。
• 本サービスは演出目的であり、個人情報の収集・利用を目的としたものではありません。
⸻
上記にご同意いただける場合は、「#」ボタンを押して通話を開始してください。'''
)

        gui.root.update()





        dialog_end = threading.Event()
        def play_mp3_thread():
            audio_intro = AudioService()
            audio_intro.play("C:\\Users\\cyber\\Desktop\\UUR\\a.mp3")
            dialog_end.set()

        t = threading.Thread(target=play_mp3_thread, daemon=True)
        t.start()

        # if gui.root.winfo_exists() and not dialog_end.is_set():
        #     # 主线程内手动倒计时刷新，避免线程中调用 GUI
        #     for t in range(DIALOG_SEC, 0, -1):

        #         gui.counter.config(text=f"{t} s")
        #         gui.root.update()
        #         time.sleep(1)
        #     gui.counter.config(text="")




















        time.sleep(1)


        # === 等待 # 启动自我介绍 ===============================
        # gui.clear_subtitles()
        # gui.set_prompt("Input phone number\nPress # to start 10-s self-intro")
        # gui.counter.config(text="")
        print("[State] Waiting for # …")
        detect_sharp(gui)
        if not gui.root.winfo_exists():
            break
        # === 自我介绍（10 秒录音 + 克隆语音） ====================
        gui.set_prompt("Self-intro recording …")
        gui.start_countdown(INTRO_SEC, "Self-intro: {} s")
        result = {}
        intro_done = threading.Event()
        def intro_thread():
            audio = AudioService()
            groq = GroqService()
            eleven = ElevenService()
            intro_wav = audio.record_auto(INTRO_SEC)
            voice_id = eleven.clone_voice(intro_wav)
            result.update(dict(audio=audio, groq=groq,
                               eleven=eleven, voice_id=voice_id))
            intro_done.set()
        threading.Thread(target=intro_thread, daemon=True).start()
        while gui.root.winfo_exists() and not intro_done.is_set():
            gui.root.update()
            time.sleep(0.05)
        if not gui.root.winfo_exists():
            break
        audio = result["audio"]
        groq = result["groq"]
        eleven = result["eleven"]
        voice_id = result["voice_id"]
        print("[Audio] Intro done, voice_id =", voice_id)
        # === 对话阶段（语音交互 + 手动倒计时） ===================
        engine = ConversationEngine(audio, groq, eleven, voice_id, gui)
        gui.set_prompt("Talking… (press * or s to end)")
        gui.enter_subtitles()


                
        key = poll_key()
        while key != SWITCH_KEY:
            
            # engine.record(DIALOG_SEC)

            dialog_end = threading.Event()
            q = queue.Queue()
            def record_thread(q):
                wav_path = engine.record(DIALOG_SEC)
                q.put(wav_path)
                dialog_end.set()

            t = threading.Thread(target=record_thread, daemon=True, args = (q,))
            t.start()

            if gui.root.winfo_exists() and not dialog_end.is_set():
                # 主线程内手动倒计时刷新，避免线程中调用 GUI
                for t in range(DIALOG_SEC, 0, -1):

                    gui.counter.config(text=f"{t} s")
                    gui.root.update()
                    time.sleep(1)
                gui.counter.config(text="")

            wav_path = q.get()

            engine.step(wav_path)
            key = poll_key()




        # === 打印寄语 & 清理语音克隆 ==============================
        gui.set_prompt("Printing advice …")
        engine.print_final_advice()
        eleven.cleanup_clones()
        print("[Printer] Advice printed – reset")
        # === 重置回等待状态 =======================================
        # 循环回到顶部
    print("[App] Exit")
    SER.close()
# ── 启动程序 ──────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[App] KeyboardInterrupt – exit")
        SER.close()






