# Gym Member Retention App

This application simulates gym member data, builds a churn prediction model, and provides a Streamlit dashboard to visualize insights and identify at-risk users.

## Project Structure

- `auxiliar/auxiliar.py`: Contains functions for generating synthetic gym member data and engineering features.
- `src/churn_model.py`: Contains the machine learning model definition, training, evaluation, and prediction logic.
- `src/create_sample_data.py`: A script to generate and save sample user and visit data into the `data/` directory.
- `src/streamlit_app.py`: The Streamlit web application for the "Gym Churn Predictor Dashboard".
- `data/`: Directory to store generated CSV data (e.g., `user_information.csv`, `user_visits.csv`). This directory is ignored by Git.
- `output/`: Directory to store the trained churn prediction model (e.g., `churn_model.joblib`). This directory is ignored by Git.
- `notebooks/test_data_generation.ipynb`: Jupyter notebook for testing data generation and initial data exploration.
- `notebooks/churn_prediction_model.ipynb`: Jupyter notebook for in-depth model development, feature importance analysis, and comparison of churned vs. active users.
- `requirements.txt`: Lists all Python dependencies.
- `.gitignore`: Specifies files and directories to be ignored by Git.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd gym-member-retention-app
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Generate sample data:**
    This will create `user_information.csv` and `user_visits.csv` in the `data/` directory.
    ```bash
    python src/create_sample_data.py
    ```

## Running the Streamlit Application

After setting up the environment and generating data, you can run the Streamlit app:

1.  **Start the Streamlit app:**
    ```bash
    streamlit run src/streamlit_app.py
    ```

2.  **Access the application:**
    Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

### Login Credentials

-   **Username:** `admin`
-   **Password:** `admin123`

You can also register a new user from the sidebar.

## Jupyter Notebooks

To explore the data generation or model development in detail, you can run the Jupyter notebooks:

1.  **Start Jupyter (if not already running):**
    ```bash
    jupyter notebook
    ```

2.  **Navigate** to the `notebooks/` directory and open `test_data_generation.ipynb` or `churn_prediction_model.ipynb`.

