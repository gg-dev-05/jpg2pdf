from flask import Flask, request, Response
from flask_mysqldb import MySQL
import yaml
import requests
import json
from dbConfig import database_config
from jpg2pdf import make_pdfs
import os
import time

env = ""
global msg
msg = ""

app = Flask(__name__)

if env == "dev":
    dev = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
    pdf = dev['pdf_maker']
    merger = dev['pdf_merger']
    DATABASE_URL = dev['CLEARDB_DATABASE_URL']
    api_token = dev['token']

else:
    pdf = os.environ.get("pdf_maker")
    merger = os.environ.get("pdf_merger")
    DATABASE_URL = os.environ.get("CLEARDB_DATABASE_URL")
    api_token = os.environ.get("token")

user, password, host, db = database_config(DATABASE_URL)

# print(user, password, host, db)
app.config['MYSQL_HOST'] = host
app.config['MYSQL_USER'] = user
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = db

mysql = MySQL(app)
baseUrl = "https://api.telegram.org/bot{}".format(api_token)
baseUrlFile = "https://api.telegram.org/file/bot{}".format(api_token)

@app.route("/")
def go():
    return "Success"

@app.route("/test", methods=['POST', 'GET'])
def test():
    if request.method == "POST":
        data = request.get_json()
        print(data)
        
        userId = data['message']['from']['id']
        

        if 'text' in data['message'] and data['message']['text'] == "/start":
            text = "Starting Command for making pdfs"
            send_message(userId, text)

            createUser(userId)

            emptyTable(userId)

        elif 'text' in data['message'] and data['message']['text'] == '/help':
            send_message(userId, "<b>This bot is under development</b>. More info on github.com/gg-dev-05/jpg2pdf")

        elif 'document' in data['message']:
            fileId = data['message']['document']['file_id']
            p = requests.get(baseUrl+"/getFile?file_id={}".format(fileId))
            fileDetails = p.json()
            file_path = fileDetails['result']['file_path']
            link = baseUrlFile+"/{}".format(file_path)
            
            createUser(userId)
            
            newImage(link, userId)


        elif 'text' in data['message'] and data['message']['text'] == "/pdf":
            text = "Making pdfs of sent files"
            send_message(userId, text)

            
            createUser(userId)

            createFinalPdf(userId)
            
            # check if user exists in users table

            # if not present - Add to users table, create table user_userID and send_message("give me jpg files")

            # else for item in user_id:
            #           make_pdf(item)
            # Merge all created pdfs
            # send_message(merged_pdf_link)
        else:
            send_message(userId, "Sorry I was not able to catch what you meant!!")

        if env == "dev":
            return Response(msg, status=200)
        return Response('Ok', status=200)
    else:
        return "GET REQUEST"


def send_message(userId, message):
    print(baseUrl + "/sendMessage?chat_id={}&text={}".format(userId, message))
    if(env == "dev"):
        global msg
        msg += message + "\n"
    else:
        requests.get(baseUrl + "/sendMessage?chat_id={}&text={}&parse_mode=html".format(userId, message))

def createUser(userID):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    print(users)
    present = False
    for user in users:
        if(str(user[0]) == str(userID)):
            present = True
            send_message(userID, "You are already present in the database, GOOD!!")
            

    if(not present):
        cur.execute("INSERT INTO users VALUES('{}');".format(userID))  
        cur.execute("CREATE TABLE user_{}(image VARCHAR(2000));".format(userID))
        mysql.connection.commit()
        cur.close()
        send_message(userID, str(userID) + " inserted in the database")

def emptyTable(userID):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_{}".format(str(userID)))
    mysql.connection.commit()
    cur.close()
    send_message(userID, "Your table is cleared")

def newImage(link, userId):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_{} VALUES('{}');".format(str(userId), link))
    cur.connection.commit()
    cur.close()
    send_message(userId, "Here is a link to the sent image:" + str(link))

def createFinalPdf(userId):
    # Get all links from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT image FROM user_{}".format(str(userId)))
    links = cur.fetchall()

    print(links)
    send_message(userId, "All Ok Creating pdfs")
    if env == 'dev':
        print(make_pdfs(links, "dev"))
    else:
        print(make_pdfs(links))
    # Make pdf from the given links

if __name__ == "__main__":
    if env == "dev":
        app.run(debug=True)
    else:
        app.run()