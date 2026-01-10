"""Trading-specific content extraction"""
import logging
import re
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


class TradingProcessor:
    """Extract trading-specific concepts from transcripts"""

    # Trading indicators
    INDICATORS = [
        # Moving averages
        "SMA",
        "EMA",
        "moving average",
        "exponential moving average",
        "simple moving average",
        # Oscillators
        "RSI",
        "relative strength index",
        "MACD",
        "stochastic",
        "CCI",
        "commodity channel index",
        # Bands and channels
        "bollinger bands",
        "keltner channel",
        "donchian channel",
        # Volume
        "volume",
        "OBV",
        "on balance volume",
        "VWAP",
        # Fibonacci
        "fibonacci",
        "fib",
        "retracement",
        # Pivot points
        "pivot point",
        "support",
        "resistance",
        # ATR
        "ATR",
        "average true range",
        # Other
        "ichimoku",
        "parabolic SAR",
    ]

    # Timeframes
    TIMEFRAMES = [
        "1 minute",
        "1min",
        "1m",
        "5 minute",
        "5min",
        "5m",
        "15 minute",
        "15min",
        "15m",
        "30 minute",
        "30min",
        "30m",
        "1 hour",
        "1h",
        "4 hour",
        "4h",
        "daily",
        "1d",
        "weekly",
        "1w",
        "monthly",
        "1M",
    ]

    # Instruments/Markets
    INSTRUMENTS = [
        "stocks",
        "stock",
        "equity",
        "equities",
        "forex",
        "FX",
        "currency",
        "crypto",
        "cryptocurrency",
        "bitcoin",
        "ethereum",
        "futures",
        "options",
        "commodities",
        "bonds",
        "ETF",
    ]

    # Strategies
    STRATEGIES = [
        "scalping",
        "day trading",
        "swing trading",
        "position trading",
        "trend following",
        "mean reversion",
        "breakout",
        "momentum",
        "arbitrage",
        "hedging",
        "grid trading",
        "martingale",
    ]

    # Chart patterns
    PATTERNS = [
        "head and shoulders",
        "double top",
        "double bottom",
        "triangle",
        "flag",
        "pennant",
        "wedge",
        "cup and handle",
        "channel",
        "trend line",
    ]

    # Risk management
    RISK_CONCEPTS = [
        "stop loss",
        "take profit",
        "risk reward",
        "position sizing",
        "risk management",
        "drawdown",
        "leverage",
        "margin",
    ]

    def __init__(self):
        """Initialize trading processor"""
        # Create comprehensive pattern list
        self.all_concepts = {
            "indicators": self.INDICATORS,
            "timeframes": self.TIMEFRAMES,
            "instruments": self.INSTRUMENTS,
            "strategies": self.STRATEGIES,
            "patterns": self.PATTERNS,
            "risk": self.RISK_CONCEPTS,
        }

    def process_trading_content(self, text: str) -> Dict[str, Any]:
        """
        Extract all trading-related concepts from text

        Args:
            text: Transcript text

        Returns:
            Dictionary with extracted trading concepts
        """
        text_lower = text.lower()

        result = {
            "indicators": self._extract_concepts(text_lower, self.INDICATORS),
            "timeframes": self._extract_concepts(text_lower, self.TIMEFRAMES),
            "instruments": self._extract_concepts(text_lower, self.INSTRUMENTS),
            "strategies": self._extract_concepts(text_lower, self.STRATEGIES),
            "patterns": self._extract_concepts(text_lower, self.PATTERNS),
            "risk_concepts": self._extract_concepts(text_lower, self.RISK_CONCEPTS),
            "price_levels": self._extract_price_levels(text),
            "percentages": self._extract_percentages(text),
            "is_trading_content": self._is_trading_content(text_lower),
        }

        # Calculate overall trading relevance score
        total_mentions = sum(
            c["mentions"]
            for category in [
                "indicators",
                "timeframes",
                "instruments",
                "strategies",
                "patterns",
                "risk_concepts",
            ]
            for c in result[category]
        )

        result["relevance_score"] = self._calculate_relevance(total_mentions, len(text.split()))

        return result

    def _extract_concepts(
        self, text_lower: str, concept_list: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract specific concepts from text

        Args:
            text_lower: Lowercase text
            concept_list: List of concepts to search for

        Returns:
            List of found concepts with counts
        """
        found = []

        for concept in concept_list:
            # Create word boundary pattern
            pattern = rf"\b{re.escape(concept.lower())}\b"
            matches = re.findall(pattern, text_lower)

            if matches:
                found.append(
                    {
                        "concept": concept,
                        "mentions": len(matches),
                        "normalized_name": concept.upper()
                        if len(concept) <= 5
                        else concept.title(),
                    }
                )

        # Sort by mentions (most common first)
        found.sort(key=lambda x: x["mentions"], reverse=True)

        return found

    def _extract_price_levels(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract price levels and targets from text

        Args:
            text: Text to analyze

        Returns:
            List of price levels with context
        """
        price_patterns = [
            r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)",  # $1,000.00
            r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)",  # 1000 dollars
            r"price\s+(?:of\s+)?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # price of 1000
            r"target\s+(?:of\s+)?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # target 1000
        ]

        price_levels = []

        for pattern in price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get context (surrounding text)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()

                price_levels.append(
                    {"price": match.group(1), "context": context, "position": match.start()}
                )

        return price_levels

    def _extract_percentages(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract percentages (returns, moves, etc.)

        Args:
            text: Text to analyze

        Returns:
            List of percentages with context
        """
        # Pattern for percentages
        pattern = r"(\d+(?:\.\d+)?)\s*%"
        percentages = []

        matches = re.finditer(pattern, text)
        for match in matches:
            # Get context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()

            percentages.append(
                {
                    "value": float(match.group(1)),
                    "context": context,
                    "position": match.start(),
                }
            )

        return percentages

    def _is_trading_content(self, text_lower: str) -> bool:
        """
        Determine if content is trading-related

        Args:
            text_lower: Lowercase text

        Returns:
            True if trading content detected
        """
        # Check for trading keywords
        trading_keywords = [
            "trading",
            "trader",
            "market",
            "stock",
            "forex",
            "crypto",
            "investment",
            "buy",
            "sell",
            "chart",
            "technical analysis",
        ]

        matches = sum(1 for kw in trading_keywords if kw in text_lower)

        # If 3+ trading keywords found, likely trading content
        return matches >= 3

    def _calculate_relevance(self, total_mentions: int, total_words: int) -> float:
        """
        Calculate trading relevance score

        Args:
            total_mentions: Total trading concept mentions
            total_words: Total words in text

        Returns:
            Relevance score (0.0 to 1.0)
        """
        if total_words == 0:
            return 0.0

        # Calculate mention density
        density = total_mentions / total_words

        # Normalize to 0-1 scale (assume 10% density = max relevance)
        relevance = min(1.0, density * 10)

        return round(relevance, 3)

    def extract_trading_tags(self, text: str) -> List[Dict[str, Any]]:
        """
        Generate tags suitable for database storage

        Args:
            text: Transcript text

        Returns:
            List of tags with categories and confidence
        """
        analysis = self.process_trading_content(text)
        tags = []

        # Extract tags from each category
        for category, concepts in [
            ("indicator", analysis["indicators"]),
            ("timeframe", analysis["timeframes"]),
            ("instrument", analysis["instruments"]),
            ("strategy", analysis["strategies"]),
            ("pattern", analysis["patterns"]),
            ("risk", analysis["risk_concepts"]),
        ]:
            for concept in concepts[:10]:  # Top 10 from each category
                # Calculate confidence based on mentions
                confidence = min(1.0, concept["mentions"] / 10)

                tags.append(
                    {
                        "tag_name": concept["normalized_name"],
                        "tag_category": category,
                        "confidence_score": confidence,
                        "mentions": concept["mentions"],
                    }
                )

        return tags

    def get_trading_summary(self, text: str) -> Dict[str, Any]:
        """
        Get a concise summary of trading content

        Args:
            text: Transcript text

        Returns:
            Summary dictionary
        """
        analysis = self.process_trading_content(text)

        # Get top items from each category
        summary = {
            "is_trading_content": analysis["is_trading_content"],
            "relevance_score": analysis["relevance_score"],
            "top_indicators": [c["concept"] for c in analysis["indicators"][:3]],
            "top_timeframes": [c["concept"] for c in analysis["timeframes"][:3]],
            "top_instruments": [c["concept"] for c in analysis["instruments"][:3]],
            "top_strategies": [c["concept"] for c in analysis["strategies"][:3]],
            "price_levels_count": len(analysis["price_levels"]),
            "percentages_count": len(analysis["percentages"]),
        }

        return summary
