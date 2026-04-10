# -*- coding: utf-8 -*-
"""
TTS语音合成服务
基于阿里云百炼CosyVoice实现语音合成
Author: SixpenniesS
"""

import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from config import (
    ALIBABA_API_KEY, TTS_ENABLED, TTS_MODEL,
    TTS_VOICE, TTS_RATE, TTS_OUTPUT_DIR
)

logger = logging.getLogger(__name__)


class TTSService:
    """TTS语音合成服务

    基于阿里云百炼CosyVoice实现语音合成。

    功能：
    - 文本转语音
    - 多音色支持
    - 语速调节
    """

    def __init__(self):
        """初始化TTS服务"""
        self.api_key = ALIBABA_API_KEY
        self.tts_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts"
        self.enabled = TTS_ENABLED
        self.model = TTS_MODEL
        self.voice = TTS_VOICE
        self.rate = TTS_RATE
        self.output_dir = Path(TTS_OUTPUT_DIR)

        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"TTS服务初始化完成: voice={self.voice}, rate={self.rate}")

    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """合成语音

        Args:
            text: 要合成的文本
            output_path: 输出路径（可选）

        Returns:
            音频文件路径或None
        """
        if not self.enabled:
            logger.info("TTS服务已禁用")
            return None

        if not text:
            logger.warning("文本为空，跳过TTS")
            return None

        try:
            # 生成输出路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"tts_{timestamp}.mp3")

            # 调用TTS API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"
            }

            data = {
                "model": self.model,
                "input": {
                    "text": text
                },
                "parameters": {
                    "voice": self.voice,
                    "rate": self.rate,
                    "format": "mp3"
                }
            }

            response = requests.post(
                self.tts_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # 处理异步任务
            if "output" in result:
                task_id = result["output"].get("task_id")
                if task_id:
                    # 等待任务完成
                    audio_url = self._wait_for_task(task_id)
                    if audio_url:
                        # 下载音频
                        return self._download_audio(audio_url, output_path)

            logger.error(f"TTS响应格式错误: {result}")
            return None

        except Exception as e:
            logger.error(f"TTS合成失败: {str(e)}")
            return None

    def _wait_for_task(self, task_id: str, max_wait: int = 30) -> Optional[str]:
        """等待异步任务完成

        Args:
            task_id: 任务ID
            max_wait: 最大等待时间（秒）

        Returns:
            音频URL或None
        """
        import time

        status_url = f"{self.tts_url}/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        for _ in range(max_wait):
            try:
                response = requests.get(status_url, headers=headers, timeout=10)
                response.raise_for_status()

                result = response.json()
                status = result.get("output", {}).get("task_status")

                if status == "SUCCEEDED":
                    return result.get("output", {}).get("results", {}).get("audio_url")
                elif status == "FAILED":
                    logger.error(f"TTS任务失败: {result}")
                    return None

                time.sleep(1)

            except Exception as e:
                logger.error(f"查询TTS任务状态失败: {str(e)}")
                return None

        logger.error("TTS任务超时")
        return None

    def _download_audio(self, url: str, output_path: str) -> Optional[str]:
        """下载音频文件

        Args:
            url: 音频URL
            output_path: 输出路径

        Returns:
            本地文件路径
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"音频已保存: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"下载音频失败: {str(e)}")
            return None

    def synthesize_and_play(
        self,
        text: str,
        play_audio: bool = False,
        async_play: bool = True
    ) -> Optional[str]:
        """合成并播放语音

        Args:
            text: 文本
            play_audio: 是否播放
            async_play: 是否异步播放

        Returns:
            音频路径
        """
        audio_path = self.synthesize(text)

        if audio_path and play_audio:
            try:
                if async_play:
                    # 异步播放
                    import subprocess
                    if os.name == "nt":
                        subprocess.Popen(
                            ["cmd", "/c", "start", "", audio_path],
                            shell=True
                        )
                    else:
                        subprocess.Popen(["afplay", audio_path])
                else:
                    # 同步播放
                    if os.name == "nt":
                        os.system(f'cmd /c start "" "{audio_path}"')
                    else:
                        os.system(f"afplay {audio_path}")

            except Exception as e:
                logger.error(f"播放音频失败: {str(e)}")

        return audio_path

    def clean_old_audio_files(self, keep_last_n: int = 10) -> int:
        """清理旧音频文件

        Args:
            keep_last_n: 保留最近的文件数量

        Returns:
            删除的文件数量
        """
        if not self.enabled:
            return 0

        try:
            files = sorted(
                self.output_dir.glob("tts_*.mp3"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            deleted = 0
            for file in files[keep_last_n:]:
                file.unlink()
                deleted += 1

            if deleted > 0:
                logger.info(f"清理了 {deleted} 个旧音频文件")

            return deleted

        except Exception as e:
            logger.error(f"清理音频文件失败: {str(e)}")
            return 0
