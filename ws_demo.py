#coding=utf-8
import os.path
import json
import hashlib

import tornado.ioloop
import tornado.httpserver
import tornado.web
import tornado.options
import tornado.websocket
from tornado.options import define,options

from model import *


define("port", default=8009, help="run on the given port", type=int)
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r'/', IndexHandler), (r'/soc', SocketHandler), (r'/login', LoginHandler), (r'/register', RegisterHandler), (r'/friend', FriendHandler), (r'/friend/add/([0-9Xx\-]+)', FriendHandler)]
        settings = dict(
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            debug = True,
            cookie_secret = 'bwli',
            login_url = r'/login'
        )
        self.db = session
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')

class FriendHandler(BaseHandler):
    def get(self, user_id):
        print user_id
        print dir(self)
        print self.get_cookie('user_id'),self.get_current_user(),self.cookies,self.request.uri
        print self.render.__doc__
        self.render('find_friend.html', users=None)

    def post(self):
        db_session = self.application.db
        query = db_session.query(User)
        users = query.all()
        self.render('find_friend.html', users=users)

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('index.html')

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    
    def post(self):
        name = self.get_argument('name', None)
        pwd = self.get_argument('pwd', None)
        #md5加密
        m = hashlib.md5()
        m.update(pwd)
        pwd = m.hexdigest()
        db_session = self.application.db
        query = db_session.query(User)
        user = query.filter(User.user_name == name, User.user_pwd == pwd).first()
        if user:
            self.set_secure_cookie('username', user.user_name)
            self.set_cookie('user_name', user.user_name)
            self.set_cookie('user_id', str(user.user_id))
            self.render('index.html',user = user)
        else:
            self.render('error.html', message= '用户名或密码错误')

class RegisterHandler(BaseHandler):
    def get(self):
        self.render('register.html')

    def post(self):
        name = self.get_argument('user_name', None)
        pwd = self.get_argument('pwd', None)
        m = hashlib.md5()
        m.update(pwd)
        pwd = m.hexdigest()
        user = User()
        user.user_name = name
        user.user_pwd = pwd
        db_session = self.application.db
        print user.user_name,user.user_pwd
        db_session.add(user)
        db_session.commit()
        self.redirect('/login')

class SocketHandler(tornado.websocket.WebSocketHandler):
    clients = set()
    clients_dict = {}
    def open(self):
        self.write_message('Welcome to WebSocket')
        message = {'type':'sys', 'message':'%s has joined' %str(id(self))}
        SocketHandler.send_to_all(message)
        SocketHandler.clients.add(self)
    
    def on_close(self):
        SocketHandler.clients.remove(self)
    
    def on_message(self, message):
        print '----------: ', json.loads(message)
        message = json.loads(message)
        if message['type'] == 'sys':
            SocketHandler.clients_dict[message['message'].split('=')[-1]] = self
        
        if message['to'] != 'all':
            SocketHandler.send_to_person(message, message['to'])
        else:
            send_message = {'type':'user', 'id':str(id(self)), 'message': message['message']}
            SocketHandler.send_to_all(send_message)

    @staticmethod
    def send_to_all(message):
        for c in SocketHandler.clients:
            c.write_message(json.dumps(message))

    @staticmethod
    def send_to_person(message, name):
        client = SocketHandler.clients_dict[name]
        client.write_message(json.dumps(message))

    @staticmethod
    def send_to_group(message, clients):
        for c in clients:
            c.write_message(josn.dumps(message))
        pass


def main():
    print '-------'
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
