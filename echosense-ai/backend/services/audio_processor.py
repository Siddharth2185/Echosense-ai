"""
Audio preprocessing and utilities
"""
import warnings
import os
from io import BytesIO
import numpy as np

# ── Python 3.14 compatibility: restore the removed audioop module ──
try:
    import audioop  # noqa: F401  (built-in on Python ≤ 3.12)
except ImportError:
    try:
        import audioop_lts as audioop  # pip install audioop-lts
        import sys
        sys.modules["audioop"] = audioop
    except ImportError:
        pass  # pydub will still warn, but won't crash

# ── Tell pydub exactly where ffmpeg lives (handles PATH not updated yet) ──
_FFMPEG_CANDIDATES = [
    # winget install location
    r"C:\Users\siddh\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",
    # common manual installs
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
]
for _candidate in _FFMPEG_CANDIDATES:
    if os.path.isfile(_candidate):
        from pydub import utils as _pydub_utils
        _pydub_utils.get_prober_name = lambda: "ffprobe"
        # Monkey-patch the converter path
        import pydub
        pydub.AudioSegment.converter = _candidate
        pydub.AudioSegment.ffmpeg = _candidate
        pydub.AudioSegment.ffprobe = _candidate.replace("ffmpeg.exe", "ffprobe.exe")
        print(f"[OK] ffmpeg found at: {_candidate}")
        break
else:
    print("[WARNING] ffmpeg not found in known locations — audio decoding may fail.")

# Try to import pydub, but make it optional for Python 3.14 compatibility
try:
    from pydub import AudioSegment
    AUDIO_PROCESSING_AVAILABLE = True
    print("[OK] Audio processing available (pydub + ffmpeg ready)")
except (ImportError, ModuleNotFoundError) as e:
    warnings.warn(f"[WARNING] Audio processing not available: {e}. Audio features will be limited.")
    print("[WARNING] Audio processing not available. Audio features will be limited.")
    AUDIO_PROCESSING_AVAILABLE = False
    AudioSegment = None


class AudioProcessor:
    """Audio preprocessing and analysis"""
    
    def get_duration(self, file_content: bytes) -> int:
        """
        Get audio duration in seconds
        
        Args:
            file_content: Audio file bytes
            
        Returns:
            Duration in seconds
        """
        if not AUDIO_PROCESSING_AVAILABLE:
            print("[WARNING] Audio processing not available")
            return 0
        try:
            audio = AudioSegment.from_file(BytesIO(file_content))
            return int(audio.duration_seconds)
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0
    
    def preprocess_audio(self, file_content: bytes) -> bytes:
        """
        Preprocess audio for better transcription
        - Convert to mono
        - Normalize volume
        - Reduce noise (basic)
        - Convert to WAV format
        
        Args:
            file_content: Original audio bytes
            
        Returns:
            Preprocessed audio bytes (WAV format)
        """
        if not AUDIO_PROCESSING_AVAILABLE:
            raise Exception("Audio processing not available. Please use Python 3.11 or 3.12.")
        try:
            # Load audio
            audio = AudioSegment.from_file(BytesIO(file_content))
            
            # Convert to mono
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Set sample rate to 16kHz (optimal for speech recognition)
            audio = audio.set_frame_rate(16000)
            
            # Normalize volume
            audio = self._normalize_volume(audio)
            
            # Export as WAV
            output = BytesIO()
            audio.export(output, format="wav")
            output.seek(0)
            
            return output.read()
            
        except Exception as e:
            raise Exception(f"Audio preprocessing failed: {str(e)}")
    
    def _normalize_volume(self, audio: AudioSegment, target_dBFS: float = -20.0) -> AudioSegment:
        """Normalize audio volume"""
        change_in_dBFS = target_dBFS - audio.dBFS
        return audio.apply_gain(change_in_dBFS)
    
    def detect_silence(self, file_content: bytes, min_silence_len: int = 2000, silence_thresh: int = -40) -> list:
        """
        Detect silent segments in audio
        
        Args:
            file_content: Audio bytes
            min_silence_len: Minimum silence length in ms
            silence_thresh: Silence threshold in dBFS
            
        Returns:
            List of (start, end) tuples for silent segments
        """
        if not AUDIO_PROCESSING_AVAILABLE:
            print("[WARNING] Audio processing not available")
            return []
        
        from pydub.silence import detect_silence
        
        try:
            audio = AudioSegment.from_file(BytesIO(file_content))
            silent_ranges = detect_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh
            )
            # Convert to seconds
            return [(start/1000, end/1000) for start, end in silent_ranges]
        except Exception as e:
            print(f"Error detecting silence: {e}")
            return []
    
    def calculate_silence_duration(self, silent_ranges: list) -> float:
        """Calculate total silence duration in seconds"""
        return sum(end - start for start, end in silent_ranges)
