# Agent365 Frontend

A modern, user-friendly Streamlit frontend for the Agent365 AI Office File Editor.

## Features

- 📤 **File Upload**: Support for .docx, .xlsx, and .pptx files
- ✍️ **Natural Language Prompts**: Describe what you want to do with your file
- 🔄 **Real-time Processing**: See progress and get results
- 👁️ **File Preview**: Preview processed files before downloading
- 📥 **Download**: Download edited files with one click
- 📊 **History**: View your processing history in the sidebar
- ⚙️ **Configurable**: Customize backend URL and authentication

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. (Optional) Install preview libraries for better file previews:

```bash
pip install python-docx pandas openpyxl python-pptx
```

## Running the App

1. Make sure your FastAPI backend is running on `http://localhost:8000`

2. Start the Streamlit app:

```bash
streamlit run app.py
```

3. Open your browser to the URL shown in the terminal (usually `http://localhost:8501`)

## Configuration

### Environment Variables

You can set these environment variables before running:

- `BACKEND_URL`: Backend API endpoint (default: `http://localhost:8000/process`)
- `BACKEND_USERNAME`: Basic Auth username (default: `admin`)
- `BACKEND_PASSWORD`: Basic Auth password (default: `change-me`)

Or configure them directly in the sidebar when the app is running.

## Usage

1. **Upload a File**: Click "Choose an Office file" and select a .docx, .xlsx, or .pptx file
2. **Enter a Prompt**: Describe what you want to do with the file (e.g., "Add a summary table", "Update all dates to 2024")
3. **Process**: Click "🚀 Process File" and wait for processing
4. **Preview**: Review the processed file preview
5. **Download**: Click "⬇️ Download Edited File" to save the result

## Backend API Requirements

The frontend expects the backend to accept:

- **Method**: POST
- **Endpoint**: `/process` (configurable)
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: The uploaded Office file
  - `prompt`: Natural language description of the task
- **Authentication**: HTTP Basic Auth
- **Response**:
  - Success (200): File download with `X-Task-Summary` header
  - Error: JSON with `error` field

**Note**: If your backend currently expects JSON with `file_path`, you may need to update it to accept file uploads. The frontend sends files as multipart/form-data.

## File Preview

The app can preview processed files:

- **Word (.docx)**: Shows paragraphs and tables (requires `python-docx`)
- **Excel (.xlsx)**: Shows dataframes for all sheets (requires `pandas` and `openpyxl`)
- **PowerPoint (.pptx)**: Shows slide titles and text (requires `python-pptx`)

If preview libraries are not installed, you'll see a message with installation instructions.

## Troubleshooting

### Connection Errors

- Ensure the FastAPI backend is running
- Check the backend URL in the sidebar settings
- Verify network connectivity

### Authentication Errors

- Check username and password in sidebar settings
- Verify backend authentication configuration

### Preview Not Working

- Install the required preview libraries (see Installation)
- Some file types may not support preview

### Processing Timeout

- Large files or complex tasks may take longer
- The default timeout is 5 minutes
- Check backend logs for processing status

## Project Structure

```
frontend/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── assets/            # Optional assets (icons, CSS)
```

## License

Part of the Agent365 project.
