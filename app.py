from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, jsonify,send_from_directory
from data import Purifications
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import os
from colorExtractor import color_extract
from flask_wtf import Form

UPLOAD_FOLDER = './images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.debug = True

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'waterTester'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Initialze MYSQL

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('admin.html')


@app.route('/admin', methods = ['POST', 'GET'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM admin WHERE username = %s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if(password_candidate == password):
                app.logger.info('PASSWORD MATCHED.')
                return redirect(url_for('home'))
            else:
                error = 'Invalid login.'
                return render_template('admin.html', error = error)
        else:
            error = 'No such user.'
            return render_template('admin.html', error = error )

    return jsonify({'message':'Login Failed.'}) 

# def is_loggedIn(f):
#     @wraps(f)
#     def wrap(*args, **kwargs):
#         if 'logged_in' in session:
#             return f(*args, **kwargs)
#         else:
#             flash('Unauthorized, Please login', 'danger')
#             return redirect(url_for('/'))
#     return wrap


@app.route('/home', methods = ['GET', 'POST'])
def home(): 
    return render_template('home.html')

class RegisterForm(Form):
    fullname = StringField('fullname', [validators.Length(min=4, max=50)])
    username = StringField('username', [validators.Length(min=4, max=10)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message = 'Passwords donot match.')
        ])
    confirm = PasswordField("Confirm password") 
    
#Register
@app.route('/register', methods=['POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        fullname = request.get_json()['fullname']
        username = request.get_json()['username']
        password = sha256_crypt.encrypt(str(request.get_json()['password'])) #need to encrypt before submitting
        confirm = request.get_json()['confirm']
        phone_no =  request.get_json()['phone_no']
        street = request.get_json()['street']
        city = request.get_json()['city']

        #Create cursor

        cur = mysql.connection.cursor()  #use this cursor to execute commands

        #Execute query
        cur.execute("INSERT INTO users (fullname, username, password, phone_no, street, city) VALUES(%s, %s, %s, %s, %s, %s)", (fullname, username, password, phone_no, street, city))

        #commit to db

        mysql.connection.commit()

        #close connection 

        cur.close()

        data = {'message': 'success'}
        return jsonify(data), 201

    data = {'message': 'failed'}
    return jsonify(data), 200


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        # getting the form fields
        username = request.get_json()['username']
        password_candidate = request.get_json()['password']

        #create cursor 

        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #get stored hash
            data = cur.fetchone() #check the query, matches the first one it gets
            password = data['password']

            #compare the password
            if sha256_crypt.verify(password_candidate, password):
                #passed
                return jsonify(data)
            else:
                error = 'Invalid Login'
                return jsonify({'message':'Invalid login'}) 
            #closed connection
            cur.close()
        else:
            error = 'Username not found'
            return jsonify({'message':'User not found'})  

    return jsonify({'message':'Login Failed.'})   

#Uers
@app.route('/users')
def users():
    #Create cursor
    cur = mysql.connection.cursor()
    #get articles
    result = cur.execute("SELECT * FROM users")

    data = cur.fetchall()

    if result > 0:
        return render_template('users.html', users=data)
    else:
        msg = 'No user foung'
        return render_template('users.html', msg=msg)

    cur.close()


@app.route('/edit_user/<string:id>', methods=['POST','GET'])
def edit_user(id):
    #Create cursor
    cur = mysql.connection.cursor()
    #Get article by its id
    result = cur.execute('SELECT * FROM users WHERE id = %s', [id])

    users = cur.fetchone()

    form = UserForm(request.form)
    #Populate
    form.fullname.data = users['fullname']
    form.username.data = users['username']
    form.phone_no.data = users['phone_no']
    form.street.data = users['street']
    form.city.data = users['city']

    if request.method == 'POST' and form.validate():
        fullname = request.form['fullname']
        username = request.form['username']
        phone_no = request.form['phone_no']
        street = request.form['street']
        city = request.form['city']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE users SET fullname=%s, username=%s, phone_no=%s, street=%s, city=%s WHERE id = %s",(fullname, username, phone_no,street,city, id))

        mysql.connection.commit()

        cur.close()

        flash('User Updated.','success')

        return redirect(url_for('users'))

    return render_template('edit_user.html', form= form)

#Delete user
@app.route('/delete_user/<string:id>', methods=['POST'])
def delete_user(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM users WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close()

    flash('User deleted.','success')

    return redirect(url_for('users'))

#Purification articles
@app.route('/purifications')
def purifications():
    #Create cursor
    cur = mysql.connection.cursor()
    #get articles
    result = cur.execute("SELECT * FROM purification")

    purification = cur.fetchall()

    if result > 0:
        return render_template('purifications.html', purification=purification)
    else:
        msg = 'No articles foung'
        return render_template('purifications.html', msg=msg)

    cur.close()

#calling from app
@app.route('/purificationsList', methods=['GET'])
def purificationsList():
    cur = mysql.connection.cursor()
    #get articles
    result = cur.execute("SELECT * FROM purification")

    purification = cur.fetchall()

    return jsonify(purification)


#article form 
class ArticleForm(Form):
    title=StringField('Title', [validators.Length(min=1, max=100)])
    body = TextAreaField('Body',[validators.Length(min=30)])

@app.route('/add_article', methods = ['GET', 'POST'])
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO purification(title, body) VALUES (%s, %s)", (title, body))

        mysql.connection.commit()

        cur.close()

        flash('Post Added.','success')

        return redirect(url_for('purifications'))

    return render_template('add_article.html', form= form)

#Edit article
@app.route('/edit_article/<string:id>', methods = ['GET', 'POST'])
def edit_article(id):
    #Create cursor
    cur = mysql.connection.cursor()
    #Get article by its id
    result = cur.execute('SELECT * FROM purification WHERE id = %s', [id])

    article = cur.fetchone()

    form = ArticleForm(request.form)
    #Populate
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE purification SET title=%s, body=%s WHERE id = %s",(title, body, id))

        mysql.connection.commit()

        cur.close()

        flash('Post Updated.','success')

        return redirect(url_for('purifications'))

    return render_template('edit_article.html', form= form)

#Delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM purification WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Article deleted.','success')

    return redirect(url_for('purifications'))

 
#for app  
@app.route('/feedback/<int:id>', methods=['POST'])
def feedback(id):
    if request.method == 'POST':
        feedback = request.get_json()['feedback']
        posted_date = request.get_json()['posted_date']

        #Create cursor

        cur = mysql.connection.cursor()  #use this cursor to execute commands

        #Execute query
        cur.execute("INSERT INTO feedback(feedback, posted_date, user_id) VALUES(%s, %s, %s)", (feedback, posted_date, id))

        #commit to db

        mysql.connection.commit()

        #close connection 

        cur.close()

        data = {'message': 'success'}
        return jsonify(data), 201

    data = {'message': 'failed'}
    return jsonify(data), 200

#for admin
@app.route('/feedbacks', methods=['GET'])
def feedbacks():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT f.id as id, user_id, username, feedback, posted_date FROM feedback f JOIN users u ON u.id = f.user_id")

    feedback = cur.fetchall()

    if result > 0:
        return render_template('feedback.html', feedback=feedback)
    else:
        msg = 'No feedback found'
        return render_template('feedback.html', msg=msg)

    cur.close()

@app.route('/delete_feed/<string:id>', methods = ['POST'])
def delete_feed(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM feedback WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close() 

    flash('Feed deleted.','success')

    return redirect(url_for('feedbacks'))

# for app  
@app.route('/records/<int:id>', methods=['POST'])
def records(id):
    if request.method == 'POST':
        title = request.get_json()['title']
        hardness = request.get_json()['total_hardness']
        free_chlorine = request.get_json()['free_chlorine']
        iron = request.get_json()['iron']
        copper = request.get_json()['copper']
        lead = request.get_json()['lead']
        nitrate = request.get_json()['nitrate']
        nitrite = request.get_json()['nitrite']
        alkalinity = request.get_json()['total_alkalinity']
        ph = request.get_json()['ph']
        posted_on = request.get_json()['posted_on']

        #Create cursor

        cur = mysql.connection.cursor()  #use this cursor to execute commands

        #Execute query
        cur.execute("INSERT INTO records(title,hardness, free_chlorine, iron, copper, lead, nitrate, nitrite,alkalinity,ph,posted_on, user_id) VALUES(%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s)", (title,hardness, free_chlorine, iron, copper, lead, nitrate, nitrite,alkalinity,ph, posted_on, id))

        #commit to db

        mysql.connection.commit()

        #close connection 

        cur.close()

        data = {'message': 'success'}
        return jsonify(data), 201

    data = {'message': 'failed'}
    return jsonify(data), 200

#for admin
@app.route('/recordList', methods=['GET'])
def recordList():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT r.id as id, username, title,hardness, free_chlorine, iron, copper, lead, nitrate, nitrite,alkalinity,ph,posted_on FROM records r JOIN users u ON u.id = r.user_id")

    records = cur.fetchall()

    if result > 0:
        return render_template('records.html', records=records)
    else:
        msg = 'No record found'
        return render_template('records.html', msg=msg)

    cur.close()

@app.route('/delete_record/<int:id>', methods = ['POST'])
def delete_record(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM records WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close() 

    flash('Feed deleted.','success')

    return redirect(url_for('feedbacks'))

@app.route('/uploader', methods = ['GET', 'POST'])  
def upload_file():
    result = None
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],f.filename))
         
    # result = color_extract('./images/final.jpg')
    # print (result)
        return jsonify(result)
        #return 'file uploaded successfully'
    elif request.method == 'GET':
        result = color_extract('./images/image.png')
        return jsonify(result), 200
    else:
        return jsonify({'message': 'upload failed'}), 404

class ForgotForm(Form):
    email = EmailField('Email',
    [validators.DataRequired(), validators.Email()])

class PasswordResetForm(Form):
    current_password = PasswordField('Current Password',
        [validators.DataRequired(),
        validators.Length(min=4, max =80)])

def send_password_reset_email(email):
    password

@app.route('/forgotPassword', methods = ['GET', 'POST'])  
def forgotPassword():
    error = None
    message = None
    form = ForgotForm()
    if form.validate_on_submit():
        pass
    return render_template('forgotPassword.html', form=form, error=error, message=message)

@app.route('/logout')
def logout():
    session.clear();
    flash('You are now logged out.', 'success')
    return redirect(url_for('/'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(host='0.0.0.0')

