"""
Sentiment analysis utilities for ESB Chatbot System
"""
import logging
from typing import Dict, Optional
from abc import ABC, abstractmethod

# Sentiment analysis libraries
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# LLM integrations
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..core.models import SentimentResult, SentimentLabel
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer(ABC):
    """Abstract base class for sentiment analyzers"""
    
    @abstractmethod
    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of given text"""
        pass


class TextBlobAnalyzer(SentimentAnalyzer):
    """TextBlob-based sentiment analyzer"""
    
    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment using TextBlob, with extra rule for negative phrases like 'don't like'"""
        try:
            text_lower = text.lower()
            # Rule-based override for negative expressions
            negative_phrases = ["don't like", "do not like", "dislike", "hate", "can't stand", "detest", "loathe"]
            if any(phrase in text_lower for phrase in negative_phrases):
                label = SentimentLabel.NEGATIVE
                confidence = 0.9
                polarity = -0.5
                subjectivity = 0.7
                reasoning = f"Rule-based: detected negative phrase in '{text}'"
                return SentimentResult(
                    label=label,
                    confidence=confidence,
                    scores={
                        "polarity": polarity,
                        "subjectivity": subjectivity
                    },
                    reasoning=reasoning
                )
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # Range: -1 to 1
            subjectivity = blob.sentiment.subjectivity  # Range: 0 to 1
            # Convert polarity to sentiment label
            if polarity > 0.1:
                label = SentimentLabel.POSITIVE
            elif polarity < -0.1:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            # Convert polarity to confidence (0 to 1)
            confidence = abs(polarity)
            return SentimentResult(
                label=label,
                confidence=confidence,
                scores={
                    "polarity": polarity,
                    "subjectivity": subjectivity
                },
                reasoning=f"TextBlob analysis: polarity={polarity:.3f}, subjectivity={subjectivity:.3f}"
            )
        except Exception as e:
            logger.error(f"TextBlob analysis error: {e}")
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                scores={},
                reasoning=f"Error in TextBlob analysis: {str(e)}"
            )


class VaderAnalyzer(SentimentAnalyzer):
    """VADER sentiment analyzer"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment using VADER"""
        try:
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']
            
            # Convert compound score to sentiment label
            if compound >= 0.05:
                label = SentimentLabel.POSITIVE
            elif compound <= -0.05:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            
            # Use compound score as confidence
            confidence = abs(compound)
            
            return SentimentResult(
                label=label,
                confidence=confidence,
                scores=scores,
                reasoning=f"VADER analysis: compound={compound:.3f}"
            )
        except Exception as e:
            logger.error(f"VADER analysis error: {e}")
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                scores={},
                reasoning=f"Error in VADER analysis: {str(e)}"
            )


class OpenAIAnalyzer(SentimentAnalyzer):
    """OpenAI-based sentiment analyzer"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        
        self.settings = get_settings()
        self.api_key = api_key or self.settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment using OpenAI"""
        try:
            prompt = f"""
            Analyze the sentiment of the following text and respond with a JSON object containing:
            - "label": one of "positive", "negative", or "neutral"
            - "confidence": a float between 0 and 1
            - "reasoning": a brief explanation
            
            Text to analyze: "{text}"
            
            Respond only with valid JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return SentimentResult(
                label=SentimentLabel(result["label"]),
                confidence=float(result["confidence"]),
                scores={"openai_confidence": result["confidence"]},
                reasoning=result.get("reasoning", "OpenAI analysis")
            )
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                scores={},
                reasoning=f"Error in OpenAI analysis: {str(e)}"
            )


class OllamaAnalyzer(SentimentAnalyzer):
    """Ollama-based sentiment analyzer using local LLM"""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama library not available")

        self.settings = get_settings()
        self.model = model or self.settings.ollama_model
        self.base_url = base_url or self.settings.ollama_base_url
        self.timeout = self.settings.ollama_timeout

        # Skip connection test to avoid hanging
        logger.info(f"OllamaAnalyzer initialized with model: {self.model}")

    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment using Ollama local LLM"""
        try:
            prompt = f"""Analyze the sentiment of the following text and respond with ONLY a JSON object in this exact format:
{{"label": "positive|negative|neutral", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

Text to analyze: "{text}"

Important:
- Respond ONLY with valid JSON
- Use exactly these labels: positive, negative, neutral
- Confidence should be between 0.0 and 1.0
- Keep reasoning brief (max 50 words)"""

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 200
                }
            )

            # Extract response content
            content = response['message']['content'].strip()

            # Try to parse JSON response
            import json
            try:
                # Clean up the response (remove any markdown formatting)
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()

                result = json.loads(content)

                # Validate the result
                if 'label' not in result or 'confidence' not in result:
                    raise ValueError("Missing required fields in response")

                # Normalize label
                label = result['label'].lower()
                if label not in ['positive', 'negative', 'neutral']:
                    raise ValueError(f"Invalid label: {label}")

                confidence = float(result['confidence'])
                if not 0.0 <= confidence <= 1.0:
                    confidence = max(0.0, min(1.0, confidence))

                return SentimentResult(
                    label=SentimentLabel(label),
                    confidence=confidence,
                    scores={"ollama_confidence": confidence},
                    reasoning=result.get("reasoning", f"Ollama {self.model} analysis")
                )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse Ollama response: {e}. Raw response: {content}")

                # Fallback: simple keyword-based analysis
                text_lower = text.lower()
                positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'wonderful', 'fantastic', 'perfect']
                negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'worst', 'disgusting', 'annoying']

                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)

                if positive_count > negative_count:
                    label = SentimentLabel.POSITIVE
                    confidence = min(0.7, 0.3 + positive_count * 0.1)
                elif negative_count > positive_count:
                    label = SentimentLabel.NEGATIVE
                    confidence = min(0.7, 0.3 + negative_count * 0.1)
                else:
                    label = SentimentLabel.NEUTRAL
                    confidence = 0.3

                return SentimentResult(
                    label=label,
                    confidence=confidence,
                    scores={"fallback_analysis": True},
                    reasoning=f"Ollama parsing failed, used fallback analysis: {str(e)}"
                )

        except Exception as e:
            logger.error(f"Ollama analysis error: {e}")
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                scores={},
                reasoning=f"Error in Ollama analysis: {str(e)}"
            )


