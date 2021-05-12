class SonicV2Connector:

    def __init__(self):
        self.STATE_DB = 'STATE_DB'
        self.data = {"serial": self.TEST_SERIAL, 
                     "model": self.TEST_MODEL, 
                     "revision": self.TEST_REV}
    
    def connect(self, db):
        pass

    def get(self, db, table, field):
        self.data.get(field, "N/A")
