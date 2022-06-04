from pprint import pprint
from sqlalchemy.orm import sessionmaker
from enum import Enum
from sqlalchemy import create_engine

DB_URL = 'postgres://upueggduidkemk:332e4beba54235af23433659ee4f6db820d69103f0bdf728da5c665d324d61fa@ec2-44-196-174-238.compute-1.amazonaws.com:5432/dfvdfqvkj5lflo'

engine = create_engine(DB_URL)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base() 
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean

class RoomState(Enum):
    WAITING = 1
    PORTWAITING = 2
    PLAYING = 3

class Room(Base):
    __tablename__ = "room"  # テーブル名を指定
    room_id = Column(Integer, primary_key=True)
    is_private = Column(Boolean)
    player_count = Column(Integer)
    guids = Column(String(255))
    room_state = Column(Integer)
    endpoints = Column(String(255)) # IP:Portのリスト
    invalid_endpoints = Column(String(255)) # 各ポートが有効かのリスト
    time = Column(Integer)
    protocols = Column(Integer)
    
    def __init__(self, room_id, first_guid, is_private=False):
        self.room_id = room_id
        self.player_count = 1
        guid_list = [first_guid, 0, 0, 0, 0]
        self.guids = ",".join([str(i) for i in guid_list])
        self.room_state = RoomState.WAITING.value
        EP_list = [0, 0, 0, 0, 0]
        self.endpoints = ",".join([str(i) for i in EP_list])
        invalids = [False, False, False, False, False]
        self.invalid_endpoints = ",".join([str(i) for i in invalids])
        self.is_private = is_private
        self.time = 0
        protocols = 0
        
    def get_lists(self):
        guid_list = self.guids.replace(" ", "").split(",")
        EP_list = self.endpoints.replace(" ", "").split(",")
        port_list = self.invalid_endpoints.replace(" ", "").split(",")
        return guid_list, EP_list, port_list
    
    def get_json(self):
        data = {}
        data["room_id"] = self.room_id
        data["room_state"] = str(RoomState(self.room_state))
        data["player_count"] = self.player_count      
        data["endpoints"] = self.endpoints
        data["invalid_endpoints"] = self.invalid_endpoints
        return data

Base.metadata.create_all(engine)

def test_sql():
    engine = create_engine(DB_URL)
    SessionClass = sessionmaker(engine)  # セッションを作るクラスを作成
    session = SessionClass()
    # ISNERT
    user_a = Room(room_id = 3, player_count = 1)
    session.add(user_a)
    session.commit()
    users = session.query(Room).all()
    for i in users:
        pprint(vars(i))

def delete_all_rooms():
    engine = create_engine(DB_URL)
    SessionClass = sessionmaker(engine)  # セッションを作るクラスを作成
    session = SessionClass()
    session.query(Room).delete()
    all_rooms = session.query(Room).all()
    for i in all_rooms:
        print(vars(i))

if __name__ == '__main__':
    Room.__table__.drop(engine)
    pass