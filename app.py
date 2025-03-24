from flask import Flask
'''
it creates an instance of the flask class,
which will be your WsGI(web server Gateqway Interface) application
'''
###WSGI application
app = Flask(__name__)

@app.route("/")
def welcome():
    return "welcome to this flask course 1d234"


if __name__ =="__main__":
    app.run(debug=True)
