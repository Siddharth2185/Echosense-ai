"""
Speech-to-Text using OpenAI Whisper
"""
import whisper
import torch
from io import BytesIO
import tempfile
import os
from typing import Dict, List

from config import get_settings

settings = get_settings()


class WhisperSTT:
    """Speech-to-Text using Whisper model"""
    
    def __init__(self):
        self.device = "cuda" if settings.use_gpu and torch.cuda.is_available() else "cpu"
        self.model_size = settings.whisper_model_size
        self.model = None
        print(f"🎤 Whisper STT initialized (device: {self.device}, model: {self.model_size})")
    
    def _load_model(self):
        """Lazy load the Whisper model"""
        if self.model is None:
            print(f"Loading Whisper model: {self.model_size}...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            print("✅ Whisper model loaded")
    
    def transcribe(self, audio_content: bytes) -> Dict:
        """
        Transcribe audio to text with timestamps
        
        Args:
            audio_content: Audio file bytes (WAV format preferred)
            
        Returns:
            Dict with 'text', 'segments', and 'language'
        """
        self._load_model()
        
        # Write to temporary file (Whisper requires file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_content)
            temp_path = temp_file.name
        
        try:
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                temp_path,
                word_timestamps=True,
                verbose=False
            )
            
            return {
                "text": result["text"],
                "language": result["language"],
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    }
                    for seg in result["segments"]
                ]
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def transcribe_with_diarization(self, audio_content: bytes, speaker_segments: List[Dict]) -> List[Dict]:
        """
        Transcribe audio and assign speakers to segments
        
        Args:
            audio_content: Audio bytes
            speaker_segments: List of dicts with 'start', 'end', 'speaker'
            
        Returns:
            List of transcript segments with speaker labels
        """
        transcription = self.transcribe(audio_content)
        
        # Match transcription segments with speaker segments
        labeled_segments = []
        
        for trans_seg in transcription["segments"]:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_mid = (trans_start + trans_end) / 2
            
            # Find which speaker segment this belongs to
            speaker = "Unknown"
            for spk_seg in speaker_segments:
                if spk_seg["start"] <= trans_mid <= spk_seg["end"]:
                    speaker = spk_seg["speaker"]
                    break
            
            labeled_segments.append({
                "speaker": speaker,
                "text": trans_seg["text"],
                "start_time": trans_seg["start"],
                "end_time": trans_seg["end"]
            })
        
        return labeled_segments
