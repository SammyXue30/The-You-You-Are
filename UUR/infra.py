import os, uuid, time, numpy as np
import sounddevice as sd
import soundfile  as sf
from io import BytesIO
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError
from groq import Groq
from .config import AUDIO_FORMAT, OUTPUT_DIR, ELEVEN_API_KEY, GROQ_API_KEY
# ---------- 辅助函数：设置麦克风设备 ----------
def _set_mic_device():
    keywords = ["usb", "microphone", "外付", "external"]
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            name = dev['name'].lower()
            if any(kw in name for kw in keywords):
                print(f":麦克风: 使用外接麦克风: [{i}] {dev['name']}")
                sd.default.device = (i, None)
                return
    print(":警告: 未检测到外接麦克风，将使用系统默认设备。")
# ---------- Audio ----------
class AudioService:
    def __init__(self, sr=44100):
        self.sr = sr
        _set_mic_device()
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    def _path(self, prefix, ext=".wav"):
        ts = time.strftime("%Y%m%d_%H%M%S")
        return os.path.join(OUTPUT_DIR, f"{prefix}_{ts}{ext}")
    def record_fixed(self, sec=10):
        input(f"按 Enter 开始录音 {sec} 秒…")
        data = sd.rec(int(sec * self.sr), self.sr, channels=1, dtype="float32")
        sd.wait()
        p = self._path("rec")
        sf.write(p, data, self.sr, format=AUDIO_FORMAT)
        print("录音已保存:", p)
        return p
    def record_auto(self, sec=6):
        print(f"\n◆ 自动录 {sec} 秒，请讲话…")
        data = sd.rec(int(sec * self.sr), self.sr, channels=1, dtype="float32")
        sd.wait()
        p = self._path("user")
        sf.write(p, data, self.sr, format=AUDIO_FORMAT)
        print("◆ 录音结束")
        return p
    def play(self, source):
        if isinstance(source, bytes):
            play(source)
        elif isinstance(source, str):
            with open(source, "rb") as f:
                play(f.read())
        else:  # ElevenLabs 流
            buf = BytesIO()
            [buf.write(c) for c in source if c]
            play(buf.getvalue())
    def delete_file(self, p):
        try:
            os.remove(p)
            print("已删除本地音频:", p)
        except FileNotFoundError:
            pass
    def purge_old(self, hours=1):
        now = time.time()
        for f in os.listdir(OUTPUT_DIR):
            fp = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(fp) and now - os.path.getmtime(fp) > hours * 3600:
                self.delete_file(fp)
# ---------- ElevenLabs ----------
class ElevenService:
    def __init__(self):
        self.cli = ElevenLabs(api_key=ELEVEN_API_KEY)
    def _existing_clone(self):
        for v in self.cli.voices.get_all().voices:
            if v.category == "cloned":
                return v.voice_id
        return None
    def clone_voice(self, wav_path):
        ex = self._existing_clone()
        if ex:
            print("复用 voice_id =", ex)
            return ex
        try:
            with open(wav_path, "rb") as f:
                v = self.cli.voices.ivc.create(
                    name=f"ph_{uuid.uuid4().hex[:6]}",
                    files=[(os.path.basename(wav_path), f.read())],
                    description="MultiversePhone"
                )
            print("克隆成功 voice_id =", v.voice_id)
            return v.voice_id
        except ApiError as e:
            detail = e.body.get("detail", {}) if hasattr(e, "body") else {}
            if detail.get("status") in ("voice_add_edit_limit_reached", "can_not_use_instant_voice_cloning"):
                ex = self._existing_clone()
                if ex:
                    print("用现有 voice_id =", ex)
                    return ex
            raise
    def tts_stream(self, voice_id, text):
        return self.cli.text_to_speech.stream(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings={"use_speaker_boost": True}
        )
    def cleanup_clones(self):
        for v in self.cli.voices.get_all().voices:
            if v.category == "cloned":
                self.cli.voices.delete(v.voice_id)
                print("已删除旧克隆:", v.name)
# ---------- Groq ----------
class GroqService:
    def __init__(self):
        self.cli = Groq(api_key=os.getenv("GROQ_API_KEY"))
    def transcribe(self, wav):
        with open(wav, "rb") as f:
            tr = self.cli.audio.transcriptions.create(model="whisper-large-v3-turbo", file=f)
        return tr.text
    def chat(self, msgs, temp=0.7, max_tokens=300):
        r = self.cli.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=msgs,
            temperature=temp,
            max_tokens=max_tokens
        )
        return r.choices[0].message.content







