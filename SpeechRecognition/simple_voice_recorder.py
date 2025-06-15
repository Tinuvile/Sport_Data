#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版实时录音器
按空格键开始/停止录音，保存音频文件
不依赖语音识别模型，可单独使用
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    import keyboard
except ImportError as e:
    print(f"缺少依赖包: {e}")
    print("请运行: python install_recorder_deps.py")
    print("或手动安装: pip install sounddevice soundfile keyboard")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleVoiceRecorder:
    """简化版语音录音器"""
    
    def __init__(self, sample_rate=16000, channels=1):
        """
        初始化录音器
        
        Args:
            sample_rate: 采样率 (Hz)
            channels: 声道数
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_data = []
        
        # 创建录音文件目录 - 使用主目录下的recordings
        self.recordings_dir = Path("../recordings")
        self.recordings_dir.mkdir(exist_ok=True)
        
        logger.info("简化版语音录音器初始化完成")
        logger.info(f"采样率: {self.sample_rate} Hz")
        logger.info(f"声道数: {self.channels}")
        logger.info(f"录音保存目录: {self.recordings_dir}")
    
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            logger.warning("已在录音中...")
            return
        
        self.is_recording = True
        self.audio_data = []
        
        logger.info("🔴 开始录音... (按空格停止)")
        
        def audio_callback(indata, frames, time, status):
            """音频回调函数"""
            if status:
                logger.warning(f"录音状态: {status}")
            
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        # 开始录音流
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=audio_callback,
            dtype=np.float32
        )
        
        self.stream.start()
    
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            logger.warning("当前未在录音...")
            return None
        
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        logger.info("⏹️ 录音已停止")
        
        if not self.audio_data:
            logger.warning("没有录制到音频数据")
            return None
        
        # 合并音频数据
        audio_array = np.concatenate(self.audio_data, axis=0)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = self.recordings_dir / f"recording_{timestamp}.wav"
        
        # 保存音频文件
        try:
            sf.write(audio_file, audio_array, self.sample_rate)
            duration = len(audio_array) / self.sample_rate
            file_size = audio_file.stat().st_size / 1024  # KB
            
            logger.info(f"💾 音频已保存: {audio_file}")
            logger.info(f"📊 录音时长: {duration:.2f} 秒")
            logger.info(f"📊 文件大小: {file_size:.1f} KB")
            
            # 显示提示
            print(f"\n{'='*50}")
            print(f"📝 录音文件: {audio_file.name}")
            print(f"⏱️  时长: {duration:.2f} 秒")
            print(f"📊 大小: {file_size:.1f} KB")
            print("💡 您可以手动播放或用其他工具识别")
            print(f"{'='*50}\n")
            
            return audio_file
            
        except Exception as e:
            logger.error(f"保存音频失败: {e}")
            return None
    
    def get_audio_devices(self):
        """获取音频设备列表"""
        logger.info("可用的音频输入设备:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                logger.info(f"  {i}: {device['name']} (输入声道: {device['max_input_channels']})")
    
    def test_microphone(self, duration=3):
        """测试麦克风"""
        logger.info(f"🎤 测试麦克风 {duration} 秒...")
        
        try:
            # 录制测试音频
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32
            )
            sd.wait()  # 等待录制完成
            
            # 检查音频电平
            max_level = np.max(np.abs(audio_data))
            rms_level = np.sqrt(np.mean(audio_data ** 2))
            
            if max_level > 0.01:
                logger.info(f"✓ 麦克风工作正常")
                logger.info(f"  最大音量: {max_level:.3f}")
                logger.info(f"  平均音量: {rms_level:.3f}")
            else:
                logger.warning(f"⚠️ 麦克风可能有问题")
                logger.warning(f"  最大音量: {max_level:.3f} (建议 > 0.01)")
                logger.warning(f"  请检查麦克风连接和权限设置")
                
        except Exception as e:
            logger.error(f"麦克风测试失败: {e}")
    
    def list_recordings(self):
        """列出录音文件"""
        recordings = list(self.recordings_dir.glob("recording_*.wav"))
        if recordings:
            logger.info(f"📁 录音文件列表 ({len(recordings)} 个):")
            for i, recording in enumerate(sorted(recordings)[-10:], 1):  # 只显示最新10个
                stat = recording.stat()
                size_kb = stat.st_size / 1024
                # 从文件名解析时间
                try:
                    timestamp_str = recording.stem.split('_', 1)[1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = "未知时间"
                
                logger.info(f"  {i:2d}. {recording.name} ({size_kb:.1f} KB, {time_str})")
        else:
            logger.info("📁 暂无录音文件")


def main():
    """主函数"""
    print("🎤 简化版实时录音器")
    print("=" * 50)
    print("操作说明:")
    print("  按 [空格] 开始录音")
    print("  再按 [空格] 停止录音")
    print("  按 [ESC] 退出程序")
    print("  按 [T] 测试麦克风")
    print("  按 [D] 显示音频设备")
    print("  按 [L] 列出录音文件")
    print("=" * 50)
    
    # 创建录音器
    recorder = SimpleVoiceRecorder()
    
    # 显示设备信息
    recorder.get_audio_devices()
    
    print(f"\n等待按键操作...")
    
    try:
        while True:
            event = keyboard.read_event()
            
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'space':
                    if not recorder.is_recording:
                        recorder.start_recording()
                    else:
                        recorder.stop_recording()
                
                elif event.name == 'esc':
                    print("\n👋 退出程序")
                    if recorder.is_recording:
                        recorder.stop_recording()
                    break
                
                elif event.name == 't':
                    print("\n🎤 开始麦克风测试...")
                    recorder.test_microphone()
                    print("等待按键操作...")
                
                elif event.name == 'd':
                    print("\n📱 音频设备列表:")
                    recorder.get_audio_devices()
                    print("等待按键操作...")
                
                elif event.name == 'l':
                    print("\n📁 录音文件:")
                    recorder.list_recordings()
                    print("等待按键操作...")
    
    except KeyboardInterrupt:
        print("\n👋 程序已中断")
        if recorder.is_recording:
            recorder.stop_recording()
    
    except Exception as e:
        logger.error(f"程序错误: {e}")
        if recorder.is_recording:
            recorder.stop_recording()


if __name__ == "__main__":
    main() 