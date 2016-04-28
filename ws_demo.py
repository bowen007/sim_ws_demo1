#coding=utf-8
import os.path
import json
import hashlib
import datetime

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
        handlers = [(r'/', IndexHandler), (r'/soc', SocketHandler), (r'/login', LoginHandler), (r'/register', RegisterHandler), (r'/friend', FriendListHandler), (r'/friend/add', FriendHandler)]
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
    def post(self):
        add_from = self.get_secure_cookie('user_id')
        print '++++++++++++now  cookies ', add_from
        add_status = self.get_argument('add_status')
        add_to = self.get_argument("to")
        db_session = self.application.db
        friend_relation_query = db_session.query(Friend_Relation)
        if int(add_status) == 0:
            #添加好友申请
            #pre_friend_add = None
            friend_add_info = Friend_Relation(add_from, add_to, None, None, datetime.datetime.now())
            pre_friend_relation_query = friend_relation_query.filter(Friend_Relation.user_id==add_from, Friend_Relation.friend_id==add_to)
            friend_relation = pre_friend_relation_query.first()
            if friend_relation is None:
                add_verify = self.get_argument('verify')
                friend_add_info.add_verify = add_verify
                friend_add_info.friend_status = add_status
                db_session.add(friend_add_info)
                self.write('request commit success')
                print SocketHandler.clients_dict
                print friend_add_info.__dict__
                client = SocketHandler.clients_dict[add_to]
                message_content = {'content_type':'add_friend', 'user_id':friend_add_info.user_id, 'time':friend_add_info.start_date, 'verify':friend_add_info.add_verify}
                message = Message('sys', message_content, friend_add_info.user_id, friend_add_info.friend_id, datetime.datetime.now())
                client.write_message(json.dumps(message, default=convert_to_builtin_type))
            else:
                if int(friend_relation.friend_status) == 1:
                    self.write('already your friend!')
                else:
                    self.write('request already commit in %s, please wait for response' %friend_relation.start_date)
        else:
            #添加好友确认
            #from is the respone, to is the request from 
            pre_friend_relation_query = friend_relation_query.filter(Friend_Relation.user_id==add_to, Friend_Relation.friend_id==add_from)
            pre_friend_relation_query.update({Friend_Relation.friend_status:add_status})
            if int(add_status) == 1:
                self.write('add friend success')
            else:
                self.write('refuse add friend request success')
        db_session.commit()

class FriendListHandler(BaseHandler):
    def get(self):
        print dir(self)
        print '+++++++++++++',self.get_current_user(),self.cookies,self.request.uri,'=====',self.get_secure_cookie('user_id')
        a = get_friend_list(self.get_secure_cookie('user_id'), self.application.db)
        print "0000000000000", a

        self.render('find_friend.html', users=None)

    def post(self):
        db_session = self.application.db
        query = db_session.query(User)
        users = query.all()
        self.render('find_friend.html', users=users)

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('index.html', user=None)

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
            self.set_secure_cookie('user_name', user.user_name)
            self.set_secure_cookie('user_id', str(user.user_id))
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
        now_time = datetime.datetime.now()
        message = Message('sys', self.get_secure_cookie('user_id')+','+ self.get_secure_cookie('user_name')+' has joined', self.get_secure_cookie('user_id'), 'all', now_time)
        SocketHandler.send_message(message)
        SocketHandler.clients_dict[self.get_secure_cookie('user_id')] = self
        SocketHandler.clients.add(self)
    
    def on_close(self):
        SocketHandler.clients.remove(self)
    
    def on_message(self, message):
        message_context = json.loads(message)
        #message_context:message_content,message_to
        message = Message('user', message_context['message_content'], self.get_secure_cookie('user_id'), message_context['message_to'], datetime.datetime.now())
        if message.message_to != 'all':
            SocketHandler.send_message(message)
        else:
            SocketHandler.send_message(message)

    @staticmethod
    def send_message(message):
        if message.message_type == 'user':
            clinet = SocketHandler.clients_dict[message.message_to]
            clinet.write_message(json.dumps(message, default=convert_to_builtin_type))
        elif message.message_type == 'group':
            group_members = SocketHandler.group_dict[message.message_to]
            try:
                for one in group_members:
                    client = SocketHandler.clients_dict[one]
                    client.write_message(json.dumps(message, default=convert_to_builtin_type))
            except:
                print one,' is not online'
        else:
            for c in SocketHandler.clients:
                c.write_message(json.dumps(message, default=convert_to_builtin_type))


def convert_to_builtin_type(obj):
    u'''转换函数，将对象转换成json'''
    d = {}
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    d.update(obj.__dict__)
    return d

def get_friend_list(user_id, db_session):
    query = db_session.query(Friend_Relation)
    friend_list = query.filter(Friend_Relation.user_id == user_id).all()
    print '!!!!!!!!!!!!!', friend_list
    friend_list.extend(query.filter(Friend_Relation.friend_id == user_id).all())
    print '!!!!!!!!!!!!!', friend_list
    friend_list = set(friend_list)
    for friend in friend_list:
        a = friend.user_id
        user = db_session.query(User).filter_by(user_id = a).first()
        print user.__dict__
    return friend_list

def main():
    print '-------'
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
