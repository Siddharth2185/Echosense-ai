"""
Sentiment Analysis using Transformers
"""
from transformers import pipeline
import torch
from typing import Dict, List

from config import get_settings

settings = get_settings()


class SentimentAnalyzer:
    """Sentiment analysis for call transcripts"""
    
    def __init__(self):
        self.device = 0 if settings.use_gpu and torch.cuda.is_available() else -1
        self.model = None
        print(f"😊 Sentiment Analyzer initialized (device: {'GPU' if self.device == 0 else 'CPU'})")
    
    def _load_model(self):
        """Lazy load the sentiment model"""
        if self.model is None:
            print("Loading sentiment analysis model...")
            # Using a model fine-tuned for conversational sentiment
            self.model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=self.device
            )
            print("✅ Sentiment model loaded")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text segment
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with 'sentiment' and 'score'
        """
        self._load_model()
        
        if not text or len(text.strip()) < 3:
            return {"sentiment": "neutral", "score": 0.0}
        
        try:
            result = self.model(text[:512])[0]  # Limit to 512 chars
            
            # Convert to our sentiment types
            sentiment = self._map_sentiment(result["label"], result["score"])
            
            # Convert score to -1 to 1 range
            score = result["score"] if result["label"] == "POSITIVE" else -result["score"]
            
            return {
                "sentiment": sentiment,
                "score": round(score, 3)
            }
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.0}
    
    def analyze_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for multiple transcript segments
        
        Args:
            segments: List of transcript segments with 'text' field
            
        Returns:
            Segments with added 'sentiment' and 'sentiment_score' fields
        """
        self._load_model()
        
        for segment in segments:
            if "text" in segment:
                analysis = self.analyze_text(segment["text"])
                segment["sentiment"] = analysis["sentiment"]
                segment["sentiment_score"] = analysis["score"]
        
        return segments
    
    def get_overall_sentiment(self, segments: List[Dict]) -> Dict:
        """
        Calculate overall sentiment for entire conversation
        
        Args:
            segments: Analyzed segments with sentiment scores
            
        Returns:
            Dict with overall sentiment and average score
        """
        if not segments:
            return {"sentiment": "neutral", "avg_score": 0.0}
        
        scores = [seg.get("sentiment_score", 0.0) for seg in segments if "sentiment_score" in seg]
        
        if not scores:
            return {"sentiment": "neutral", "avg_score": 0.0}
        
        avg_score = sum(scores) / len(scores)
        
        # Determine overall sentiment
        if avg_score > 0.3:
            sentiment = "positive"
        elif avg_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "avg_score": round(avg_score, 3),
            "positive_segments": sum(1 for s in scores if s > 0.3),
            "negative_segments": sum(1 for s in scores if s < -0.3),
            "neutral_segments": sum(1 for s in scores if -0.3 <= s <= 0.3)
        }
    
    def _map_sentiment(self, label: str, score: float) -> str:
        """Map model output to our sentiment categories"""
        if label == "POSITIVE":
            if score > 0.8:
                return "satisfied"
            else:
                return "positive"
        elif label == "NEGATIVE":
            if score > 0.8:
                return "frustrated"
            else:
                return "negative"
        else:
            return "neutral"
    
    def analyze_by_speaker(self, segments: List[Dict]) -> Dict:
        """
        Analyze sentiment separately for each speaker
        
        Args:
            segments: Segments with 'speaker' and 'sentiment_score'
            
        Returns:
            Dict with sentiment stats per speaker
        """
        speaker_sentiments = {}
        
        for segment in segments:
            speaker = segment.get("speaker", "Unknown")
            score = segment.get("sentiment_score", 0.0)
            
            if speaker not in speaker_sentiments:
                speaker_sentiments[speaker] = []
            
            speaker_sentiments[speaker].append(score)
        
        results = {}
        for speaker, scores in speaker_sentiments.items():
            avg_score = sum(scores) / len(scores) if scores else 0.0
            results[speaker] = {
                "avg_score": round(avg_score, 3),
                "sentiment": "positive" if avg_score > 0.3 else "negative" if avg_score < -0.3 else "neutral",
                "total_segments": len(scores)
            }
        
        return results
