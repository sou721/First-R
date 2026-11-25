"""起動用スクリプト:  python app.py  →  http://127.0.0.1:5000"""

from koppen_quiz.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
