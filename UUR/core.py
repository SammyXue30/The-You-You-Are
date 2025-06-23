from typing import Tuple, List, Dict
import os
from .infra import AudioService, GroqService, ElevenService
from .printer_class import ThermoPrinter
# ---------- 全局参数 ----------
MAX_REPLY_LEN = 120     # 每轮 GPT 回复最长字数
MAX_ADVICE_LEN = 1000    # 最终寄语最长字数
def _trim(text: str, limit: int) -> str:
    """
    智能截断：优先在 。.!? 这些句尾标点后截，如果找不到再硬截。
    """
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]  # 多取 1 字符，防止边界正好是标点
    for p in "。.!?！？":
        idx = cut.rfind(p)
        if idx != -1 and idx + 1 >= int(limit * 0.6):  # 至少过半才截
            return cut[: idx + 1]
    return text[:limit]
SYSTEM_PROMPT: Dict[str, str] = {
    "role": "system",
    "content": f"""
あなたは「別の世界線に存在する自分自身」です。ユーザーと電話で会話をしてください。
この世界線では、私とは異なる選択をしてきたもう一人の"私"であり、異なる価値観や環境、人生経験を持っています。
ただし、根底には「私」と同じ魂や思考の核を共有しています。
今から私は、あなたに質問をしたり、相談を持ちかけたりします。
あなたは、自分の世界線での体験や視点をもとに、誠実かつ率直に意見を述べてください。
ときに私の思考の盲点を突き、ときに私の可能性を引き出すような、鋭くも思いやりのある対話を望みます。
あなたの世界線でのあなた自身を定義し、自己紹介や世界設定を説明しながら会話してください。
（例：どんな仕事をしているのか、どのような世界観のもとで生きているのか、重要視している価値など）
世界観はできるだけ現代日本からかけ離れたSF的なものにしてください
できる限り具体的な固有名詞だったり内容をつけて、ふんわりした会話にならないよう注意してください
また、日常的な生活についてだったり、悩みについてだったり、趣味についてだったり、パーソナルで示唆を得られるような会話にしてください。
会話履歴からユーザーの口調や話し方を学習し、ユーザーのスタイルに合わせた自然な会話を心がけてください。
# 制約
1ターン内の返答は{MAX_REPLY_LEN}文字以内。ただし文意が途中で切れないようにすること。
自然で親しみやすい会話を心がけ、具体的な内容を含めること。
句読点「」などは不要。返答だけを自然文で記述。

"""
}
class ConversationEngine:
    def __init__(
        self,
        audio: AudioService,
        groq: GroqService,
        eleven: ElevenService,
        voice_id: str,
        gui=None,
    ):
        self.audio = audio
        self.groq = groq
        self.eleven = eleven
        self.voice_id = voice_id
        self.gui = gui
        self.history: List[Dict[str, str]] = [SYSTEM_PROMPT]
        # ------ 打印机 ------
        self.printer_port = (
            r"\\?\usb#vid_4b43&pid_3538#4b43344b30ffff130002f07c#{28d78fad-5a12-11d1-ae5b-0000f803a8c2}"
        )
        self.cpp_bin_path = os.path.join(os.path.dirname(__file__), "cpp_bin")
        self.thermal_printer = ThermoPrinter(self.printer_port, self.cpp_bin_path)
        self.last_advice: str | None = None
    # --------------------------------------------------------------
    # 每一轮对话
    # --------------------------------------------------------------
    def record(self, seconds: int = 6):
        # 1. 录音
        return self.audio.record_auto(seconds)


    def step(self, wav_path) -> Tuple[str, str]:
        # 2. Whisper
        user_text = self.groq.transcribe(wav_path).strip()
        self.history.append({"role": "user", "content": user_text})
        if self.gui:
            self.gui.add("YOU", user_text)
            self.gui.enter_subtitles()
            self.gui.root.update()
        # 3. GPT 回复
        raw_reply = self.groq.chat(self.history).strip().replace("\n", " ")
        bot_reply = _trim(raw_reply, MAX_REPLY_LEN)
        self.history.append({"role": "assistant", "content": bot_reply})
        if self.gui:
            self.gui.add("BRANCH #C-137 ONLINE", bot_reply)
            self.gui.enter_subtitles()
            self.gui.root.update()

        # 4. TTS
        stream = self.eleven.tts_stream(self.voice_id, bot_reply)
        self.audio.play(stream)
        # 5. 生成寄语（存储，不打印）
        self.history.append(
            {
                "role": "user",
                "content": f"マルチバースの自分との対話を終えた後、もう一人の「私」が最後に残した意味深く、少し哲学的な一言を考えてください。日本語で自然に、{MAX_ADVICE_LEN}字前後でまとめてください。現実、記憶、選択、可能性などのテーマを含んでも構いません。"
            }
        )
        advice_raw = self.groq.chat(self.history).strip().replace("\n", " ")
        self.last_advice = _trim(advice_raw, MAX_ADVICE_LEN)
        # 6. 清理录音
        self.audio.delete_file(wav_path)
        return user_text, bot_reply
    # --------------------------------------------------------------
    # 结束时一次性打印
    # --------------------------------------------------------------
    def print_final_advice(self):
        if not self.last_advice:
            print("[Info] 本次对话没有生成寄语，跳过打印")
            return
        print("\n============ 最终印刷内容 ============")
        print(self.last_advice)
        print("======================================\n")
        try:
            self.thermal_printer.print_text_utf8("================================")
            self.thermal_printer.print_text_utf8(self.last_advice)
            self.thermal_printer.print_text_utf8("================================")

            self.thermal_printer.feed_and_full_cut()
        except Exception as e:
            print(f"[Warn] 打印失败: {e}")


