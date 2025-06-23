import sounddevice as sd
import soundfile as sf
import os
import time
def find_external_mic():
    keywords = ["usb", "microphone", "外付", "external"]
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            name_lower = dev['name'].lower()
            if any(kw in name_lower for kw in keywords):
                return i, dev['name']
    return None, None
def record_with_device(device_index, duration=10, samplerate=44100):
    print(f":麦克风: 使用设备 {device_index} 开始录音：{duration} 秒")
    sd.default.device = (device_index, None)
    data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()
    return data
def save_to_desktop(data, samplerate, filename="外接麦克风测试.wav"):
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    output_path = os.path.join(desktop_path, filename)
    sf.write(output_path, data, samplerate)
    print(f":白色的对勾: 已保存音频到：{output_path}")
def main():
    mic_index, mic_name = find_external_mic()
    if mic_index is None:
        print(":x: 未找到外接麦克风，请确认已连接。")
        return
    print(f":白色的对勾: 找到外接麦克风: [{mic_index}] {mic_name}")
    data = record_with_device(mic_index, duration=10)
    save_to_desktop(data, samplerate=44100)
if __name__ == "__main__":
    main()












