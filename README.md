# JSONL Dataset Editor for AI

A simple, user-friendly desktop application for creating and editing JSONL (JSON Lines) files, specifically designed for preparing datasets for AI model fine-tuning.

This tool provides a graphical interface to easily manage datasets that follow the common `instruction`, `input`, `output` format, while also offering powerful features like duplicate detection, undo/redo, and theme switching.

*(A sample screenshot showing the application's interface)*

## Key Features

*   **Graphical User Interface:** No more error-prone manual editing in a text editor. See your dataset entries in a clear, organized list.
*   **Load, Edit, and Save:** Full support for creating new JSONL files from scratch or loading and modifying existing ones.
*   **Structured Editing:** Dedicated text fields for the `instruction`, `input`, and `output` keys, ensuring a consistent data structure.
*   **Duplicate Input Detection:** Automatically identifies and highlights entries with identical `input` fields, which is crucial for cleaning datasets and preventing training data contamination.
*   **Multi-Level Undo/Redo:** Made a mistake? Easily undo or redo actions like adding, deleting, or editing an entire item.
*   **Light & Dark Themes:** Switch between a light or dark theme for your comfort.
*   **Auto-Saving:** Changes are automatically saved to the file when you switch between items or lose focus from the window, minimizing data loss.
*   **Keyboard Shortcuts:** A full suite of keyboard shortcuts for common actions (New, Open, Save, Undo, etc.) to speed up your workflow.
*   **Zero Dependencies:** Runs out-of-the-box with a standard Python 3 installation. No external libraries are needed!

## The JSONL Data Format

This editor is optimized for a specific JSONL structure where each line is a JSON object containing three main keys:

*   `"instruction"`: A task or directive for the AI model.
*   `"input"`: The context or data the model should use to follow the instruction. This can be empty.
*   `"output"`: The desired response or completion from the model.

**Example `data.jsonl` file:**
```json
{"instruction": "Translate the following English text to French.", "input": "Hello, world!", "output": "Bonjour, le monde!"}
{"instruction": "Summarize the following text.", "input": "The quick brown fox jumps over the lazy dog. This sentence is famous because it contains all the letters of the English alphabet.", "output": "The provided text is a well-known pangram."}
{"instruction": "Generate a list of three popular dog breeds.", "input": "", "output": "1. Labrador Retriever\n2. German Shepherd\n3. Golden Retriever"}
```

### Getting Started

There are two ways to use this application:

#### 1\. Pre-built Application (Windows)

For the easiest use, a pre-built executable is available. No installation is required.

1.  Go to the dist folder.
    
2.  Run **jsonl\_editor.exe**.
    

#### 2\. Running from Source

If you have Python 3 installed, you can run the editor directly.

1.  Clone or download the repository.
    
2.  Generated bashpython jsonl\_editor.pycontent\_copydownload

