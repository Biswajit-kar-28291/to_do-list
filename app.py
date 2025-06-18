import os 
from flask import Flask, render_template, url_for,request,redirect,jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text

path= os.path.abspath(os.path.dirname(__file__))
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+ os.path.join(path, 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Fixed spelling
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')


db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    email=db.Column(db.String(100), nullable=False,unique=True)
    password=db.Column(db.String(100), nullable=False)
    name=db.Column(db.String(100),nullable=False)
    
    def __repr__(self):
        return f'<Trans {self.id}>'
    
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user = db.relationship('User', backref=db.backref('todos', lazy=True))


@app.route('/',methods=['GET','POST'])
def login():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]
        this_user=User.query.filter_by(email=email).first()
        if this_user:
            if password==this_user.password:
                return redirect(url_for('todo', id=this_user.id))

            else:
                return 'check'
        else:
            return "reg kror"

    return render_template('login.html')

@app.route('/register',methods=['GET','POST'])
def reg():
    if request.method=="POST":
        name=request.form['name']
        email=request.form["email"]
        password=request.form["password"]
        a_password=request.form["a_password"]
        this_user=User.query.filter_by(email=email).first()
        if this_user:
            return redirect(url_for('login'))
        else:
            if password==a_password:
                user=User(email=email, password=password,name=name)
                db.session.add(user)
                db.session.commit()
                return "added"
            else:
                return "add paswrid again"

    # return render_template('login.html')
    return render_template("reg.html")

@app.route('/todo/<int:id>',methods=['GET','POST'])
def todo(id):
    this_user=User.query.filter_by(id=id).first()
    all=Todo.query.filter_by(user_id=id).all()
    t_task=len(all)
    c_count=0
    i_count=0
    for i in all:
        if i.status=="complete":
            c_count+=1
        else:
            i_count+=1
    if t_task==0:
        per=0
    else:
        per=(c_count/t_task)*100
    # print(all)
    # =Todo.query.filter_by(user_id=id).first()
    # name=this_user.name

    filter_by = request.args.get("filter", "all")
    if filter_by == "incomplete":
        all = Todo.query.filter_by(user_id=id, status='incomplete').all()
        # print('all',all)
    elif filter_by == "complete":
        all = Todo.query.filter_by(user_id=id,status='complete').all()
        print("h"  ,len(all))
        # return 'hi'
    else:
        all = Todo.query.filter_by(user_id=id).all()

    if request.method=='POST':
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        task=request.form['task']
        category=request.form['category']
        a=Todo(date=date,task=task,category=category,user_id=this_user.id,status='incomplete')
        db.session.add(a)
        db.session.commit()
        return redirect(url_for('todo', id=this_user.id))


        
    return render_template('todo.html',name=this_user,tasks=all,t_task=t_task,c_count=c_count,i_count=i_count ,per=int(per))


@app.route('/delete/<int:id>',methods=['GET','POST'])
def delete(id):
    value=Todo.query.get_or_404(id)

    print(value)
    iid=value.user_id
    db.session.delete(value)
    db.session.commit()
    return redirect(url_for('todo',id=iid))


@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):
    value=Todo.query.get_or_404(id)
    # print(value)
    a=value.user_id
    

    if request.method=='POST':
        date_str = request.form['date']
        value.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        value.category=request.form['category']
        value.task=request.form['task']
        db.session.commit()
        # print(value.user_id)
        return redirect(url_for('todo', id=a))
    return render_template('update.html',value=value,name=value,tasks=Todo.query.filter_by(user_id=value.user_id).all())



@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    value=Todo.query.get_or_404(id)
    data = request.get_json()
    is_checked = data.get('read', False)
    if is_checked:
        value.status="complete"
        db.session.commit()
    else:
       value.status="incomplete"
       db.session.commit() 

    # Update your database here (pseudo-code)
    # db.update_status(is_checked)
    print('Checkbox checked:', is_checked,id)
    return jsonify({'status': 'success', 'new_status': value.status})


    







if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
