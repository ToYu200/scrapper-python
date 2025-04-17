from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import pymysql
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Настройки подключения к MySQL
DB_HOST = os.environ.get('DB_HOST', 'localhost')  # Хост базы данных
DB_USER = os.environ.get('DB_USER', 'root')       # Имя пользователя
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Geefsoig123!')   # Пароль пользователя
DB_NAME = os.environ.get('DB_NAME', 'webscrapper')  # Имя базы данных

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url VARCHAR(2048) NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
        conn.commit()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    html_content = ''

    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            flash("Пожалуйста, введите URL")
            return redirect(url_for('index'))

        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text

            # абсолютные пути для ресурсов
            soup = BeautifulSoup(html_content, 'html.parser')
            for tag in soup.find_all(['img', 'link', 'script']):
                attr = 'src' if tag.name in ['img', 'script'] else 'href'
                if tag.get(attr):
                    # преобразование относительных путей в абсолютные
                    tag[attr] = urljoin(url, tag[attr])
            html_content = str(soup)

            # сохранение HTML в файл
            with open("output.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            # Сохраняем в базу данных
            conn = get_db_connection()
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO scrape_history (url, timestamp) VALUES (%s, %s)",
                        (url, datetime.now())
                    )
                conn.commit()

        except requests.exceptions.RequestException as e:
            flash(f"Ошибка при запросе URL: {e}")
            return redirect(url_for('index'))

    return render_template('index.html', html_content=html_content)

@app.route('/download')
def download_html():
    file_path = "output.html"
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("Файл не найден.")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)