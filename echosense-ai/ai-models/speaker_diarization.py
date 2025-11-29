"""
Speaker Diarization - Identify who is speaking when
"""
from typing import List, Dict
import numpy as np


class SpeakerDiarization:
    """
    Simple speaker diarization using audio features
    
    Note: For production, use pyannote.audio or similar
    This is a simplified version for MVP
    """
    
    def __init__(self):
        print("🎭 Speaker Diarization initialized (simplified version)")
    
    def diarize(self, audio_content: bytes, num_speakers: int = 2) -> List[Dict]:
        """
        Perform speaker diarization
        
        Args:
            audio_content: Audio bytes
            num_speakers: Expected number of speakers (default: 2 for agent + customer)
            
        Returns:
            List of segments with speaker labels
            [{"start": 0.0, "end": 5.2, "speaker": "Agent"}, ...]
        """
        # For MVP, we'll use a simple heuristic approach
        # In production, use pyannote.audio or similar
        
        # Simplified logic: alternate between Agent and Customer
        # This is a placeholder - real implementation would use ML models
        
        segments = self._simple_diarization(audio_content)
        return segments
    
    def _simple_diarization(self, audio_content: bytes) -> List[Dict]:
        """
        Simplified diarization using basic heuristics
        
        Assumption: Agent speaks first, then alternates
        This is a placeholder for the MVP
        """
        from pydub import AudioSegment
        from pydub.silence import split_on_silence
        from io import BytesIO
        
        try:
            audio = AudioSegment.from_file(BytesIO(audio_content))
            
            # Split on silence to get speech chunks
            chunks = split_on_silence(
                audio,
                min_silence_len=500,  # 500ms silence
                silence_thresh=-40,    # dB
                keep_silence=200       # Keep 200ms of silence
            )
            
            segments = []
            current_time = 0
            speaker_toggle = True  # Start with Agent
            
            for i, chunk in enumerate(chunks):
                duration = len(chunk) / 1000.0  # Convert to seconds
                
                speaker = "Agent" if speaker_toggle else "Customer"
                
                segments.append({
                    "start": current_time,
                    "end": current_time + duration,
                    "speaker": speaker
                })
                
                current_time += duration
                
                # Toggle speaker (simplified approach)
                # In reality, this should use voice characteristics
                if duration > 2.0:  # Only toggle on longer segments
                    speaker_toggle = not speaker_toggle
            
            return segments
            
        except Exception as e:
            print(f"Diarization error: {e}")
            # Fallback: return single segment
            return [{
                "start": 0.0,
                "end": 60.0,
                "speaker": "Agent"
            }]
    
    def assign_speaker_labels(self, segments: List[Dict]) -> List[Dict]:
        """
        Assign meaningful labels to speakers
        
        Args:
            segments: Raw diarization segments
            
        Returns:
            Segments with "Agent" or "Customer" labels
        """
        # Simple heuristic: first speaker is usually the agent
        if not segments:
            return []
        
        # Label first speaker as Agent
        for seg in segments:
            if "speaker" not in seg or seg["speaker"] == "SPEAKER_00":
                seg["speaker"] = "Agent"
            elif seg["speaker"] == "SPEAKER_01":
                seg["speaker"] = "Customer"
        
        return segments
