# 🚀 Running MedMon on Kaggle (Headless Mode)

This guide explains how to run the MedMon scraper on Kaggle without any visual dashboard, as requested.




## Option 1: Unified Notebook (Recommended)
If you prefer a single file solution:
1. Upload `medmon_unified.ipynb` to Kaggle.
2. Open it as a Notebook.
3. Run the cells sequentially.
   - Cell 1: Installs dependencies.
   - Cell 2: Database setup.
   - Cell 3: Scraper setup.
   - Cell 4: Configuration and Main Execution (Edit keywords here).

## Option 2: Upload Files & Run Headless
1. **Upload Files**:
   - Upload the `kaggle_version` folder content (`main_kaggle_headless.py`, `medmon_kaggle.py`, `db_kaggle.py`, `requirements.txt`) to your Kaggle Notebook's working directory.
   - Or copy-paste the content of these files into notebook cells.

2. **Installation**:
   Run this cell to install the required libraries:
   ```python
   !pip install -r requirements.txt
   !pip install lxml[html_clean]
   !apt-get update && apt-get install -y google-chrome-stable
   ```

3. **Configuration & Running**:
   You can run the scraper by executing `main_kaggle_headless.py`. 
   You can edit the configuration directly in the file, or if you pasted it into a cell, edit the top section:


```python
# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
KEYWORDS = ["PT ASABRI", "Info Korupsi"]  # Edit your keywords here
SCRAPING_CONFIG = {
    "language": "id",
    "period": "7d",       # 7 days
    "max_results": 10,
    "workers": 5
}
RESET_DATABASE = False    # Set True to clear old data
# ==========================================
```

Run the script:
```python
!python main_kaggle_headless.py
```


## Option 3: Streamlit Dashboard (Visual UI)
If you want the visual dashboard:
1. Follow the "Upload Files" step from Option 2.
2. Install `pyngrok`.
3. Run:
   ```python
   # Authenticate ngrok first
   import os
   from pyngrok import ngrok
   ngrok.set_auth_token("YOUR_TOKEN")
   
   # Run app
   get_ipython().system_raw('streamlit run streamlit_kaggle.py --server.port 8501 &')
   
   # Connect
   import time
   time.sleep(3)
   public_url = ngrok.connect(8501).public_url
   print(f"Click here: {public_url}")
   ```

## Checking Results (For Headless/Unified Modes)
1. Look at the **Output** tab of your notebook.
2. Open the `output/` folder.
3. Download the generated `.csv` or `.json` files.
4. You can also download `medmon.db` to save the full database.
