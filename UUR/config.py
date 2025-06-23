"""
配置常量 & 环境变量
"""
import os
from dotenv import load_dotenv, find_dotenv
# --------------------------------------------------------------
# 1. 尝试在当前工作目录向上搜索 .env
# --------------------------------------------------------------
found = find_dotenv()
# 2. 若没找到，再拼接包根目录的 .env
if not found:
    PKG_ROOT = os.path.dirname(os.path.abspath(__file__))  # ...\UUR
    found = os.path.join(os.path.dirname(PKG_ROOT), ".env")  # 项目根
# 3. 加载
load_dotenv(found, override=False)
# --------------------------------------------------------------
# 常量
# --------------------------------------------------------------
AUDIO_FORMAT = "WAV"          # 可改 MP3 / OGG / FLAC
OUTPUT_DIR   = "audio_outputs"
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# ELEVEN_API_KEY = 'None'
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
# GROQ_API_KEY = 'None'

if not (ELEVEN_API_KEY and GROQ_API_KEY):
    raise RuntimeError(
        f"未能从 {found} 读取 ELEVENLABS_API_KEY / GROQ_API_KEY，请检查 .env 或系统环境变量。"
    )
