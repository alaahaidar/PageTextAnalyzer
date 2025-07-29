# Web Scraper Project

## Overview

This is a Python-based web scraping application that extracts visible text content from web pages and filters out Polish text content. The application identifies the language of text snippets and displays non-Polish text in an HTML table format. It now features both a command-line interface and a modern web interface with URL input field and "Check" button for easy analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Dual Interface Architecture
The application now features two interfaces:
1. **Command-line Interface** (`web_scraper.py`): Original single-file architecture for command-line usage
2. **Web Interface** (`app.py` + `templates/index.html`): Flask-based web application with modern UI

### Core Components
- **WebTextExtractor Class**: The main class that handles all web scraping and text processing functionality
- **Command-line Interface**: Simple argument parsing and user interaction in `web_scraper.py`
- **Web Application**: Flask server providing a user-friendly web interface with URL input field and "Check" button
- **Text Processing Pipeline**: Sequential processing of HTML content through parsing, extraction, language detection, and filtering

## Key Components

### Web Scraping Engine
- **HTTP Client**: Uses the `requests` library for fetching web pages
- **HTML Parser**: Leverages `BeautifulSoup4` for robust HTML parsing and DOM traversal
- **Content Extraction**: Targets specific HTML tags defined in `TEXT_TAGS` constant for comprehensive text extraction

### Language Detection System
- **Language Analyzer**: Integrates `langdetect` library for automatic language identification
- **Polish Filter**: Specifically designed to identify and exclude Polish language content
- **Deterministic Results**: Uses seeded random number generation for consistent language detection across runs

### Text Processing Pipeline
- **Content Cleaning**: Removes HTML comments, scripts, and style elements
- **Text Normalization**: Handles whitespace and formatting cleanup
- **Language Analysis**: Processes each text snippet for language identification
- **Filtering Logic**: Separates Polish from non-Polish content

## Data Flow

1. **Input Processing**: URL validation and normalization
2. **Content Retrieval**: HTTP request to fetch webpage content
3. **HTML Parsing**: BeautifulSoup processes the raw HTML
4. **Text Extraction**: Systematic extraction from predefined HTML tags
5. **Language Detection**: Each text snippet analyzed for language
6. **Content Filtering**: Polish content filtered out
7. **Output Generation**: Non-Polish text formatted into HTML table

## External Dependencies

### Core Libraries
- **requests**: HTTP client for web page fetching
- **beautifulsoup4**: HTML parsing and DOM manipulation
- **langdetect**: Language identification capabilities

### Python Standard Library
- **sys**: Command-line argument handling and system operations
- **re**: Regular expression support for text processing
- **html**: HTML entity encoding/decoding
- **urllib.parse**: URL parsing and validation
- **typing**: Type hints for better code documentation

## Deployment Strategy

### Standalone Script Deployment
The application is designed as a self-contained Python script that can be executed directly. This approach offers:

**Advantages:**
- Simple deployment (single file)
- No complex setup or configuration required
- Easy to distribute and run on different systems

**Requirements:**
- Python 3.x environment
- Manual dependency installation via pip
- Command-line access for execution

### Error Handling
- Graceful handling of missing dependencies with clear installation instructions
- URL validation and HTTP error management
- Language detection failure handling

### Usage Patterns
- Command-line execution with URL argument
- Interactive mode with URL prompting
- Suitable for both one-off analysis and batch processing scenarios

The architecture prioritizes simplicity and ease of use over scalability, making it ideal for research, content analysis, or educational purposes where quick text extraction and language filtering is needed.