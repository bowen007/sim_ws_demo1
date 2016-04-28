#coding=utf-8
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import \
        BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE, \
        DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER, \
        LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR, \
        NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP, \
        TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR

BaseModel = declarative_base()

def init_db():
    BaseModel.metadata.create_all(engine)

def drop_db():
    BaseModel.metadata.drop_all(engine)

class User(BaseModel):
    __tablename__ = 'user_table'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(30))
    user_pwd = Column(String(100))

class Friend_Relation(BaseModel):
    __tablename__ = 'friend_relation'

    friend_relation_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    friend_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    add_verify = Column(String(30))
    friend_status = Column(String(30))
    start_date = Column(DATETIME, nullable=False)
    end_date = Column(DATETIME, nullable=True)
    def __init__(self, user_id, friend_id, add_verify, friend_status, start_date):
        self.user_id = user_id
        self.friend_id = friend_id
        self.add_verify = add_verify
        self.friend_status = friend_status
        self.start_date = start_date

class Group(BaseModel):
    __tablename__ = 'group_table'

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String(30), nullable=False)
    start_date = Column(DATE, nullable=False)
    end_date = Column(DATE)

class User_Group_Relation(BaseModel):
    __tablename__ = 'user_group_relation'

    user_group_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    group_id = Column(Integer, ForeignKey('group_table.group_id'), nullable=False)

class Friend_Add_Info(BaseModel):
    __tablename__ = 'friend_add_info'

    friend_add_id = Column(Integer, primary_key=True)
    friend_add_from = Column(Integer, ForeignKey('user_table.user_id'))
    friend_add_to = Column(Integer, ForeignKey('user_table.user_id'))
    friend_add_verify = Column(String(30))
    friend_add_time = Column(DATETIME)
    friend_add_status = Column(String(10))
    
    def __init__(self, friend_add_from, friend_add_to, friend_add_verify, friend_add_time, friend_add_status):
        self.friend_add_from = friend_add_from
        self.friend_add_to = friend_add_to
        self.friend_add_verify = friend_add_verify
        self.friend_add_time = friend_add_time
        self.friend_add_status = friend_add_status

class Message:
    message_type = ''
    message_content = ''
    message_from = ''
    message_to = ''
    message_time = ''

    def __init__(self, message_type, message_content, message_from, message_to, message_time):
        self.message_type = message_type
        self.message_content = message_content
        self.message_from = message_from
        self.message_to = message_to
        self.message_time = message_time


DB_CONNECT_STRING = 'mysql+mysqldb://root:root@localhost/test?charset=utf8'
engine = create_engine(DB_CONNECT_STRING, echo=True)
DB_Session = sessionmaker(bind=engine)
session = DB_Session()

#drop_db()
init_db()
