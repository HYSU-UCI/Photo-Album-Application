from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/upload")
def upload():
    return render_template("upload.html")


@app.route("/tagedit")
def tagedit():
    return render_template("tagedit.html")
