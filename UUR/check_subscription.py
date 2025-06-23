import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# 载入 .env 中的变量
load_dotenv()
API_KEY = os.getenv("ELEVENLABS_API_KEY")

def check_subscription_status():
    if not API_KEY:
        print("❌ 没有找到 ELEVENLABS_API_KEY，请检查 .env 文件")
        return

    cli = ElevenLabs(api_key=API_KEY)

    try:
        subs = cli.user.subscription.get()
        print("\n📊 当前订阅信息")
        print("-" * 40)
        print(f"订阅等级（tier）：{subs.tier}")
        print(f"是否可以使用即时语音克隆（IVC）：{subs.can_use_instant_voice_cloning}")
        print(f"已用语音槽位：{subs.voice_slots_used} / {subs.voice_limit}")
        print(f"已用专业语音槽位：{subs.professional_voice_slots_used}")
        print(f"每月已用克隆次数（创建/编辑）：{subs.voice_add_edit_counter}")
        print(f"是否可以使用专业语音克隆（PVC）：{subs.can_use_professional_voice_cloning}")
        print("-" * 40)
    except Exception as e:
        print(f"❌ 无法获取订阅信息: {e}")

if __name__ == "__main__":
    check_subscription_status()