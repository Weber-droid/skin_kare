import os
from flask import Flask, flash, request, jsonify, render_template, redirect, session, url_for
from forms import RegistrationForm, LoginForm
from flask_bcrypt import Bcrypt
import base64
import requests
from PIL import Image
import io
import numpy as np
from datetime import datetime
import sqlite3

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
bcrypt = Bcrypt(app)

DATABASE = 'users.db'

def create_user_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

create_user_table()




def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def is_skin_image(image):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    img_array = np.array(image)
    avg_color = np.mean(img_array, axis=(0, 1))
    skin_lower = np.array([120, 80, 60])
    skin_upper = np.array([240, 200, 180])
    return np.all(avg_color >= skin_lower) and np.all(avg_color <= skin_upper)

@app.route('/')
def index():
    #return render_template('index.html')
    username = session.get('username')
    if not username:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))
    return render_template('index.html', username=username)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
            conn.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'danger')
        finally:
            conn.close()

    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Check email and password.', 'danger')
            
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



















@app.route('/results')
def result():
    return render_template('results.html')

@app.route('/history')
def history():
    conn = sqlite3.connect('skin_kare.db')
    cursor = conn.cursor()
    cursor.execute('SELECT diagnosis, treatment, date FROM analyses ORDER BY date DESC')
    analyses = cursor.fetchall()
    conn.close()

    return render_template('historyPage.html', analyses=analyses)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    conn = sqlite3.connect('skin_kare.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM analyses')
    conn.commit()
    conn.close()

    return redirect(url_for('history'))


@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' in request.files:
        file = request.files['image']
        image = Image.open(file)
    else:
        img_data = request.form.get('image_base64').split(",")[1]
        image = Image.open(io.BytesIO(base64.b64decode(img_data)))

    if not is_skin_image(image):
        return jsonify({"error": "The uploaded image is not a skin image."}), 400

    image_base64 = encode_image_to_base64(image)

    prompt = """
    You are a professional dermatologist. Analyze this skin image and provide:
    1. The name of the skin condition
    2. A description
    3. Suggested remedies or treatments
    """

    result = call_openrouter_api(image_base64, prompt)
    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    analysis = result['choices'][0]['message']['content']
    condition_name = analysis.split('.')[0]
    treatment = "Moisturizers and corticosteroid creams"  
    date = datetime.now().strftime('%m/%d/%Y')

    save_analysis(condition_name, treatment, date)

    response_data = {
        "condition": condition_name,
        "analysis": analysis,
        "imageBase64": image_base64
    }

    return jsonify(response_data)

def call_openrouter_api(image_base64, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/llama-3.2-11b-vision-instruct:free",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_base64}}]}]
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def save_analysis(diagnosis, treatment, date):
    conn = sqlite3.connect('skin_kare.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO analyses (diagnosis, treatment, date) VALUES (?, ?, ?)', (diagnosis, treatment, date))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)