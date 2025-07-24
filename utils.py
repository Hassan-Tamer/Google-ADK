import os
import queue
import threading
from groq import Groq # type: ignore
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile

class STT():
    def __init__(self,model='whisper-large-v3'):
        self.client = Groq()
        self.model = model
    
    def getSTT(self):
        """
        Record user audio and send it to Groq Whisper API for transcription.
        """
        audio_file = self.record_audio()
        with open(audio_file, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=file,
                model=self.model,
                prompt="Arabic speech related to hotel customer service",
                language="ar",
                temperature=0.0  
            )
        print("🧠 Transcribed Text:", transcription.text)
        os.remove(audio_file)
        return transcription.text
    
    def record_audio(self, fs=16000):
        """
        Records audio from the microphone. 
        Press Enter to start recording, press Enter again to stop.
        Returns the path to the temporary WAV file.
        """
        print("🎙️ Press Enter to start recording...")
        input()
        
        print("🔴 Recording... Press Enter to stop.")
        
        # Use a queue to collect audio data
        audio_queue = queue.Queue()
        recording_active = threading.Event()
        recording_active.set()
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")
            if recording_active.is_set():
                audio_queue.put(indata.copy())
        
        # Start recording in a separate thread
        stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=fs,
            dtype='int16'
        )
        
        stream.start()
        
        # Wait for second Enter press to stop recording
        input()
        recording_active.clear()
        stream.stop()
        stream.close()
        
        print("🔴 Recording stopped.")
        
        # Collect all audio data from the queue
        audio_data = []
        while not audio_queue.empty():
            audio_data.append(audio_queue.get())
        
        if not audio_data:
            print("No audio data recorded.")
            return None
        
        # Concatenate all audio chunks
        import numpy as np
        recording = np.concatenate(audio_data, axis=0)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav.write(temp_file.name, fs, recording)
        
        return temp_file.name


