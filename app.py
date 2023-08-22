from flask import Flask, render_template_string, request
from textblob import TextBlob
from pytrends.request import TrendReq
import openai
import plotly.graph_objs as go
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)

# Set your OpenAI API key
api_key = "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"

# Initialize the OpenAI API client
openai.api_key = api_key

# Modify the Trend Analysis Function
def analyze_search_trends(keywords):
    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload(keywords, cat=0, timeframe='today 3-m', geo='', gprop='')
    trend_data = pytrends.interest_over_time()
    return trend_data



# Function to generate meta content descriptions with SEO instructions
def generate_meta_description(input_words, template_option):
    templates = {
        "default": "Generate a meta content description for a webpage about {} {}. "
                   "Include keywords for SEO optimization and make the description engaging and concise.",
        "creative": "Craft an engaging meta description for a webpage centered around {} {}. "
                    "Ensure the keywords are SEO-optimized and the description captivates the reader's attention."
    }

    template = templates.get(template_option, templates["default"])
    input_words_str = ", ".join(input_words)
    prompt = template.format(input_words_str, input_words_str)

    response = openai.Completion.create(
        engine="text-davinci-003",  # Choose the appropriate GPT model
        prompt=prompt,
        max_tokens=100,  # Control the length of the description
        temperature=0.6,  # Adjust the randomness of the output
        stop=None  # Allow the model to continue generating without a specific stop condition
    )

    meta_description = response.choices[0].text.strip()
    return meta_description

@app.route("/", methods=["GET", "POST"])
def index():
    meta_description = ""
    character_count = 0
    seo_keywords = ""
    sentiment_emoji = ""
    trend_chart_path = None
    trend_chart_data = None
    
    if request.method == "POST":
        input_words = request.form.get("input_words")
        template_option = request.form.get("template_option")
        
        if input_words:
            input_words = input_words.split(",")
            
            # Check if template option is selected, default to "default"
            template_option = template_option or "default"
            
            meta_description = generate_meta_description(input_words, template_option)
            
            # Calculate character count
            character_count = len(meta_description)
            
            # Suggest SEO keywords
            seo_keywords = ", ".join(input_words)
            
            # Auto capitalization and punctuation
            meta_description = meta_description.capitalize() + "."
            
            # Perform sentiment analysis
            sentiment_analysis = TextBlob(meta_description)
            sentiment_score = sentiment_analysis.sentiment.polarity

            # Define sentiment labels and corresponding emojis
            sentiment_labels = {
                "negative": "😔",
                "neutral": "😐",
                "positive": "😄"
            }

            # Determine sentiment label based on score
            if sentiment_score < -0.2:
                sentiment_label = "negative"
            elif sentiment_score > 0.2:
                sentiment_label = "positive"
            else:
                sentiment_label = "neutral"

            sentiment_emoji = sentiment_labels[sentiment_label]
            
            # Analyze search trends
            trend_data = analyze_search_trends(input_words)
            
            # Create a trend analysis chart
            trend_chart_path = create_trend_chart(trend_data, input_words)
    
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Meta Description Generator</title>
        <!-- Add Bootstrap CSS link -->
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="card">
                <div class="card-body">
                    <h1 class="card-title">Meta Description Generator</h1>
                    <form method="POST">
                        <div class="form-group">
                            <label for="input_words">Enter input words (comma-separated):</label>
                            <input type="text" class="form-control" name="input_words" id="input_words">
                        </div>
                        
                        <div class="form-group">
                            <label for="template_option">Select Template:</label>
                            <select class="form-control" name="template_option" id="template_option">
                                <option value="default">Default</option>
                                <option value="creative">Creative</option>
                            </select>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Generate Meta Description</button>
                    </form>
                    
                    {% if meta_description %}
                    <h2 class="mt-3">Generated Meta Description:</h2>
                    <p>{{ meta_description }}</p>
                    <p>Character Count: {{ character_count }}</p>
                    <p>SEO Keywords: {{ seo_keywords }}</p>
                    <p>Sentiment: {{ sentiment_emoji }}</p>
                    <h2 class="mt-3">Search Trend Analysis:</h2>
                    <img src="{{ url_for('static', filename=trend_chart_path) }}" alt="Search Trend Chart">

                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Add Bootstrap JS link here -->
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    """

    return render_template_string(template, meta_description=meta_description, character_count=character_count, seo_keywords=seo_keywords, sentiment_emoji=sentiment_emoji, trend_chart_path=trend_chart_path)

# Create Trend Analysis Chart
def create_trend_chart(trend_data, keywords):
    trend_df = pd.DataFrame(trend_data)
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=trend_df, x=trend_df.index, y=keywords[0], marker='o')
    plt.title('Search Trend Analysis')
    plt.xlabel('Date')
    plt.ylabel('Interest')
    plt.xticks(rotation=45)
    plt.tight_layout()

    trend_chart_path = 'trend_chart.png'  # Only the filename
    plt.savefig(f'static/{trend_chart_path}')  # Save in the "static" directory
    plt.close()

    return trend_chart_path


if __name__ == "__main__":
    app.run(debug=True)