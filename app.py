from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import os
from anthropic import Anthropic
import time

app = Flask(__name__)

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

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
        .header {
            color: #ff6600;
            font-size: 13pt;
            margin-bottom: 15px;
        }
        .story {
            margin-bottom: 15px;
            line-height: 1.4;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
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
            font-size: 10pt;
        }
        .refresh:hover {
            background-color: #ff8533;
        }
        .tags {
            margin-top: 5px;
        }
        .tag {
            display: inline-block;
            background-color: #f0f0f0;
            color: #666;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 8pt;
            margin-right: 5px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <b>Hacker News Top Stories</b>
    </div>
    <a href="/" class="refresh">Refresh Stories</a>
    {% for story in stories %}
    <div class="story">
        <span class="number">{{ loop.index }}.</span>
        <a href="{{ story.url }}" class="title-link">{{ story.title }}</a>
        {% if story.source %}
        <span class="source"> ({{ story.source }})</span>
        {% endif %}
        {% if story.tags %}
        <div class="tags">
            {% for tag in story.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
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

def get_content_tags(title):
    try:
        # Create a prompt for Claude
        prompt = f"""Based on this article title: "{title}"
        Please generate exactly 5 short, relevant content tags (1-2 words each) that categorize what this article might be about.
        Return only the tags separated by commas, nothing else."""
        
        # Get Claude's response
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0.5,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Split the response into tags and clean them
        tags = [tag.strip() for tag in response.content[0].text.split(',')]
        return tags[:5]  # Ensure we only return 5 tags
        
    except Exception as e:
        print(f"Error getting tags: {str(e)}")
        return []

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
                        
                        title = main_link.text.strip()
                        # Get tags from Claude
                        tags = get_content_tags(title)
                        
                        story = {
                            'title': title,
                            'url': main_link['href'],
                            'source': source,
                            'tags': tags
                        }
                        stories.append(story)
                        # Add a small delay to avoid hitting API rate limits
                        time.sleep(0.5)
        
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