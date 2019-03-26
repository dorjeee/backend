from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, jsonify
from data import Purifications
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


@app.route('/')
def index():
    return render_template('home.html')

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

#User form 
class UserForm(Form):
    fullname = StringField('Fullname',[validators.Length(max=30)])
    username = StringField('Username',[validators.Length(max=30)])
    phone_no = StringField('Phone_no')
    street = StringField('Street',[validators.Length(max=30)])
    city = StringField('City',[validators.Length(max=30)])


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

@app.route('/purificationsList')
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


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        fullname = request.get_json()['fullname']
        username = request.get_json()['username']
        password = sha256_crypt.encrypt(str(request.get_json()['password'])) #need to encrypt before submitting
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
                return jsonify({'message':'verified'})
            else:
                error = 'Invalid Login'
                return jsonify({'message':'error'}) 
            #closed connection
            cur.close()
        else:
            error = 'Username not found'
            return jsonify(error)  

    return jsonify({'message':'Login Failed.'})   
 


if __name__ == '__main__':

    app.secret_key = 'secret123'
    app.run(host='0.0.0.0')





