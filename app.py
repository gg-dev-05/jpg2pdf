from flask import Flask
from flask_mysqldb import MySQL
import yaml
import requests


app = Flask(__name__)

dev = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = dev['mysql_host']
app.config['MYSQL_USER'] = dev['mysql_user']
app.config['MYSQL_PASSWORD'] = dev['mysql_password']
app.config['MYSQL_DB'] = dev['mysql_db']

mysql = MySQL(app)
api_token = dev['token']
baseUrl = "https://api.telegram.org/bot{}".format(api_token)
baseUrlFile = "https://api.telegram.org/file/bot{}".format(api_token)

@app.route("/")
def start():    
    r = requests.get(baseUrl+"/getUpdates")
    data = r.json()
    print(len(data['result']))
    for i in data['result']:
        id = i['message']['from']['id']
        createUser(id)

        if 'text' in i['message'] and i['message']['text'] = "/start":
            removeAllOldImages(id)
        if 'document' in i['message']:
            fileId = i['message']['document']['thumb']['file_id']
            p = requests.get(baseUrl+"/getFile?fileid={}".format(fileId))
            fileDetails = p.json()
            file_path = fileDetails['result']['file_path']
            link = baseUrlFile+"/{}".format(file_path)
            newImage(link, id)

    return str(data['result'][0]['message']['from']['id'])


def createUser(userID):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    print(users)
    present = False
    for user in users:
        if(str(user[0]) == str(userID)):
            present = True
            print("Already Present")

    if(not present):
        cur.execute("INSERT INTO users VALUES('{}');".format(userID))  
        print("INSERTED")
        cur.execute("CREATE TABLE user_{}(image VARCHAR(2000));".format(userID))
        mysql.connection.commit()
        cur.close()
        print("Inserted")

def newImage(link, userId):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_{} VALUES({});".format(userId, link))
    cur.connection.commit()
    cur.close()
    print(link, " added to user_", userId)

def removeAllOldImages(userId):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_{}".format(userId))
    cur.connection.commit()
    cur.close()
    print("Old Images removed")

if __name__ == "__main__":
    app.run(debug=True)