class HybridAnalyzer(SentimentAnalyzer):
    """Hybrid sentiment analyzer combining multiple approaches"""

    def __init__(
        self,
        use_openai: bool = False,
        use_ollama: bool = True,
        openai_api_key: Optional[str] = None,
        ollama_model: Optional[str] = None
    ):
        self.textblob = TextBlobAnalyzer()
        self.vader = VaderAnalyzer()
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.use_ollama = use_ollama and OLLAMA_AVAILABLE

        if self.use_openai:
            try:
                self.openai = OpenAIAnalyzer(openai_api_key)
            except (ImportError, ValueError) as e:
                logger.warning(f"OpenAI analyzer not available: {e}")
                self.use_openai = False

        if self.use_ollama:
            try:
                self.ollama = OllamaAnalyzer(model=ollama_model)
            except (ImportError, Exception) as e:
                logger.warning(f"Ollama analyzer not available: {e}")
                self.use_ollama = False

    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment using hybrid approach"""
        try:
            # Get results from different analyzers
            textblob_result = self.textblob.analyze(text)
            vader_result = self.vader.analyze(text)

            results = [textblob_result, vader_result]
            analyzer_names = ["textblob", "vader"]

            if self.use_ollama:
                ollama_result = self.ollama.analyze(text)
                results.append(ollama_result)
                analyzer_names.append("ollama")

            if self.use_openai:
                openai_result = self.openai.analyze(text)
                results.append(openai_result)
                analyzer_names.append("openai")

            # Combine results using weighted average
            num_analyzers = len(results)
            if num_analyzers == 2:  # textblob + vader
                weights = [0.4, 0.6]
            elif num_analyzers == 3:  # textblob + vader + (ollama or openai)
                weights = [0.2, 0.3, 0.5]
            elif num_analyzers == 4:  # textblob + vader + ollama + openai
                weights = [0.15, 0.25, 0.35, 0.25]
            else:
                weights = [1.0 / num_analyzers] * num_analyzers

            # Calculate weighted sentiment scores
            sentiment_scores = {"positive": 0, "neutral": 0, "negative": 0}
            total_confidence = 0

            for i, result in enumerate(results):
                weight = weights[i]
                total_confidence += result.confidence * weight

                if result.label == SentimentLabel.POSITIVE:
                    sentiment_scores["positive"] += weight
                elif result.label == SentimentLabel.NEGATIVE:
                    sentiment_scores["negative"] += weight
                else:
                    sentiment_scores["neutral"] += weight

            # Determine final label
            final_label = max(sentiment_scores, key=sentiment_scores.get)
            final_confidence = min(total_confidence, 1.0)

            # Combine all scores
            combined_scores = {}
            for i, result in enumerate(results):
                analyzer_name = analyzer_names[i]
                # Handle both enum and string labels
                label_value = result.label.value if hasattr(result.label, 'value') else str(result.label)
                combined_scores[f"{analyzer_name}_label"] = label_value
                combined_scores[f"{analyzer_name}_confidence"] = result.confidence
                combined_scores.update({f"{analyzer_name}_{k}": v for k, v in result.scores.items()})

            # Create reasoning
            reasoning_parts = []
            for i, result in enumerate(results):
                analyzer_display_name = analyzer_names[i].title()
                # Handle both enum and string labels
                label_str = result.label.value if hasattr(result.label, 'value') else str(result.label)
                reasoning_parts.append(f"{analyzer_display_name}: {label_str} ({result.confidence:.3f})")
            reasoning = f"Hybrid analysis - {', '.join(reasoning_parts)} -> Final: {final_label}"

            return SentimentResult(
                label=SentimentLabel(final_label),
                confidence=final_confidence,
                scores=combined_scores,
                reasoning=reasoning
            )
        except Exception as e:
            logger.error(f"Hybrid analysis error: {e}")
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                scores={},
                reasoning=f"Error in hybrid analysis: {str(e)}"
            )


def get_sentiment_analyzer(model_type: str = "hybrid", **kwargs) -> SentimentAnalyzer:
    """Factory function to get sentiment analyzer"""
    if model_type == "textblob":
        return TextBlobAnalyzer()
    elif model_type == "vader":
        return VaderAnalyzer()
    elif model_type == "openai":
        # Filter kwargs for OpenAI
        openai_kwargs = {k: v for k, v in kwargs.items() if k in ['openai_api_key']}
        return OpenAIAnalyzer(**openai_kwargs)
    elif model_type == "ollama":
        # Filter kwargs for Ollama
        ollama_kwargs = {k: v for k, v in kwargs.items() if k in ['model', 'base_url', 'ollama_model']}
        # Map ollama_model to model if provided
        if 'ollama_model' in ollama_kwargs:
            ollama_kwargs['model'] = ollama_kwargs.pop('ollama_model')
        return OllamaAnalyzer(**ollama_kwargs)
    elif model_type == "hybrid":
        # Filter kwargs for Hybrid
        hybrid_kwargs = {k: v for k, v in kwargs.items() if k in ['use_openai', 'use_ollama', 'openai_api_key', 'ollama_model']}
        return HybridAnalyzer(**hybrid_kwargs)
    else:
        raise ValueError(f"Unknown sentiment analyzer type: {model_type}")
