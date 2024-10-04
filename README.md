# TinyGen

## Introduction

**TinyGen** is a lightweight service that generates code diffs based on a provided GitHub repository and a user-defined prompt. Leveraging FastAPI, OpenAI's language models, and Supabase for data storage, this tool offers a streamlined way to apply and review code modifications automatically.


## Features

- **Generate Code Diffs**: Provide a GitHub repository URL and a prompt to receive a unified diff representing the requested changes.
- **Reflection Mechanism**: Utilizes a two-step LLM process to ensure the relevance and accuracy of the generated changes.
- **Data Storage**: Stores all requests and responses in a Supabase database for logging and auditing purposes.
- **User-Friendly Interface**: Simple web interface to input data and view results with color-coded diffs.
- **Robust Error Handling**: Gracefully manages errors related to fetching repositories, API calls, and more.


## Technologies Used

- **Backend**:
  - [FastAPI](https://fastapi.tiangolo.com/)
  - [OpenAI API](https://beta.openai.com/docs/)
  - [Supabase](https://supabase.com/)
  - [Uvicorn](https://www.uvicorn.org/)
  - [GitPython](https://gitpython.readthedocs.io/)
  - [Requests](https://docs.python-requests.org/)

- **Frontend**:
  - HTML, CSS, JavaScript

- **Others**:
  - [dotenv](https://pypi.org/project/python-dotenv/) for environment variable management

---

## Setup and Installation

### Prerequisites

- **Python 3.8+**: Ensure you have Python installed. You can download it from [here](https://www.python.org/downloads/).
- **Git**: Required for cloning the repository. Install from [here](https://git-scm.com/downloads).
- **GitHub Account**: To provide access to public repositories.
- **OpenAI API Key**: Sign up and obtain an API key from [OpenAI](https://beta.openai.com/signup/).
- **Supabase Account**: Sign up at [Supabase](https://supabase.com/) and create a new project.

### Installation Steps

1. **Clone the Repository**

    ```bash
    git clone https://github.com/angelafeliciaa/TinyGen.git
    cd app
    ```

2. **Create a Virtual Environment**

    ```bash
    python3 -m venv venv
    ```

3. **Activate the Virtual Environment**

    - **On macOS/Linux**:

        ```bash
        source venv/bin/activate
        ```

    - **On Windows**:

        ```bash
        venv\Scripts\activate
        ```

4. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

---

## Configuration

1. **Environment Variables**

    Create a `.env` file in the root directory and add the following variables:

    ```env
    OPENAI_API_KEY=your_openai_api_key
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_key
    ```

    **Note**: Replace `your_openai_api_key`, `your_supabase_url`, and `your_supabase_key` with your actual credentials.

2. **Supabase Setup**

    - **Create a Table**: In your Supabase project, create a table named `tinygen_logs` with the following columns:
        - `id`: UUID (Primary Key)
        - `repo_url`: Text
        - `prompt`: Text
        - `diff`: Text
        - `created_at`: Timestamp (default to `now()`)

---

## Running the Application

1. **Start the FastAPI Server**

    ```bash
    python app/main.py
    ```

    The server will start at `http://0.0.0.0:8000`.

2. **Access the Frontend**

    Open your browser and navigate to `http://localhost:8000/` to access the web interface.

---

## API Documentation

### Endpoints

#### `GET /`

Serves the frontend HTML page.

- **URL**: `/`
- **Method**: `GET`
- **Success Response**:
  - **Code**: `200 OK`
  - **Content**: `index.html` file

#### `POST /generate`

Generates a unified diff based on the provided GitHub repository and prompt.

- **URL**: `/generate`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:

    ```json
    {
      "repoUrl": "https://github.com/owner/repo",
      "prompt": "Convert all JavaScript files to TypeScript."
    }
    ```

- **Success Response**:
  - **Code**: `200 OK`
  - **Content**:

    ```json
    {
      "diff": "Unified diff string..."
    }
    ```

- **Error Responses**:
  - **Code**: `500 Internal Server Error`
  - **Content**:

    ```json
    {
      "error": "Error message detailing what went wrong."
    }
    ```

#### `GET /fetch-content`

Fetches the content of a specified GitHub repository.

- **URL**: `/fetch-content`
- **Method**: `GET`
- **Query Parameters**:
  - `repo_url`: URL of the GitHub repository

- **Success Response**:
  - **Code**: `200 OK`
  - **Content**:

    ```json
    {
      "repo_content": {
        "file_path_1": "file content...",
        "file_path_2": "file content...",
        // ...
      }
    }
    ```

- **Error Responses**:
  - **Code**: `500 Internal Server Error`
  - **Content**:

    ```json
    {
      "error": "Error message detailing what went wrong."
    }
    ```

---

## Deployment

To make your API accessible online, you can deploy it to a cloud platform. Below are the steps to deploy on **Heroku**.

### Deploying to Heroku

1. **Sign Up & Install Heroku CLI**

    - **Sign Up**: Create an account at [Heroku](https://www.heroku.com/).
    - **Install CLI**: Follow the instructions [here](https://devcenter.heroku.com/articles/heroku-cli) to install the Heroku CLI.

2. **Prepare Your App for Deployment**

    - **Create a `Procfile`**: This file tells Heroku how to run your app.

        ```plaintext
        web: uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}
        ```

    - **Ensure `requirements.txt` is Up-to-Date**

        If you've added new dependencies, update the `requirements.txt`:

        ```bash
        pip freeze > requirements.txt
        ```

3. **Initialize Git Repository**

    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```

4. **Create Heroku App**

    ```bash
    heroku create your-app-name
    ```

    Replace `your-app-name` with your desired app name. If omitted, Heroku will generate a unique name.

5. **Set Environment Variables on Heroku**

    ```bash
    heroku config:set OPENAI_API_KEY=your_openai_api_key
    heroku config:set SUPABASE_URL=your_supabase_url
    heroku config:set SUPABASE_KEY=your_supabase_key
    ```

6. **Deploy to Heroku**

    ```bash
    git push heroku master
    ```

7. **Access Your Live API**

    Once deployed, Heroku provides a URL like `https://your-app-name.herokuapp.com/`. Use this URL to interact with your API.

**Note**: Free Heroku dynos sleep after periods of inactivity. For persistent uptime, consider upgrading to a paid plan or exploring other hosting providers.

---

## Supabase Integration

All interactions with the API are logged in Supabase for auditing and analysis. Here's how the integration works:

### Table Schema: `tinygen_logs`

| Column      | Type    | Description                                     |
|-------------|---------|-------------------------------------------------|
| `id`        | UUID    | Unique identifier (Primary Key)                 |
| `repo_url`  | Text    | URL of the GitHub repository                    |
| `prompt`    | Text    | User-provided prompt for code modification      |
| `diff`      | Text    | Generated unified diff                          |
| `created_at`| Timestamp | Timestamp of when the log was created         |

### Inserting Logs

When a `POST /generate` request is made, the following data is inserted into the `tinygen_logs` table:

- `repo_url`: The GitHub repository URL provided by the user.
- `prompt`: The prompt describing the desired changes.
- `diff`: The unified diff generated by the system.

This setup allows you to keep track of all requests and their corresponding outputs.

---

## Usage

1. **Access the Web Interface**

    Navigate to `http://localhost:8000/` (or your deployed URL) in your web browser.

2. **Generate a Diff**

    - **Repo URL**: Enter the URL of a public GitHub repository (e.g., `https://github.com/owner/repo`).
    - **Prompt**: Describe the changes you want to apply (e.g., `Convert all JavaScript files to TypeScript.`).
    - **Submit**: Click the "Generate Diff" button.

3. **View Results**

    The generated diff will appear in the "Result" section with additions highlighted in green and deletions in red.

