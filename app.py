from flask import Flask
from models import main

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    main.main()


if __name__ == '__main__':
    app.run(debug=True)