from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    due_date = db.Column(db.String(10))
    is_completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='Media')

# Crear la base de datos (ejecutar solo una vez)
with app.app_context():
    db.create_all()
    # Tarea de ejemplo
    db.session.add(Task(
        title="Ejemplo",
        description="Mi primera tarea",
        due_date=datetime.now().strftime("%Y-%m-%d"),
        priority="Alta"
    ))
    db.session.commit()

@app.route('/')
def index():
    tasks = Task.query.all()
    completed = Task.query.filter_by(is_completed=True).count()
    pending = Task.query.filter_by(is_completed=False).count()
    return render_template('index.html', tasks=tasks, completed=completed, pending=pending)

@app.route('/add', methods=['POST'])
def add_task():
    new_task = Task(
        title=request.form['title'],
        description=request.form['description'],
        due_date=request.form['due_date'],
        priority=request.form['priority']
    )
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>')
def toggle_task(id):
    task = Task.query.get(id)
    task.is_completed = not task.is_completed
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)