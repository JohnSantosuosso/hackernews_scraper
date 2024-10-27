from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

def ensure_templates_directory():
    os.makedirs('templates', exist_ok=True)

def create_template():
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Hacker News</title>
    <style>
        body {
            font-family: Verdana, Geneva, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f6f6ef;
        }
        .story {
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .title-link {
            color: #000;
            text-decoration: none;
        }
        .title-link:hover {
            text-decoration: underline;
        }
        .source {
            color: #828282;
            font-size: 8pt;
        }
        .number {
            color: #828282;
            font-size: 10pt;
            margin-right: 5px;
        }
        .refresh {
            display: inline-block;
            padding: 10px 20px;
            background-color: #ff6600;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .refresh:hover {
            background-color: #ff8533;
        }
    </style>
</head>
<body>
    <a href="/" class="refresh">Refresh Stories</a>
    {% for story in stories %}
    <div class="story">
        <span class="number">{{ loop.index }}.</span>
        <a href="{{ story.url }}" class="title-link">{{ story.title }}</a>
        {% if story.source %}
        <span class="source"> ({{ story.source }})</span>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>"""
    
    template_path = os.path.join('templates', 'index.html')
    with open(template_path, 'w') as f:
        f.write(template_content)

def extract_site_from_href(href):
    if href and 'from?site=' in href:
        return href.split('from?site=')[1].rstrip(')')
    return None

def scrape_hackernews():
    try:
        response = requests.get('https://news.ycombinator.com', timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        stories = []
        for tr in soup.find_all('tr', class_='athing'):
            title_td = tr.find_all('td', class_='title')[-1]
            
            if title_td:
                titleline = title_td.find('span', class_='titleline')
                if titleline:
                    main_link = titleline.find('a')
                    sitebit = titleline.find('span', class_='sitebit comhead')
                    
                    if main_link:
                        source = None
                        if sitebit:
                            source_link = sitebit.find('a')
                            if source_link and source_link.get('href'):
                                source = extract_site_from_href(source_link['href'])
                        
                        story = {
                            'title': main_link.text.strip(),
                            'url': main_link['href'],
                            'source': source
                        }
                        stories.append(story)
        
        return stories
        
    except Exception as e:
        print(f"Error fetching stories: {str(e)}")
        return []

@app.route('/')
def index():
    stories = scrape_hackernews()
    return render_template('index.html', stories=stories)

if __name__ == '__main__':
    ensure_templates_directory()
    create_template()
    app.run(debug=True)

