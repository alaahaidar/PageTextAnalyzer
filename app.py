#!/usr/bin/env python3
"""
Web Interface for Non-Polish Text Extractor

A Flask web application that provides a user-friendly interface
for the web scraper functionality.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from web_scraper import WebTextExtractor
import tempfile

app = Flask(__name__)

@app.route('/')
def index():
    """Main page with URL input form."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_url():
    """Analyze URL and return results."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'Please enter a URL'}), 400
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Create extractor and process URL
        extractor = WebTextExtractor()
        html_output = extractor.process_url(url)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.html', 
            delete=False, 
            encoding='utf-8'
        )
        temp_file.write(html_output)
        temp_file.close()
        
        return jsonify({
            'success': True,
            'message': 'Analysis completed successfully!',
            'download_url': f'/download/{os.path.basename(temp_file.name)}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download the generated HTML file."""
    try:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name='non_polish_text_results.html',
                mimetype='text/html'
            )
        else:
            return "File not found", 404
            
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)