"""NLP processing for transcript analysis"""
import logging
from typing import List, Dict, Any, Optional, Set
import spacy
from collections import Counter
import re

logger = logging.getLogger(__name__)


class NLPProcessor:
    """Process transcripts with NLP to extract entities, concepts, and structure"""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NLP processor

        Args:
            model_name: spaCy model name
        """
        self.model_name = model_name
        self._nlp = None
        logger.info(f"Initialized NLP processor with model: {model_name}")

    @property
    def nlp(self):
        """Lazy load spaCy model"""
        if self._nlp is None:
            try:
                logger.info(f"Loading spaCy model: {self.model_name}")
                self._nlp = spacy.load(self.model_name)
                logger.info("spaCy model loaded successfully")
            except OSError:
                logger.error(
                    f"spaCy model '{self.model_name}' not found. "
                    f"Run: python -m spacy download {self.model_name}"
                )
                raise
        return self._nlp

    def process_transcript(self, text: str) -> Dict[str, Any]:
        """
        Process transcript text with full NLP pipeline

        Args:
            text: Transcript text

        Returns:
            Dictionary with extracted information
        """
        doc = self.nlp(text)

        return {
            "entities": self.extract_entities(doc),
            "keywords": self.extract_keywords(doc),
            "topics": self.extract_topics(doc),
            "summary_sentences": self.extract_key_sentences(doc, top_n=5),
            "statistics": {
                "total_tokens": len(doc),
                "total_sentences": len(list(doc.sents)),
                "unique_entities": len(set([ent.text for ent in doc.ents])),
            },
        }

    def extract_entities(self, doc) -> List[Dict[str, Any]]:
        """
        Extract named entities from document

        Args:
            doc: spaCy Doc object

        Returns:
            List of entities with type and context
        """
        entities = []
        seen = set()

        for ent in doc.ents:
            # Avoid duplicates
            key = (ent.text.lower(), ent.label_)
            if key in seen:
                continue
            seen.add(key)

            entities.append(
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "label_description": spacy.explain(ent.label_),
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                }
            )

        # Sort by frequency (most common first)
        entity_counter = Counter([e["text"] for e in entities])
        entities.sort(key=lambda x: entity_counter[x["text"]], reverse=True)

        return entities

    def extract_keywords(
        self, doc, top_n: int = 20, include_phrases: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract keywords and key phrases

        Args:
            doc: spaCy Doc object
            top_n: Number of keywords to return
            include_phrases: Include noun phrases

        Returns:
            List of keywords with scores
        """
        # Extract single-word keywords (nouns, proper nouns, adjectives)
        keywords = []
        for token in doc:
            if (
                token.pos_ in ["NOUN", "PROPN", "ADJ"]
                and not token.is_stop
                and not token.is_punct
                and len(token.text) > 2
            ):
                keywords.append(token.lemma_.lower())

        # Count frequencies
        keyword_freq = Counter(keywords)

        # Extract noun phrases if requested
        if include_phrases:
            for chunk in doc.noun_chunks:
                # Clean and normalize phrase
                phrase = " ".join(
                    [
                        token.lemma_.lower()
                        for token in chunk
                        if not token.is_stop and not token.is_punct
                    ]
                )
                if phrase and len(phrase.split()) > 1:
                    keyword_freq[phrase] += 1

        # Get top keywords
        top_keywords = [
            {"keyword": kw, "frequency": freq, "score": freq}
            for kw, freq in keyword_freq.most_common(top_n)
        ]

        return top_keywords

    def extract_topics(self, doc, min_confidence: float = 0.3) -> List[Dict[str, Any]]:
        """
        Extract main topics from document using simple heuristics

        Args:
            doc: spaCy Doc object
            min_confidence: Minimum confidence score

        Returns:
            List of topics with confidence scores
        """
        # Get noun phrases and entities
        topics = set()

        # From entities
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW"]:
                topics.add(ent.text)

        # From noun phrases (longer ones are usually better topics)
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:
                topics.add(chunk.text)

        # Score topics by frequency
        topic_freq = Counter()
        text_lower = doc.text.lower()

        for topic in topics:
            count = text_lower.count(topic.lower())
            if count > 1:  # Only include if mentioned multiple times
                topic_freq[topic] = count

        # Convert to list with confidence scores
        total_mentions = sum(topic_freq.values()) or 1
        topic_list = [
            {"topic": topic, "mentions": count, "confidence": count / total_mentions}
            for topic, count in topic_freq.most_common(10)
            if count / total_mentions >= min_confidence
        ]

        return topic_list

    def extract_key_sentences(self, doc, top_n: int = 5) -> List[str]:
        """
        Extract most important sentences (simple extractive summary)

        Args:
            doc: spaCy Doc object
            top_n: Number of sentences to extract

        Returns:
            List of key sentences
        """
        sentences = list(doc.sents)

        # Score sentences based on:
        # 1. Contains entities
        # 2. Contains keywords
        # 3. Length (not too short, not too long)
        sentence_scores = []

        for sent in sentences:
            score = 0

            # Entity bonus
            score += len(sent.ents) * 2

            # Keyword bonus (nouns, proper nouns)
            keywords = [
                token
                for token in sent
                if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop
            ]
            score += len(keywords)

            # Length penalty (prefer medium-length sentences)
            sent_len = len(sent)
            if 10 <= sent_len <= 30:
                score += 2
            elif sent_len < 5:
                score -= 2

            # Position bonus (first and last sentences often important)
            sent_idx = sentences.index(sent)
            if sent_idx == 0 or sent_idx == len(sentences) - 1:
                score += 1

            sentence_scores.append((sent.text.strip(), score))

        # Sort by score and return top N
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        return [sent for sent, score in sentence_scores[:top_n]]

    def tag_content(
        self, text: str, categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Automatically tag content based on categories

        Args:
            text: Transcript text
            categories: Optional list of category keywords to look for

        Returns:
            List of tags with confidence scores
        """
        doc = self.nlp(text)
        tags = []

        # Default categories if none provided
        if categories is None:
            categories = [
                "tutorial",
                "review",
                "analysis",
                "how-to",
                "guide",
                "beginner",
                "advanced",
                "strategy",
                "tips",
                "news",
            ]

        # Simple keyword-based tagging
        text_lower = text.lower()
        total_words = len(doc)

        for category in categories:
            pattern = rf"\b{category}\b"
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))

            if matches > 0:
                confidence = min(1.0, matches / (total_words / 100))
                tags.append(
                    {
                        "tag_name": category,
                        "tag_category": "auto_generated",
                        "confidence_score": confidence,
                        "mentions": matches,
                    }
                )

        # Sort by confidence
        tags.sort(key=lambda x: x["confidence_score"], reverse=True)

        return tags

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Simple sentiment analysis (positive/negative/neutral)

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result
        """
        # This is a very simple implementation
        # For production, consider using a dedicated sentiment model

        doc = self.nlp(text)

        # Count positive and negative words (simple approach)
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "awesome",
            "best",
            "love",
            "perfect",
            "fantastic",
            "wonderful",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "worst",
            "hate",
            "poor",
            "disappointing",
            "useless",
            "wrong",
            "fail",
        }

        pos_count = 0
        neg_count = 0

        for token in doc:
            word_lower = token.lemma_.lower()
            if word_lower in positive_words:
                pos_count += 1
            elif word_lower in negative_words:
                neg_count += 1

        total = pos_count + neg_count
        if total == 0:
            sentiment = "neutral"
            score = 0.0
        elif pos_count > neg_count:
            sentiment = "positive"
            score = (pos_count - neg_count) / total
        else:
            sentiment = "negative"
            score = -(neg_count - pos_count) / total

        return {
            "sentiment": sentiment,
            "score": score,
            "positive_words": pos_count,
            "negative_words": neg_count,
        }

    def extract_definitions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract definitions (patterns like "X is Y", "X means Y")

        Args:
            text: Text to analyze

        Returns:
            List of found definitions
        """
        doc = self.nlp(text)
        definitions = []

        # Pattern: "TERM is DEFINITION"
        for sent in doc.sents:
            sent_text = sent.text
            # Simple regex patterns
            patterns = [
                r"(\w+(?:\s+\w+)*)\s+is\s+(.+?)(?:\.|$)",
                r"(\w+(?:\s+\w+)*)\s+means\s+(.+?)(?:\.|$)",
                r"(\w+(?:\s+\w+)*)\s+refers to\s+(.+?)(?:\.|$)",
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, sent_text, re.IGNORECASE)
                for match in matches:
                    term = match.group(1).strip()
                    definition = match.group(2).strip()

                    # Filter out too short or too long
                    if 3 <= len(term.split()) <= 5 and 5 <= len(definition.split()) <= 30:
                        definitions.append(
                            {
                                "term": term,
                                "definition": definition,
                                "context": sent_text,
                            }
                        )

        return definitions
