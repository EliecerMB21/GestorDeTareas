import os
import base64
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

app = Flask(__name__)

# Configuración de base de datos
db_url = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'sslmode': 'require'}} if 'postgresql' in db_url else {}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    due_date = db.Column(db.String(10))
    is_completed = db.Column(db.Boolean, default=False)
    difficulty = db.Column(db.String(20), nullable=False)
    attachment = db.Column(db.LargeBinary)
    attachment_filename = db.Column(db.String(255))
    attachment_mime_type = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    tasks = Task.query.order_by(db.desc(Task.difficulty)).all()
    completed = Task.query.filter_by(is_completed=True).count()
    pending = Task.query.filter_by(is_completed=False).count()
    return render_template('index.html', tasks=tasks, completed=completed, pending=pending)

@app.route('/add', methods=['POST'])
def add_task():
    try:
        file = request.files.get('attachment')
        new_task = Task(
            title=request.form['title'],
            description=request.form['description'],
            due_date=request.form['due_date'],
            difficulty=request.form['difficulty'],
            attachment=file.read() if file else None,
            attachment_filename=file.filename if file else None,
            attachment_mime_type=file.content_type if file else None
        )
        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        print(f"Error: {str(e)}")
    return redirect(url_for('index'))

@app.route('/preview/<int:task_id>')
def preview_attachment(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        if not task.attachment:
            return "Archivo no encontrado", 404
            
        if task.attachment_mime_type.startswith('image/'):
            return f'<img src="data:{task.attachment_mime_type};base64,{base64.b64encode(task.attachment).decode()}" class="img-fluid">'
        
        elif task.attachment_mime_type == 'text/plain':
            return f'<pre class="bg-light p-3">{task.attachment.decode("utf-8", errors="replace")}</pre>'
        
        elif task.attachment_mime_type == 'application/pdf':
            return send_file(
                BytesIO(task.attachment),
                mimetype='application/pdf',
                download_name=task.attachment_filename
            )
        
        return "Vista previa no disponible"
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('index'))

@app.route('/download/<int:task_id>')
def download_attachment(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        if not task.attachment:
            return "Archivo no encontrado", 404
        return send_file(
            BytesIO(task.attachment),
            download_name=task.attachment_filename,
            as_attachment=True
        )
    except Exception as e:
        print(f"Error en descarga: {str(e)}")
        return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_task(id):
    try:
        db.session.delete(Task.query.get(id))
        db.session.commit()
    except Exception as e:
        print(f"Error: {str(e)}")
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>')
def toggle_task(id):
    try:
        task = Task.query.get(id)
        task.is_completed = not task.is_completed
        db.session.commit()
    except Exception as e:
        print(f"Error: {str(e)}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)