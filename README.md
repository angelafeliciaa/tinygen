# TinyGen

TinyGen is a tool for generating diffs based on natural language descriptions.

## Live Demo

A live demo of TinyGen is available at [https://tinygen-31646a1cc468.herokuapp.com](https://tinygen-31646a1cc468.herokuapp.com).

## Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/tinygen.git
   cd tinygen
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

5. Open `http://localhost:8000` in your browser to use the application.

## Usage

Enter a natural language description of the changes you want to make to your code, and TinyGen will generate the corresponding diff.

## Technologies Used

- FastAPI
- OpenAI API
- Supabase

---
