from app import create_app
from flask import Flask
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

    def create_app():
        app = Flask(__name__)
        app.config['DEBUG'] = True
