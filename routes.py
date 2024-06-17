from flask import Flask, request, render_template, make_response, redirect, session, url_for
from flask_mysqldb import MySQL
from flask_session import Session

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_test'

app.config['SECRET_KEY'] = 'secretkey'
app.config['SESSION_TYPE'] = 'filesystem'

mysql = MySQL(app)
Session(app)

@app.route("/", methods=["POST", "GET"])
def homepage():
    if(request.method == "POST"):
        data = request.form.get('search')
        return make_response(redirect(url_for('result_page', search=data)))
    else:
        return render_template('homePage.html', files=fetchFiles())

@app.route("/result", methods=["POST", "GET"])
def result_page():
    search = request.args.get('search')
    if request.method == "POST":
        search = request.form.get('search')

    if search == None:
        if 'user' in session:
            return render_template('resultPage.html', files=fetchFiles(), user=session['user'])
        else:
            return render_template('resultPage.html', files=fetchFiles(), search=search)
    else:
        if 'user' in session:
            return render_template('resultPage.html', files=filter(search), user=session['user'], search=search)
        else:
            return render_template('resultPage.html', files=filter(search), search=search)

def filter(query):
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM ms_file WHERE file_name LIKE '%{query}%'")
    files = cur.fetchall()

    modified_files = [] #cleaning file_name with _
    for file in files:
        file_id = file[0]  
        original_filename = file[1] 
        modified_filename = original_filename.replace('_', ' ')
        modified_files.append((file_id, modified_filename))

    cur.close()
    
    return modified_files

@app.route("/detail")
def detail_page():
    return render_template("detailPage.html")

def fetchFiles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ms_file")
    files = cur.fetchall()

    modified_files = [] #cleaning file_name with _
    for file in files:
        file_id = file[0]  
        original_filename = file[1] 
        modified_filename = original_filename.replace('_', ' ')
        modified_files.append((file_id, modified_filename))

    cur.close()
    return modified_files

def authed(user):
    response = make_response(redirect("/"))
    session['user'] = user
    return response


@app.route("/login", methods=["POST", "GET"])
def login():
    if(request.method == "POST"):
        data = request.form
        user = auth(data["usernim"], data["password"])
        if(user):
            return authed(user)
        else:
            return "<p>Login Failed</p>"
        
    elif(request.method == "GET"):
        return render_template('loginPage.html')
    else:
        return "<p>Login</p>"
    
def auth(nim, password):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ms_user WHERE UserNim = %s AND UserPassword = %s", (nim, password))
    data = cur.fetchone()
    cur.close()
    return data

@app.route("/logout")
def logout():
    response = make_response(redirect("/"))
    session.pop('user', None)
    return response