from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="spacescribe",
    version="0.1.0",
    author="SpaceScribe Team",
    author_email="info@spacescribe.io",
    description="A comprehensive YouTube video transcription platform with API, CLI, and MCP integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SpaceTrev/space-scribe",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "sqlalchemy>=2.0.25",
        "youtube-transcript-api>=0.6.2",
        "yt-dlp>=2024.1.7",
        "openai-whisper>=20231117",
        "spacy>=3.7.2",
        "click>=8.1.7",
        "rich>=13.7.0",
        "typer>=0.9.0",
        "celery>=5.3.6",
        "redis>=5.0.1",
        "pandas>=2.1.4",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "spacescribe=cli.main:app",
        ],
    },
)
