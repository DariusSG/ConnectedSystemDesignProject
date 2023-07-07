from ClientUI import app
from flask import render_template, request, jsonify


@app.route("/")
def home():
    return render_template("index.html")