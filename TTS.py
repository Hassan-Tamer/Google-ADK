import os
import tempfile
from abc import ABC, abstractmethod
from pydub import AudioSegment # type: ignore
from pydub.playback import play # type: ignore
import mishkal.tashkeel
# GCP imports
from google.cloud import texttospeech

# PlayAI (Groq) imports
from groq import Groq # type: ignore

# Base Strategy
class TTSStrategy(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> str:
        """Synthesize text and return path to a WAV file"""
        pass

# GCP TTS implementation
class GCP_TTS(TTSStrategy):
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()

    def synthesize(self, text: str) -> str:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ar-XA",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            name="ar-XA-Chirp3-HD-Callirrhoe"
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = self.client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        mp3_temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        mp3_temp.write(response.audio_content)
        mp3_temp.close()

        # Convert MP3 to WAV
        wav_temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sound = AudioSegment.from_mp3(mp3_temp.name)
        sound.export(wav_temp.name, format="wav")

        return wav_temp.name

# PlayAI (Groq) TTS implementation
class PlayAI_TTS(TTSStrategy):
    def __init__(self, model='playai-tts-arabic', voice="Amira-PlayAI"):
        self.client = Groq()
        self.model = model
        self.voice = voice

    def synthesize(self, text: str) -> str:
        print("Beginning TTS conversion (PlayAI)")
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3"
        )

        mp3_temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        response.write_to_file(mp3_temp.name)

        # Convert MP3 to WAV
        wav_temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sound = AudioSegment.from_mp3(mp3_temp.name)
        sound.export(wav_temp.name, format="wav")

        return wav_temp.name

# TTS Client
class TTSClient:
    def __init__(self, strategy: TTSStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: TTSStrategy):
        self.strategy = strategy

    def speak(self, text: str, use_tashkeel: bool = False):
        if use_tashkeel:
            print("Applying tashkeel to text...")
            vocalizer = mishkal.tashkeel.TashkeelClass()
            text = vocalizer.tashkeel(text)
            print(f"Text with tashkeel: {text}")
        wav_file = self.strategy.synthesize(text)
        sound = AudioSegment.from_wav(wav_file)
        print("Playing response...")
        play(sound)
        os.remove(wav_file)


if __name__ == "__main__":
    gcp_tts = GCP_TTS()
    playai_tts = PlayAI_TTS()
    
    client = TTSClient(gcp_tts)
    client.speak("Hello from GCP!")

    client.set_strategy(playai_tts)
    client.speak("Hello from PlayAI!")

