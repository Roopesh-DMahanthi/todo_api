from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import mysql.connector
from datetime import datetime
from cryptography.fernet import Fernet

try:
        mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="toor",
        database="work_india"
        )
except:
        print("Failed Connecting to Database")
        exit()

def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
    return key

def load_key():
    try:
        return open("secret.key", "rb").read()
    except:
        return None

key = load_key()
if (key == None):
    print('New Key Generated')
    key=generate_key()

app = Flask(__name__)
api = Api(app)


class Register(Resource):
    def post(self):
        agent_id = request.form['agent_id']
        passwd = request.form['password']
        #print(agent_id, passwd)
        passwd = Fernet(key).encrypt(passwd.encode()).decode()
        
        mycursor = mydb.cursor()
        sql = 'INSERT INTO users (aid,password) VALUES (%d, "%s");' % (int(agent_id), passwd)
        #print(sql)
        try:
            mycursor.execute(sql)
        except:
            return {'status': 'account not-created'},404
        mydb.commit()
        mycursor.close()
        return {'status': 'account created','status_code': 200 },200

class Login(Resource):    
    def post(self):
        agent_id = request.form['agent_id']
        passwd = request.form['password']
        #passwd=Fernet(key).encrypt(passwd.encode())
        mycursor = mydb.cursor()
        sql = 'SELECT aid,password FROM users WHERE aid=%d;' % (int(agent_id))
        #print(sql)
        try:
            mycursor.execute(sql)
        except:
            return {'status': 'failure','status_code': 401 },401
        data=mycursor.fetchone()
        if (data == None):
            return {'status': 'failure','status_code': 401 },401
        aid, password = data
        password = Fernet(key).decrypt(password.encode()).decode()
        mycursor.close()
        if (str(password) == str(passwd)):
            return {'status': 'success','agent_id': int(aid),'status_code': 200 },200
        return {'status': 'failure','status_code': 401 },401

class ListTodos(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('agent', type=int, help='Agent Id')
        args = parser.parse_args()
        aid = args['agent']
        mycursor = mydb.cursor()
        sql = 'SELECT title,description, category, due_date FROM todos WHERE agentid=%d ORDER BY due_date ASC;' % (int(aid))
        try:
            mycursor.execute(sql)
        except:
            return {'status': 'failure','status_code': 401 },401
        
        rows = mycursor.fetchall()
        rowcount = mycursor.rowcount
        #print('Total Row(s):', rowcount)
        data=[]
        for row in rows:
            row=list(row)
            row[-1] = row[-1].strftime("%d/%m/%Y")
            dc = { 
                'title': row[0], 
                'description': row[1], 
                'category': row[2], 
                'due_date': row[3] 
                } 
            print(dc)
            data.append(dc)

        mycursor.close()
        return data,200
        
class SaveTodo(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('agent', type=int, help='Agent Id')
        args = parser.parse_args()
        aid = args['agent']
        title = request.form['title']
        desc = request.form['description']
        categ = request.form['category']
        dt = request.form['due_date']
        mycursor = mydb.cursor()
        sql = 'INSERT INTO todos (title,description,category,due_date,agentid) VALUES ("%s","%s","%s","%s",%d);' %(title,desc,categ,dt,aid)
        try:
            mycursor.execute(sql)
        except:
            return {'status': 'failure','status_code': 401 },401
        mydb.commit()
        mycursor.close()
        
        return {'status': 'success','status_code': 200},200 



api.add_resource(Register, '/app/agent')
api.add_resource(Login, '/app/agent/auth')
api.add_resource(ListTodos, '/app/sites/list/')
api.add_resource(SaveTodo, '/app/sites')

if __name__ == '__main__':
    app.run(debug=True)