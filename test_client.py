import requests

url = "http://localhost:5000/"

def get_room_test():
    url = "http://localhost:5000/get_room/"
    params = {
        "room_id": 619041,
        "guid": 30,
    }      
    response = requests.get(url, params=params)
    print(response.content)
        
def join_room_test():
    url = "http://localhost:5000/join/"
    data = {
        "room_id": 619041,
        "guid": 30
    }
    response = requests.post(url, data=data)
    print(response.content)
    
def update_room_test():
    url = "http://localhost:5000/update_room/"
    data = {
        "room_id": 321661,
        "guid": 30,
        "start_game": True,
        "IP_endpoint": "127.0.0.1:8000"
    }
    response = requests.post(url, data=data)
    print(response.content)
    
    
def create_room_test():
    url = "http://localhost:5000/create_room/"
    data = {
        "guid": 30
    }
    response = requests.post(url, data=data)
    print(response.content)
        
if __name__ == "__main__":
    update_room_test()