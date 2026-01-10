"""Tests for NLP processing"""
import pytest
from core.processor.nlp_processor import NLPProcessor
from core.processor.trading_processor import TradingProcessor


class TestNLPProcessor:
    """Test NLP processor"""

    @pytest.fixture
    def nlp_processor(self):
        """Create NLP processor instance"""
        return NLPProcessor()

    def test_extract_keywords(self, nlp_processor):
        """Test keyword extraction"""
        text = "Trading stocks is a great way to invest. Stocks and bonds are important."

        # Process with spaCy
        doc = nlp_processor.nlp(text)
        keywords = nlp_processor.extract_keywords(doc, top_n=10)

        assert len(keywords) > 0
        assert all("keyword" in kw for kw in keywords)
        assert all("frequency" in kw for kw in keywords)


class TestTradingProcessor:
    """Test trading processor"""

    @pytest.fixture
    def trading_processor(self):
        """Create trading processor instance"""
        return TradingProcessor()

    def test_extract_indicators(self, trading_processor):
        """Test indicator extraction"""
        text = "We use RSI and MACD indicators for this strategy."

        result = trading_processor.process_trading_content(text)

        assert result["is_trading_content"]
        assert len(result["indicators"]) > 0

        # Check if RSI and MACD are found
        indicator_names = [ind["concept"] for ind in result["indicators"]]
        assert any("RSI" in name or "rsi" in name.lower() for name in indicator_names)

    def test_extract_timeframes(self, trading_processor):
        """Test timeframe extraction"""
        text = "I trade on the 5 minute and daily timeframes."

        result = trading_processor.process_trading_content(text)

        assert len(result["timeframes"]) > 0

    def test_is_trading_content(self, trading_processor):
        """Test trading content detection"""
        trading_text = "Learn about forex trading, stocks, and market analysis."
        non_trading_text = "This is a cooking tutorial about making pasta."

        result1 = trading_processor.process_trading_content(trading_text)
        result2 = trading_processor.process_trading_content(non_trading_text)

        assert result1["is_trading_content"]
        assert not result2["is_trading_content"]

    def test_relevance_score(self, trading_processor):
        """Test relevance score calculation"""
        score = trading_processor._calculate_relevance(total_mentions=10, total_words=100)

        assert 0.0 <= score <= 1.0
