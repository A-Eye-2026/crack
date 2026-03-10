class Score:
    def __init__(self,member_id,kor,eng,math,id=None,created_at=None):
        self.id = id
        self.member_id = member_id
        self.kor = kor
        self.eng = eng
        self.math = math
        self.created_at = created_at
    @property
    def total(self):
        return self.kor+self.eng+self.math
    @property
    def avg(self):
        return round(self.total/3,2)
    @property
    def grade(self):
        avg = self.avg
        if avg >= 90:
            return 'A'
        elif avg >= 80:
            return 'B'
        elif avg >= 70:
            return 'C'
        else:
            return 'F'
    @classmethod
    def from_db(cls,row:dict):
        if not row:
            return None
        return cls(
        id = row.get('id'),
        member_id = row.get('member_id'),
        kor = row.get('korean'),
        eng = row.get('english'),
        math = row.get('math'),
        created_at = row.get('created_at')
        )