from firebase import firebase
class firebase_Get:
    def __init__(self):
        url = 'https://lab12-34dd3-default-rtdb.firebaseio.com'
        self.fdb = firebase.FirebaseApplication(url, None)
        
    def get(self):
        
        
        #fdb.put('/test_sumo','flow1',list(i for i in range(24)))
        result = self.fdb.get('/test_sumo','flow1')
        #print(type(result))
        #print(result)            
        return result
    def put_async(self,val):
        self.fdb.put_async('/test_sumo_light','light',int(val))
    def put(self,val):
        self.fdb.put('/test_sumo_light','light',int(val))
        pass
if __name__ == "__main__":
    pass