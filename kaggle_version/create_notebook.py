import json
import os

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def create_notebook():
    # Read source files
    db_code = read_file('db_kaggle.py')
    medmon_code = read_file('medmon_kaggle.py')
    main_code = read_file('main_kaggle_headless.py')
    
    # Process imports in main_code
    # Remove imports of local modules since they will be in previous cells
    main_lines = main_code.split('\n')
    filtered_main_lines = []
    for line in main_lines:
        if 'import medmon_kaggle' in line or 'import db_kaggle' in line:
            continue
        # Replace module calls with direct calls
        line = line.replace('db.init_database', 'init_database')
        line = line.replace('db.add_keyword', 'add_keyword')
        line = line.replace('db.save_article', 'save_article')
        line = line.replace('db.save_scrape_history', 'save_scrape_history')
        line = line.replace('db.clear_all_articles', 'clear_all_articles')
        line = line.replace('medmon.scrape_google_news', 'scrape_google_news')
        line = line.replace('medmon.get_full_article', 'get_full_article')
        line = line.replace('medmon.analyze_sentiment', 'analyze_sentiment')
        line = line.replace('medmon.save_results', 'save_results')
        filtered_main_lines.append(line)
    
    cleaned_main_code = '\n'.join(filtered_main_lines)

    # Define cells
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# MedMon Kaggle Notebook\n",
                "This notebook contains the complete code for the MedMon scraper, capable of running headlessly on Kaggle.\n",
                "\n",
                "### Instructions:\n",
                "1. **Run Cell 1** to install dependencies.\n",
                "2. **Run Cell 2** to setup database functions.\n",
                "3. **Run Cell 3** to setup scraper functions.\n",
                "4. **Run Cell 4** to configure and START scraping."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "!pip install gnews newspaper3k googlenewsdecoder selenium transformers torch wordcloud matplotlib pandas lxml[html_clean]\n",
                "!apt-get update\n",
                "!apt-get install -y google-chrome-stable"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": db_code.splitlines(True)
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": medmon_code.splitlines(True)
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": cleaned_main_code.splitlines(True)
        }
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.10.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    with open('medmon_unified.ipynb', 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2)
    
    print("Notebook 'medmon_unified.ipynb' created successfully.")

if __name__ == "__main__":
    create_notebook()
