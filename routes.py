from flask import Flask, request, render_template, make_response, redirect, session, url_for, flash, send_file, abort
from flask_mysqldb import MySQL
from flask_session import Session
from irs import bm25_plus, sentence_embd
import numpy as np
import ast
import io
from pdf_scraping import PDF_scraper
from text_embedding import text_embed_string as embed
import time
import json
from datetime import datetime

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_test'

app.config['SECRET_KEY'] = 'secretkey'
app.config['SESSION_TYPE'] = 'filesystem'

mysql = MySQL(app)
Session(app)
search_log = {}

@app.route("/", methods=["POST", "GET"])
def homepage():
    if(request.method == "POST"):
        data = request.form.get('search')
        return make_response(redirect(url_for('result_page', search=data)))
    else:
        return render_template('homePage.html', files=fetchFiles())

def log_search(query, search_method, files, user_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    search_key = f"{user_id}_{timestamp}"

    search_log[search_key] = {
        "UserId": user_id,
        "Query": query,
        "SearchMethod": search_method,
        "Documents": {f"Document_{index+1}": {"name": file[1], "status": "Irrelevant"} for index, file in enumerate(files)}
    }

    return search_key

def update_document_status(search_key, doc_name):
    for key, value in search_log[search_key]["Documents"].items():
        doc_name = doc_name.replace("_", " ")
        value["name"] = value["name"].replace("_", " ")
        print("2")
        print(value["name"])
        print(doc_name)
        if value["name"] == doc_name:
            print("3")
            search_log[search_key]["Documents"][key]["status"] = "Relevant"
            break

@app.route("/result/sql", methods=["POST", "GET"])
def result_page():
    search = request.args.get('search')
    if request.method == "POST":
        search = request.form.get('search')

    user_id = session['user'][0] if 'user' in session else 'Anonymous'
    files, message = filter(search)
    
    # Log the search
    search_key = log_search(search, "SQL", files, user_id)

    if 'user' in session:
        return render_template('resultPage.html', files=files, user=session['user'], search=search, message=message, search_key=search_key)
    else:
        return render_template('resultPage.html', files=files, search=search, message=message, search_key=search_key)

@app.route("/result/irs", methods=["POST", "GET"])
def irs():
    start_time = time.time()

    cur = mysql.connection.cursor()
    cur.execute("SELECT file_id, file_content FROM ms_file")
    data = cur.fetchall()
    cur.close()

    search = request.args.get('search')
    if request.method == "POST":
        search = request.form.get('search')

    docs = calcTotal(search, data)
    
    ranked_files = []
    for doc_id, score in docs:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM ms_file WHERE file_id = %s", (doc_id,))
        file = cur.fetchone()
        cur.close()
        if file:
            file_id = file[0]
            original_filename = file[1]
            modified_filename = original_filename.replace('_', ' ')
            short_abstract = extract_short_abstract(file[2])
            ranked_files.append((file_id, modified_filename, short_abstract)) 

    end_time = time.time()
    time_taken = end_time - start_time

    file_message = "Found {:d} files".format(len(ranked_files))
    time_message = "in {:.4f} seconds using irs".format(time_taken)
    message = file_message + " " + time_message
    
    user_id = session['user'][0] if 'user' in session else 'Anonymous'
    
    # Log the search
    search_key = log_search(search, "IRS", ranked_files, user_id)

    if 'user' in session:
        return render_template('resultPage.html', files=ranked_files, user=session['user'], search=search, message=message, search_key=search_key)
    else:
        return render_template('resultPage.html', files=ranked_files, search=search, message=message, search_key=search_key)
        
def filter(query):
    start_time = time.time()
    
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM ms_file WHERE file_content LIKE '%{query}%'") #ubah file_name jadi file_content
    files = cur.fetchall()

    modified_files = [] #cleaning file_name with _ and extract abstract
    for file in files:
        file_id = file[0]  
        original_filename = file[1] 
        modified_filename = original_filename.replace('_', ' ')
        short_abstract = extract_short_abstract(file[2])
        modified_files.append((file_id, modified_filename, short_abstract))

    cur.close()

    end_time = time.time()
    time_taken = end_time - start_time

    file_message = "Found {:d} files".format(len(modified_files))
    time_message = "in {:.4f} seconds using query".format(time_taken)
    message = file_message + " " + time_message

    return modified_files, message

def extract_short_abstract(file_content):
    start_index = file_content.lower().find("abstract")

    if start_index >= 0:
        substring = file_content[start_index:start_index+300].strip() + "..."
        return substring
    else:
        print("Abstract word not found.")  
        return ""

@app.route("/detail/<int:file_id>")
def detail(file_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ms_file WHERE file_id = %s", (file_id,))
    file = cur.fetchone()
    cur.close()

    # Update document relevance in search log
    search_key = request.args.get('search_key')
    if search_key and search_key in search_log:
        file_name = file[1].replace('_', ' ')
        update_document_status(search_key, file[1])
    
    return render_template('detailPage.html', file=file)

def fetchFiles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ms_file")
    files = cur.fetchall()

    modified_files = [] #cleaning file_name with _
    for file in files:
        file_id = file[0]  
        original_filename = file[1] 
        modified_filename = original_filename.replace('_', ' ')
        short_abstract = extract_short_abstract(file[2])
        modified_files.append((file_id, modified_filename, short_abstract))

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

# using bm25
def calcbm25(query,data, returnVal = False):
    corpus = [doc[1].lower().split(" ") for doc in data]
    bm25Score = [bm25_plus(query.lower().split(" "),row[1].lower().split(" "),corpus) for row in data]
    if returnVal:
        docs = sorted([(data[i][0],bm25Score[i]) for i in range(len(data))], key = lambda x: x[1], reverse=True)
        return docs
    else:
        return bm25Score

def formatVec(st):
    st = st.replace("[","").replace("]","")
    st = st.split("\n ")
    st = " ".join(st)
    array = np.array(np.fromstring(st, sep=' '),dtype=float)
    array = array.reshape(1,-1)
    return array

# using sentence embedding
def calcSentenceEmb(query, data, returnVal = False):
    cur = mysql.connection.cursor()
    cur.execute("SELECT file_content_vector FROM ms_file")
    vecs = cur.fetchall()
    datas = []
    for vec in vecs:
        datas.append(formatVec(vec[0]))
    datas = np.vstack(datas)
    sim_score = sentence_embd(query, datas)
    if returnVal:
        docs = sorted([(data[i][0],sim_score[i]) for i in range(len(data))], key = lambda x: x[1], reverse=True)
        print(docs)
        return docs
    else:
        return sim_score

# total calculation
def calcTotal(query, data):
    bm25_score = calcbm25(query,data)
    sentence_embd_score = calcSentenceEmb(query, data)
    scores = [bm25_score[i] * sentence_embd_score[i] for i in range(len(bm25_score))]
    docs = sorted([(data[i][0],scores[i]) for i in range(len(data))], key = lambda x: x[1], reverse=True)
    return docs

@app.route("/addArticle", methods=["POST", "GET"])
def addArticle():
    if(request.method == "POST"):
        title = request.form.get("articleTitleInput")
        fileI = request.files.get('articleFileInput').read()    
        return ValidateArticleInput(title, fileI)

    elif(request.method == "GET"):
        return render_template('addArticlePage.html')


def ValidateArticleInput(title, fileI):
    if not title or not fileI:
        flash('Both fields are required!', 'danger')
        return render_template('addArticlePage.html')
    else:
        file_info = processArticle(title, fileI)
        insertArticle(file_info)
        flash('Article successfully added!', 'success')
        return render_template('addArticlePage.html')

def processArticle(title, fileI):
    file_name = title.replace(" ", "_")
    file_data = fileI
    file_content = PDF_scraper.text_scraper(fileI).replace("\n", "")
    file_content_vector = embed([str(file_content)])

    return (file_name, file_data, file_content, file_content_vector)

def insertArticle(file_info):
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO ms_file (file_name, file_data, file_content, file_content_vector) VALUES (%s, %s, %s, %s)", 
        (file_info[0], file_info[1], file_info[2], file_info[3])
    )
    mysql.connection.commit()
    cur.close()
    return None

@app.route('/download/<int:file_id>')
def download(file_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT file_name, file_data FROM ms_file WHERE file_id = %s", (file_id,))
    result = cur.fetchone()
    cur.close()

    if result:
        file_name, file_data = result

        # Update document relevance in search log
        search_key = request.args.get('search_key')
        if search_key and search_key in search_log:
            update_document_status(search_key, file_name)

        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
            
        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=file_name, mimetype='application/pdf')
    else:
        abort(404)

@app.route("/save_log", methods=["GET"])
def save_log():
    with open('search_log.json', 'w') as f:
        json.dump(search_log, f)
    return "<p>Log saved successfully</p>"

if __name__ == "__main__":
    app.run(debug=True)