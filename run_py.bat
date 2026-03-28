@echo off
cd /d "directory here"

:: Install or update required packages
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

:: Run the Python script
echo Starting the application...
streamlit run app.py

:: Keep the window open after the script finishes
pause