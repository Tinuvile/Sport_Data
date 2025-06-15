#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音识别模块
使用 FunASR 的 Paraformer 模型进行中文语音识别
"""

import os
import logging
from typing import Union, List, Dict, Any

# 首先导入配置，设置缓存目录
import config

from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """语音识别器类"""
    
    def __init__(self, 
                 model_name: str = "paraformer-zh",
                 vad_model: str = "fsmn-vad",
                 punc_model: str = "ct-punc",
                 device: str = "cpu"):
        """
        初始化语音识别器
        
        Args:
            model_name: 主模型名称
            vad_model: VAD（语音活动检测）模型
            punc_model: 标点预测模型
            device: 设备类型 ("cpu" 或 "cuda:0")
        """
        self.model_name = model_name
        self.vad_model = vad_model
        self.punc_model = punc_model
        self.device = device
        self.model = None
        
        logger.info(f"初始化语音识别器，使用模型: {model_name}")
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            self.model = AutoModel(
                model=self.model_name,
                vad_model=self.vad_model,
                punc_model=self.punc_model,
                device=self.device
            )
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def recognize_file(self, 
                      audio_file: str, 
                      batch_size_s: int = 300,
                      hotword: str = None) -> Dict[str, Any]:
        """
        识别音频文件
        
        Args:
            audio_file: 音频文件路径
            batch_size_s: 批处理大小（秒）
            hotword: 热词
            
        Returns:
            识别结果字典
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        try:
            logger.info(f"开始识别音频文件: {audio_file}")
            
            # 设置参数
            kwargs = {
                "input": audio_file,
                "batch_size_s": batch_size_s
            }
            
            if hotword:
                kwargs["hotword"] = hotword
            
            # 执行识别
            result = self.model.generate(**kwargs)
            
            logger.info("音频文件识别完成")
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"音频识别失败: {e}")
            raise
    
    def recognize_audio_data(self, 
                           audio_data: Union[str, bytes, Any],
                           sample_rate: int = 16000,
                           batch_size_s: int = 300) -> Dict[str, Any]:
        """
        识别音频数据
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            batch_size_s: 批处理大小（秒）
            
        Returns:
            识别结果字典
        """
        try:
            logger.info("开始识别音频数据")
            
            result = self.model.generate(
                input=audio_data,
                batch_size_s=batch_size_s
            )
            
            logger.info("音频数据识别完成")
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"音频数据识别失败: {e}")
            raise
    
    def _format_result(self, result: List[Dict]) -> Dict[str, Any]:
        """
        格式化识别结果
        
        Args:
            result: 原始识别结果
            
        Returns:
            格式化后的结果
        """
        if not result:
            return {"text": "", "timestamp": [], "confidence": 0.0}
        
        # 提取文本
        text = result[0].get("text", "")
        
        # 提取时间戳信息
        timestamp = result[0].get("timestamp", [])
        
        # 提取置信度（如果有）
        confidence = result[0].get("confidence", 0.0)
        
        return {
            "text": text,
            "timestamp": timestamp,
            "confidence": confidence,
            "raw_result": result
        }
    
    def recognize_with_vad(self, 
                          audio_file: str,
                          max_single_segment_time: int = 30000) -> Dict[str, Any]:
        """
        使用 VAD 进行语音识别
        
        Args:
            audio_file: 音频文件路径
            max_single_segment_time: VAD 最大单段时长（毫秒）
            
        Returns:
            识别结果
        """
        try:
            logger.info(f"使用 VAD 识别音频文件: {audio_file}")
            
            # 使用 VAD 配置
            result = self.model.generate(
                input=audio_file,
                cache={},
                vad_kwargs={"max_single_segment_time": max_single_segment_time},
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15
            )
            
            logger.info("VAD 语音识别完成")
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"VAD 语音识别失败: {e}")
            raise


class StreamingSpeechRecognizer:
    """流式语音识别器"""
    
    def __init__(self, 
                 model_name: str = "paraformer-zh-streaming",
                 chunk_size: List[int] = [0, 10, 5],
                 encoder_chunk_look_back: int = 4,
                 decoder_chunk_look_back: int = 1):
        """
        初始化流式语音识别器
        
        Args:
            model_name: 流式模型名称
            chunk_size: 分块大小配置 [0, 10, 5] 表示 600ms
            encoder_chunk_look_back: 编码器回看分块数
            decoder_chunk_look_back: 解码器回看分块数
        """
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.encoder_chunk_look_back = encoder_chunk_look_back
        self.decoder_chunk_look_back = decoder_chunk_look_back
        self.model = None
        
        logger.info(f"初始化流式语音识别器，使用模型: {model_name}")
        self._load_model()
    
    def _load_model(self):
        """加载流式模型"""
        try:
            self.model = AutoModel(model=self.model_name)
            logger.info("流式模型加载成功")
        except Exception as e:
            logger.error(f"流式模型加载失败: {e}")
            raise
    
    def recognize_streaming(self, audio_file: str) -> List[Dict[str, Any]]:
        """
        流式识别音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            流式识别结果列表
        """
        import soundfile
        
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        try:
            logger.info(f"开始流式识别音频文件: {audio_file}")
            
            # 读取音频
            speech, sample_rate = soundfile.read(audio_file)
            chunk_stride = self.chunk_size[1] * 960  # 600ms
            
            cache = {}
            results = []
            total_chunk_num = int(len(speech) - 1) // chunk_stride + 1
            
            for i in range(total_chunk_num):
                speech_chunk = speech[i * chunk_stride:(i + 1) * chunk_stride]
                is_final = i == total_chunk_num - 1
                
                result = self.model.generate(
                    input=speech_chunk,
                    cache=cache,
                    is_final=is_final,
                    chunk_size=self.chunk_size,
                    encoder_chunk_look_back=self.encoder_chunk_look_back,
                    decoder_chunk_look_back=self.decoder_chunk_look_back
                )
                
                if result and result[0].get("text"):
                    results.append({
                        "chunk_id": i,
                        "text": result[0]["text"],
                        "is_final": is_final,
                        "raw_result": result
                    })
                    logger.info(f"分块 {i}: {result[0]['text']}")
            
            logger.info("流式识别完成")
            return results
            
        except Exception as e:
            logger.error(f"流式识别失败: {e}")
            raise


def main():
    """主函数，演示使用方法"""
    # 创建语音识别器
    recognizer = SpeechRecognizer()
    
    # 示例：识别音频文件
    # audio_file = "test_audio.wav"  # 替换为您的音频文件路径
    # result = recognizer.recognize_file(audio_file, hotword="魔搭")
    # print(f"识别结果: {result['text']}")
    
    print("语音识别模块初始化完成！")
    print("使用方法：")
    print("1. 创建识别器: recognizer = SpeechRecognizer()")
    print("2. 识别文件: result = recognizer.recognize_file('audio.wav')")
    print("3. 获取文本: text = result['text']")


if __name__ == "__main__":
    main() 