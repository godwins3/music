from flask import Flask, session, Request,render_template
from models import main

app = Flask(__name__)

@app.route('/')
def index():
    main()


if __name__ == '__main__':
    app.run(debug=True)