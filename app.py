from flask import Flask
app = Flask(__name__)
from flask import request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sql_util import Room, RoomState
import random

DB_URL = 'GO_VISIT_POSTGRESQL_SETTINGS_AND_COPY_CREDENTIALS_URI_AND_PASTE_HERE'
engine = create_engine(DB_URL)

# required: guid
@app.route("/create_room/", methods=['POST'])
def create_room():
    if "guid" not in request.form:
        return "No Room Found."
    SessionClass = sessionmaker(engine)
    session = SessionClass()
    all_rooms = session.query(Room).all()
    room_ids = [room.room_id for room in all_rooms]
    room_id = random.randint(0,1000000)
    while (room_id in room_ids): room_id = random.randint(0,1000000)
    new_room = Room(room_id=room_id, first_guid=request.form["guid"])
    session.add(new_room)
    session.commit()
    json_text = new_room.get_state_dict()
    json_text["player_index"] = 0
    session.close()
    return jsonify(json_text)

# 30件返す
@app.route("/get_all_room/", methods=["GET"])
def get_rooms():
    SessionClass = sessionmaker(engine)
    session = SessionClass()
    room = session.query(Room).filter(Room.player_count < 5, Room.is_private==False, Room.room_state==RoomState.WAITING.value).limit(30).all()
    if room is None: return "No Room Found."
    room_info_list = []
    for i in room:
        room_info_list.append({"room_id": i.room_id, "player_count": i.player_count})
    print(room_info_list)
    return jsonify(room_info_list)
    
# required: guid
# optional: room_id if you join specific room
@app.route("/join/", methods=['POST'])
def join():
    if "guid" not in request.form:
        return "No Room Found."
    SessionClass = sessionmaker(engine)
    session = SessionClass()
    if "room_id" not in request.form:
        # 野良参加
        room = session.query(Room).filter(Room.player_count < 5, Room.is_private==False, Room.room_state==RoomState.WAITING.value).first()   
    else:
        room_id = int(request.form["room_id"])
        print(room_id)
        room = session.query(Room).filter(Room.player_count < 5, Room.room_id==room_id, Room.room_state==RoomState.WAITING.value).first()
    if room is None: return "No Room Found."
    guids, _, _ = room.get_lists()
    if request.form["guid"] in guids:
        return jsonify(room.get_state_dict())
    room.player_count += 1
    guids[room.player_count -1] = request.form["guid"]
    room.guids = ",".join(guids)
    session.commit()
    json_text = room.get_state_dict()
    json_text["player_index"] = room.player_count - 1
    session.close()
    return jsonify(json_text)

# requried: room_id: int, guid: int
@app.route("/get_room/", methods=['GET'])
def get_room_state():
    room_id = request.args.get("room_id", 0)
    guid = request.args.get("guid", " ")
    if room_id is 0 or guid is " ": return "No Room Found."
    SessionClass = sessionmaker(engine)
    session = SessionClass()
    room = session.query(Room).filter(Room.room_id == room_id).first()
    if (room is None): return "No Room Found."
    guids, _, _ = room.get_lists()
    if (guid not in guids): return "No Room Found."
    json_text = room.get_state_dict()
    json_text["player_index"] = guids.index(guid)
    json_text["invision_index"] = room.invision_index
    session.close()
    return jsonify(json_text)

# requried: room_id: int, guid: int
@app.route("/leave_room/", methods=["POST"])
def leave_room():
    if "room_id" not in request.form or "guid" not in request.form:
        return "Failed"
    SessionClass = sessionmaker(engine)
    session = SessionClass()
    room = session.query(Room).filter(Room.room_id == int(request.form["room_id"])).first()
    if room is None: return "Failed"
    guids, endpoints, ports = room.get_lists()
    if request.form["guid"] not in guids: return "Failed"
    room.player_count -= 1
    if room.player_count == 0: 
        session.delete(room)
        session.commit()
        session.close()
        return "Success"
    player_index = guids.index(request.form["guid"])
    guids.pop(player_index).append("0")
    endpoints.pop(player_index).append("0")
    ports.pop(player_index).append("False")
    room.endpoints = ",".join(endpoints)
    room.invalid_endpoints = ",".join(ports)
    room.guids = ",".join(guids)
    session.commit()
    session.close()
    return "Success"

# 部屋更新。スタート処理、エンドポイント設定、ポート無効報告
# required: room_id=int, guid=int
# at least 1 required: start_game=Any, IP_endpoint="oo.oo.oo.oo:xxxx", port_report="oo.oo.oo.oo:xxxx"
@app.route("/update_room/", methods=['POST'])
def update_room_state():
    if "room_id" not in request.form or "guid" not in request.form:
        return "No Room Found."
    room_id = int(request.form["room_id"])
    guid = request.form["guid"]
    SessionClass = sessionmaker(engine)
    session = SessionClass()
    room = session.query(Room).filter(Room.room_id == room_id).first()
    if (room is None): return "No Room Found."
    guids, endpoints, ports = room.get_lists()
    player_index = guids.index(guid)
    if (guid not in guids): return "No Room Found."
    print(" ".join(request.form.keys()))
    if "start_game" in request.form and room.room_state is RoomState.WAITING.value and player_index == 0:
        print("ゲーム開始");
        room.room_state = RoomState.PORTWAITING.value
    if "IP_endpoint" in request.form:
        endpoints[player_index] = request.form["IP_endpoint"]
        print("aaa")
        registered_count = sum(i != "0" for i in endpoints)
        print(registered_count)
        if registered_count == room.player_count: #集まった
            room.room_state = RoomState.PLAYING.value
            if room.invision_index == "":
                invision_index = random.randint(0, room.player_count-1)
                room.invision_index = str(invision_index)
        ports[player_index] = False
        room.endpoints = ",".join(endpoints)
        room.invalid_endpoints = ",".join([str(i) for i in ports])
    if "port_report" in request.form and request.form["port_report"] in endpoints:
        EP_index = endpoints.index(request.form["port_report"])
        ports[EP_index] = True
        room.invalid_endpoints = ",".join([str(i) for i in ports])
    session.commit()
    json_text = room.get_state_dict()
    json_text["player_index"] = player_index
    session.close()
    return jsonify(json_text)

## おまじない
if __name__ == "__main__":
    app.run(debug=True)