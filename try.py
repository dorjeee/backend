from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.debug = True

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'waterTester'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Initialze MYSQL

mysql = MySQL(app)


Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

#articles
@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

#single article
@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id =id)

#register user class
class RegisterForm(Form):
    name = StringField('Full Name', validators=[validators.input_required()])  
    username =  StringField('Username', [validators.Length(min=4, max=25 )])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message = 'Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    phone_no = StringField('Phone No', validators=[validators.input_required()]) 
    street = StringField('Street') 
    city = StringField('City', validators=[validators.input_required()]) 

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.headers['name']
#         username = request.headers['username']
#         password = sha256_crypt.encrypt(str(request.headers['password'])) #need to encrypt before submitting
#         phone_no = request.headers['phone_no']
#         street = request.headers['street']
#         city = request.headers['city']

#         #Create cursor

#         cur = mysql.connection.cursor()  #use this cursor to execute commands

#         #Execute query
#         cur.execute("INSERT INTO users (name, username, password, phone_no, street, city) VALUES(%s, %s, %s, %s, %s, %s)", (name, username, password, phone_no, street, city))

#         #commit to db

#         mysql.connection.commit()

#         #close connection 

#         cur.close()

#         data = {'name': 'nabin khadka'}
#         return jsonify(data)

#     data = {'msg': 'nhjgfdg'}
#     return jsonify(data), 200


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.name.data
        password = sha256_crypt.encrypt(str(form.password.data)) #need to encrypt before submitting
        phone_no = form.phone_no.data
        street = form.street.data
        city = form.city.data

        #Create cursor

        cur = mysql.connection.cursor()  #use this cursor to execute commands

        #Execute query
        cur.execute("INSERT INTO users (name, username, password, phone_no, street, city) VALUES(%s, %s, %s, %s, %s, %s)", (name, username, password, phone_no, street, city))

        #commit to db

        mysql.connection.commit()

        #close connection 

        cur.close()

        flash('You are now registered.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)   

#user login 

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        # getting the form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor 

        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #get stored hash
            data = cur.fetchone() #check the query, matches the first one it gets
            password = data['password']

            #compare the passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed
                session['logged_in']= True
                session['username'] = usernames

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)  
            #closed connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)    

    return render_template('login.html')    

#check if the user is logged in 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized. Pease login.', 'danger')
            return redirect(url_for('login'))
    return wrap        


#logout

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Dashboard 

@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run()