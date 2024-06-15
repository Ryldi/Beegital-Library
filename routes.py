from flask import Flask, request, render_template, make_response, redirect, session
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

@app.route("/")
def homepage():
    if 'user' in session:
        return render_template('homePage.html', files=fetchFiles(), user=session['user'])
    return render_template('homePage.html', files=fetchFiles())

@app.route("/result")
def result_page():
    return render_template("resultPage.html")

@app.route("/detail")
def detail_page():
    return render_template("detailPage.html")

def fetchFiles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ms_file")
    files = cur.fetchall()
    cur.close()
    return files

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