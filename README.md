# 🤖BlogPosting Schema AI Architect  

This is a Streamlit web application designed to function as an AI agent that generates comprehensive `BlogPosting` schema (in JSON-LD format) for any given blog post URL.

### Features

-   **Modular Python Structure:** The code is organized into logical modules for extraction, analysis, and schema building.
-   **Web Scraping:** Uses `requests` and `BeautifulSoup` to fetch and parse HTML content from a URL.
-   **AI-Powered Content Analysis:** Leverages the Gemini API to analyze the blog post's text and generate relevant keywords.
-   **Secure API Key Handling:** Uses Streamlit's built-in secrets management for API keys.
-   **User-Friendly Interface:** A simple and clean UI built with Streamlit for easy interaction.
-   **Transparent Process:** Displays the extracted and analyzed data at each stage before generating the final schema.

### Project Structure

The project is composed of the following Python modules:

-   `app.py`: The main Streamlit application file that handles the UI and orchestrates the workflow.
-   `utils.py`: Contains helper functions for tasks like fetching URLs and parsing HTML.
-   `extractor.py`: Responsible for Stage 1 - extracting raw data (headline, author, images, etc.) from the webpage.
-   `analyzer.py`: Responsible for Stage 2 - performing content analysis, such as word count and AI-powered keyword generation.
-   `schema_builder.py`: Responsible for Stage 3 & 4 - assembling the final JSON-LD schema and formatting it for output.

### Setup and Installation

1.  **Prerequisites:**
    * Python 3.8+

2.  **Clone the repository or save all files** into a single directory.

3.  **Install dependencies:**
    ```bash
    pip install streamlit requests beautifulsoup4
    ```

### Configuration

To enable the AI-powered keyword generation, you need a Google Gemini API key.

1.  **Get your API Key:** Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to create your key.

2.  **Store the Key Securely:** Create a folder named `.streamlit` in your project's root directory. Inside it, create a file named `secrets.toml` and add your key in the following format:

    ```toml
    # .streamlit/secrets.toml

    [api_keys]
    gemini = "YOUR_API_KEY_HERE"
    ```

    The application is already configured to read the key from this file securely.

### How to Run the Application

1.  Open your terminal or command prompt.
2.  Navigate to the root directory of the project.
3.  Run the following command:

    ```bash
    streamlit run app.py
    ```

Your default web browser will open with the application running.

### How to Use the App

1.  Enter the full URL of the blog post you wish to analyze into the input field.
2.  Click the "Generate Schema" button.
3.  The application will show the data it extracts and analyzes in real-time.
4.  Once complete, the final, formatted `BlogPosting` schema will be displayed in a code box, ready for you to copy and use.
