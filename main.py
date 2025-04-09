from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

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