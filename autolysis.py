# /// script
# requires-python=">=3.9"
# dependencies = [
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "seaborn",
#     "requests",
#     "openai",
#     "scikit-learn",
#     "tabulate",
#     "chardet",
#     "asyncio",
# ]
# ///


import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving plots
import matplotlib.pyplot as plt
import httpx
import chardet

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

def load_csv_data(file_path):
    """Load CSV data with encoding detection."""
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    
    with open(file_path, 'rb') as file_handle:
        encoding_result = chardet.detect(file_handle.read())
    detected_encoding = encoding_result['encoding']
    print(f"Detected file encoding: {detected_encoding}")
    
    try:
        return pd.read_csv(file_path, encoding=detected_encoding)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

def perform_data_analysis(data_frame):
    """Perform basic data analysis."""
    if data_frame.empty:
        print("Error: Dataset is empty.")
        sys.exit(1)
    
    numeric_data_frame = data_frame.select_dtypes(include=['number'])
    analysis_results = {
        'summary': data_frame.describe(include='all').to_dict(),
        'missing_values': data_frame.isnull().sum().to_dict(),
        'correlation': numeric_data_frame.corr().to_dict() if not numeric_data_frame.empty else {}
    }
    print("Data analysis complete.")
    return analysis_results

def create_visualizations(data_frame):
    """Generate and save visualizations."""
    sns.set(style="whitegrid")
    numeric_columns = data_frame.select_dtypes(include=['number']).columns

    if numeric_columns.empty:
        print("No numeric columns found for visualization.")
        return

    for numeric_column in numeric_columns:
        plt.figure()
        sns.histplot(data_frame[numeric_column].dropna(), kde=True)
        plt.title(f'Distribution of {numeric_column}')
        file_name = f'{numeric_column}_distribution.png'
        plt.savefig(file_name)
        print(f"Saved distribution plot: {file_name}")
        plt.close()

def generate_analysis_narrative(analysis_data):
    """Generate narrative using LLM."""
    token = os.getenv("AIPROXY_TOKEN")
    if not token:
        print("Error: AIPROXY_TOKEN environment variable is not set.")
        sys.exit(1)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    prompt_message = (
        f"Analyze the following dataset: "
        f"\nSummary Statistics: {analysis_data['summary']}"
        f"\nMissing Values: {analysis_data['missing_values']}"
        f"\nCorrelation Matrix: {analysis_data['correlation']}"
    )
    
    request_data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt_message}]
    }
    
    try:
        response = httpx.post(API_URL, headers=headers, json=request_data, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except httpx.HTTPStatusError as http_error:
        print(f"HTTP error occurred: {http_error}")
    except httpx.RequestError as request_error:
        print(f"Request error occurred: {request_error}")
    except Exception as general_error:
        print(f"An unexpected error occurred: {general_error}")
    return "Narrative generation failed due to an error."

def main_process(file_path):
    print("Starting autolysis process...")
    
    # Step 1: Load Data
    data_frame = load_csv_data(file_path)
    print(f"Dataset loaded successfully. Shape: {data_frame.shape}")
    
    # Step 2: Analyze Data
    print("Analyzing data...")
    analysis_data = perform_data_analysis(data_frame)
    
    # Step 3: Visualize Data
    print("Generating visualizations...")
    create_visualizations(data_frame)
    
    # Step 4: Generate Narrative
    print("Generating narrative...")
    narrative_output = generate_analysis_narrative(analysis_data)
    
    if narrative_output != "Narrative generation failed due to an error.":
        with open('README.md', 'w') as readme_file:
            readme_file.write(narrative_output)
        print("Narrative successfully written to README.md.")
    else:
        print("Narrative generation failed. Skipping README creation.")
    
    print("Autolysis process completed.")

if __name__ == "_main_":
    if len(sys.argv) != 2:

      print("Usage: python autolysis.py <file_path>")
      sys.exit(1)
    main_process(sys.argv[1])
    
