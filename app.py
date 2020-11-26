from flask import Flask, request, Response
from flask_mysqldb import MySQL
import yaml
import requests
import json
from dbConfig import database_config
import os

env = ""

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

print(user, password, host, db)
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
        return Response('Ok', status=200)
    else:
        return "GET REQUEST"
    
@app.route("/start")
def start():    
    r = requests.get(baseUrl+"/getUpdates")
    # print(baseUrl+"/getUpdates")
    data = r.json()
    # print(data)
    for i in data['result']:
        id = i['message']['from']['id']
        offset_value = i['update_id']
        createUser(id, offset_value)

        if 'text' in i['message'] and i['message']['text'] == "/start":
            removeAllOldImages(id,offset_value)
        if 'document' in i['message']:
            fileId = i['message']['document']['file_id']
            p = requests.get(baseUrl+"/getFile?file_id={}".format(fileId))
            fileDetails = p.json()
            file_path = fileDetails['result']['file_path']
            link = baseUrlFile+"/{}".format(file_path)
            newImage(link, id)
        if 'text' in i['message'] and i['message']['text'] == "/pdf":
            link = make_pdfs(id)
            return link

    return "Success"


def createUser(userID, offset_value):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    present = False
    for user in users:
        if(str(user[0]) == str(userID)):
            present = True
            print("Already Present")
            break

    if(not present):
        cur.execute("INSERT INTO users VALUES('{}', '{}');".format(userID, offset_value))  
        cur.execute("CREATE TABLE user_{}(image VARCHAR(2000));".format(userID))
        mysql.connection.commit()
        cur.close()
        print("user_", userID, " inserted to users and table created")

def newImage(link, userId):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_{} VALUES('{}');".format(userId, link))
    cur.connection.commit()
    cur.close()
    print(link, "added to user_", userId)

def removeAllOldImages(userId, offset_value):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_{}".format(userId))
    cur.execute("UPDATE users SET offset_value='{}' where userId = '{}';".format(offset_value, userId))
    cur.connection.commit()
    cur.close()
    print("Old Images removed")

def make_pdfs(userId):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user_{}".format(userId))
    links = cur.fetchall()

    
    pdf_links = []
    for i in links:
        data = '{"Parameters": [{"Name": "File","FileValue": {"Url":"' + i[0] + '"}},{"Name": "StoreFile","Value": true}]}'
        # print(data)
        output = json.loads(data)

        fin = requests.post(pdf, json=output)
        response = fin.json()
        # print(response['Files'][0]['Url'])
        pdf_links.append(response['Files'][0]['Url'])


    data = '{"Parameters": [{"Name": "Files","FileValues": ['

    for i in range(len(pdf_links)):
        data += '{"Url": " '+ pdf_links[i] +'"}'
        if(i != len(pdf_links)-1):
            data += ","

    data += ']},{"Name": "StoreFile","Value": true}]}'

    # print(data)
    output = json.loads(data)
    fin = requests.post(merger, json=output)
    response = fin.json()
    print(response)
    return str(response['Files'][0]['Url'])
 
    # pdfs = []
    # for image in images:
    #     data = '{"Parameters": [{"Name": "File", "FileValue": {"Url": "' + image[0] +  '"}}, {"Name": "StoreFile", "Value": true}]}'
    #     print(data)
    #     output = json.loads(data)
    #     img_pdf = requests.post(pdf, json=output)
    #     final_pdf = img_pdf.json()
    #     pdfs.append(final_pdf['Files'][0]['Url'])
    # print(pdfs)

    # # MERGE PDFs
    # data = '''{"Parameters": [{"Name": "Files","FileValues": ['''
    # for i in range(len(pdfs)):
    #     data += '{"Url": "' + pdfs[i] +'"}'
    #     if i != len(pdfs)-1:
    #         data += ","
    # data += ']},{"Name": "StoreFile","Value": true}]}'
    # print(data)
    # output = json.loads(data)
    # merged_pdf = requests.post(pdf, json=output)
    # print(merged_pdf.json())


if __name__ == "__main__":
    if env == "dev":
        app.run(debug=True)
    else:
        app.run()