import os
from dotenv import load_dotenv
from groq import Groq

# 载入 .env 文件中的 API KEY
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("未在 .env 中找到 GROQ_API_KEY")

# 初始化 Groq 客户端
client = Groq(api_key=api_key)

# 定义简单消息
messages = [
    {"role": "system", "content": "あなたは優しいAIです。"},
    {"role": "user", "content": "こんにちは、元気ですか？"}
]

# 尝试请求
try:
    print("正在连接 Groq API...")
    response = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=messages,
        temperature=0.7,
        max_tokens=100
    )
    print("✅ 成功连接！模型返回：", response.choices[0].message.content)

except Exception as e:
    print("❌ Groq API 请求失败：", str(e))
    