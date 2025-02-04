# CV Format Standardizer

CV Format Standardizer is a Streamlit application that extracts and standardizes CV (curriculum vitae) content from various file formats (such as `.txt`, `.docx`, and `.pdf`). It leverages OpenAI's GPT-4 (via the LangChain and CrewAI frameworks) to process and reformat CV data into a consistent, easy-to-read markdown format and also generates a PDF with custom styling.

## Features

- **File Upload:** Supports CV file uploads in `.txt`, `.docx`, and `.pdf` formats.
- **Text Extraction:** Automatically extracts text from the uploaded file.
- **CV Processing:**
  - Uses a **Senior Researcher** agent to extract relevant sections and details.
  - Uses a **Senior Editor** agent to refine the output and remove redundancies.
- **Output Formats:**
  - Generates CV output in standardized markdown.
  - Converts markdown into a styled PDF, including a logo and the current date in the footer.
- **Interactive UI:** Built with Streamlit for an easy-to-use web interface.

## Installation

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/cv_format_standardizer.git
cd cv_format_standardizer
```

### 2. Create a Virtual Environment (Recommended)

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Install the required packages using `pip`. A sample `requirements.txt` might include:

```txt
streamlit
python-dotenv
markdown
python-docx
PyPDF2
weasyprint
langchain-openai
crewai
```

Install them with:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and add your OpenAI API key and an optional logo URL:

```env
OPENAI_API_KEY=your_openai_api_key_here
LOGO_URL=https://link_to_your_logo.png
```

> **Important:** Ensure `.env` is added to your `.gitignore` to prevent accidentally committing sensitive information.

## Usage

### Running the App

Start the Streamlit application by running:

```bash
streamlit run app.py
```

### How to Use

1. **Upload a CV File:**  
   Use the file uploader in the app to select a CV file in `.txt`, `.docx`, or `.pdf` format.

2. **Process the File:**  
   Click the **Process** button to extract and standardize the CV content using the defined agents and tasks.

3. **Edit and Download:**  
   The app displays the standardized CV in markdown. You can edit the content if needed and download the final version as a PDF.

## How It Works

- **Text Extraction:**  
  The function `extract_text_from_file` handles text extraction from various file formats.

- **PDF Generation:**  
  The function `markdown_to_pdf` converts markdown text to a PDF using `weasyprint` with custom CSS (including a logo and the current date).

- **Agents and Tasks:**  
  Two agents are defined:
  - **cv_transcriber:** Extracts relevant CV details.
  - **cv_editor:** Refines the markdown output.
  
  Tasks are defined to instruct each agent on how to process and standardize the CV data.

- **Interactive UI:**  
  The Streamlit interface allows users to upload files, process them, edit the output, and download the final PDF.

## Deployment

You can deploy this application to various platforms:

- **Streamlit Cloud:**  
  Push your code to GitHub and link your repository to [Streamlit Cloud](https://streamlit.io/cloud). Configure your secrets (environment variables) via the platform’s UI.
  
- **Heroku:**  
  Create a `Procfile` (e.g., `web: streamlit run app.py --server.port=$PORT`) and deploy the app to Heroku.

## Contributing

Contributions are welcome! Please open issues or submit pull requests if you have suggestions or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to OpenAI for GPT-4.
- Thanks to the developers of Streamlit, LangChain, and CrewAI.


