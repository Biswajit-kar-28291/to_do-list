import os
from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash 
app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/todo.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {  
    'pool_pre_ping': True,
    'pool_recycle': 300,
}


db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(
        db.String(200),
        nullable=False) 
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.id}>'


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user = db.relationship('User', backref=db.backref('todos', lazy=True))



with app.app_context():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Email and password are required", 400

        this_user = User.query.filter_by(email=email).first()

        if this_user and check_password_hash(this_user.password, password):
            return redirect(url_for('todo', id=this_user.id))
        elif this_user:
            return 'Incorrect password'
        else:
            return redirect(url_for('reg'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def reg():
    try:
        if request.method == "POST":
            name = request.form.get('name')
            email = request.form.get("email")
            password = request.form.get("password")
            a_password = request.form.get("a_password")

        
            if not all([name, email, password, a_password]):
                return "All fields are required", 400

            if password != a_password:
                return "Passwords do not match"

            
            this_user = User.query.filter_by(email=email).first()
            if this_user:
                return "Email already registered. Please login."

            hashed_password = generate_password_hash(password)
            user = User(email=email, password=hashed_password, name=name)
            db.session.add(user)
            db.session.commit()

            return redirect(url_for('todo', id=user.id))

        return render_template("reg.html")

    except Exception as e:
        print(f"REGISTER ERROR: {str(e)}")
        return f"Server Error: {str(e)}", 500


@app.route('/todo/<int:id>', methods=['GET', 'POST'])
def todo(id):
    try:
        this_user = User.query.get_or_404(id)
        all_todos = Todo.query.filter_by(user_id=id).all()

        # Calculate stats
        t_task = len(all_todos)
        c_count = sum(1 for t in all_todos if t.status == "complete")
        i_count = t_task - c_count
        per = int((c_count / t_task * 100)) if t_task > 0 else 0

        # Apply filters
        filter_by = request.args.get("filter", "all")
        if filter_by == "incomplete":
            all_todos = Todo.query.filter_by(user_id=id,
                                             status='incomplete').all()
        elif filter_by == "complete":
            all_todos = Todo.query.filter_by(user_id=id,
                                             status='complete').all()

        # Add new task
        if request.method == 'POST':
            date_str = request.form['date']
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            task = request.form['task']
            category = request.form['category']

            new_todo = Todo(date=date,
                            task=task,
                            category=category,
                            user_id=this_user.id,
                            status='incomplete')
            db.session.add(new_todo)
            db.session.commit()
            return redirect(url_for('todo', id=this_user.id))

        return render_template('todo.html',
                               name=this_user,
                               tasks=all_todos,
                               t_task=t_task,
                               c_count=c_count,
                               i_count=i_count,
                               per=per)

    except Exception as e:
        print(f"TODO ERROR: {str(e)}")
        return f"Server Error: {str(e)}", 500


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    try:
        task = Todo.query.get_or_404(id)
        user_id = task.user_id
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('todo', id=user_id))
    except Exception as e:
        print(f"DELETE ERROR: {str(e)}")
        return f"Server Error: {str(e)}", 500


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    try:
        task = Todo.query.get_or_404(id)

        if request.method == 'POST':
            date_str = request.form['date']
            task.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            task.category = request.form['category']
            task.task = request.form['task']
            db.session.commit()
            return redirect(url_for('todo', id=task.user_id))

        return render_template('update.html', value=task, name=task.user)
    except Exception as e:
        print(f"UPDATE ERROR: {str(e)}")
        return f"Server Error: {str(e)}", 500


@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    try:
        task = Todo.query.get_or_404(id)
        data = request.get_json()
        is_checked = data.get('read', False)

        task.status = "complete" if is_checked else "incomplete"
        db.session.commit()

        return jsonify({'status': 'success', 'new_status': task.status})
    except Exception as e:
        print(f"STATUS UPDATE ERROR: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/testdb')
def testdb():
    try:
        db.session.execute(text('SELECT 1'))
        return 'Database connection working!'
    except Exception as e:
        return f'Database connection failed: {str(e)}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
