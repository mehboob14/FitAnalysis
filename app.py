import os
import asyncio
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from scraper.upd_1 import run_scrape_and_save
from scraper.upd_structure import run_structure
from AnalysisScripts.Script import run_fit_analysis

app = Flask(__name__)
app.secret_key = 'testkey'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/performAnalysis', methods=['POST'])
def performAnalysis():
    url = request.form.get('url')
    front_image = request.files.get('front_image')
    side_image = request.files.get('side_image')

    if not url or not front_image or not side_image:
        flash("All fields are required!")
        return redirect(url_for('index'))

    front_filename = secure_filename(front_image.filename)
    side_filename = secure_filename(side_image.filename)
    front_path = os.path.join(app.config['UPLOAD_FOLDER'], front_filename)
    side_path = os.path.join(app.config['UPLOAD_FOLDER'], side_filename)
    front_image.save(front_path)
    side_image.save(side_path)

    run_scrape_and_save(url)

    run_structure()

    analysis_result = run_fit_analysis(front_path, side_path)

    return render_template('result.html', result=analysis_result)

if __name__ == '__main__':
    app.run(debug=True)
