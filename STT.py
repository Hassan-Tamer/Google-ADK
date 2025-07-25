import os
import queue
import threading
import tempfile
from abc import ABC, abstractmethod
from typing import Optional
import sounddevice as sd # type: ignore
import scipy.io.wavfile as wav # type: ignore
import numpy as np

# GCP
import subprocess
from google.cloud import speech

# Groq
from groq import Groq # type: ignore


class STTStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Transcribes a given WAV file and returns the text."""
        pass


class GCP_STT(STTStrategy):
    def __init__(self):
        self.client = speech.SpeechClient()

    @property
    def name(self) -> str:
        return "GCP_STT"
    
    def convert_to_linear16(self, input_path: str, output_path: str):
        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-ac", "1",           # Mono
            "-ar", "16000",       # 16kHz
            "-f", "wav",          # WAV format
            output_path
        ], check=True)

    def transcribe(self, audio_path: str) -> str:
        converted_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        self.convert_to_linear16(audio_path, converted_path)

        with open(converted_path, "rb") as f:
            content = f.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="ar-SA",
        )

        response = self.client.recognize(config=config, audio=audio)
        results = [result.alternatives[0].transcript for result in response.results]
        return " ".join(results)


class GroqWhisper_STT(STTStrategy):
    def __init__(self, model='whisper-large-v3'):
        self.client = Groq()
        self.model = model
        # self.prompt = "محادثة باللغة العربية بين موظف استقبال فندق وزبون، تتعلق بخدمة العملاء..."
        self.prompt = "Arabic speech related to hotel customer service"

    @property
    def name(self) -> str:
        return "GroqWhisper_STT"
    
    def transcribe(self, audio_path: str) -> str:
        with open(audio_path, "rb") as f:
            transcription = self.client.audio.transcriptions.create(
                file=f,
                model=self.model,
                prompt=self.prompt,
                language="ar",
                temperature=0.0
            )
        return transcription.text


class STTClient:
    def __init__(self, strategy: STTStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: STTStrategy):
        self.strategy = strategy

    def record_audio(self, fs=16000) -> Optional[str]:
        print("🎙️ Press Enter to start recording...")
        input()
        print("🔴 Recording... Press Enter again to stop.")

        q = queue.Queue()
        stop_flag = threading.Event()
        stop_flag.set()

        def callback(indata, frames, time, status):
            if stop_flag.is_set():
                q.put(indata.copy())

        stream = sd.InputStream(
            callback=callback,
            channels=1,
            samplerate=fs,
            dtype='int16'
        )
        stream.start()

        input()
        stop_flag.clear()
        stream.stop()
        stream.close()
        print("🛑 Recording stopped.")

        frames = []
        while not q.empty():
            frames.append(q.get())

        if not frames:
            print("⚠️ No audio recorded.")
            return None

        audio = np.concatenate(frames, axis=0)
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav.write(temp_file.name, fs, audio)
        return temp_file.name

    def listen_and_transcribe(self) -> Optional[str]:
        audio_path = self.record_audio()
        if not audio_path:
            return None
        transcript = self.strategy.transcribe(audio_path)
        os.remove(audio_path)
        print(f"Transcribed Text[{self.strategy.name}]:", transcript)
        return transcript

if __name__ == "__main__":
    gcp_stt = GCP_STT()
    groq_stt = GroqWhisper_STT()
    client = STTClient(groq_stt)

    client.listen_and_transcribe()
    client.set_strategy(gcp_stt)
    client.listen_and_transcribe()
