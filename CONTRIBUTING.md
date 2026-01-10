# Contributing to SpaceScribe

Thank you for your interest in contributing to SpaceScribe! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/space-scribe.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to the branch: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/SpaceTrev/space-scribe.git
cd space-scribe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Download spaCy model
python -m spacy download en_core_web_sm

# Initialize database
spacescribe init

# Run tests
pytest
```

## Code Style

We follow PEP 8 style guidelines. Use these tools:

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_transcriber.py
```

## Pull Request Guidelines

1. **Title**: Use a clear, descriptive title
2. **Description**: Explain what changes you made and why
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update docs if needed
5. **Code Quality**: Ensure code passes linting and formatting checks

## Commit Message Format

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(transcriber): add support for playlist transcription

- Add playlist URL detection
- Implement batch processing for playlists
- Add progress tracking

Closes #123
```

## Areas for Contribution

### High Priority
- [ ] Celery background job processing
- [ ] WebSocket support for real-time progress
- [ ] Advanced NLP features (sentiment analysis, topic modeling)
- [ ] Performance optimizations
- [ ] Additional export formats
- [ ] Improved error handling

### Medium Priority
- [ ] Multi-language support improvements
- [ ] Better caching strategies
- [ ] API rate limiting
- [ ] User authentication and authorization
- [ ] Playlist processing improvements
- [ ] Better web interface

### Low Priority
- [ ] Additional trading indicators
- [ ] Custom chunking strategies
- [ ] Plugin system
- [ ] CLI improvements
- [ ] Documentation improvements

## Questions?

- Open an issue for bugs or feature requests
- Join our Discord: https://discord.gg/spacescribe
- Email: info@spacescribe.io

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
