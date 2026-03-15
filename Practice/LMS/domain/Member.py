class Member:
    def __init__(self,id,uid,pw,name,role="user",active=True):
        self.id = id
        self.uid = uid
        self.pw = pw
        self.name = name
        self.role = role
        self.active = active
    @classmethod
    def from_db(cls,row:dict):
        if not row:
            return None
        return cls(
            id = row.get('id'),
            uid = row.get('uid'),
            pw = row.get('pw'),
            name = row.get('name'),
            role = row.get('role'),
            active = bool(row.get('active'))
        )
    def is_admin(self):
        return self.role == "admin"
    def __str__(self):
        return f"{self.name},{self.uid},{self.pw} ({self.role})"