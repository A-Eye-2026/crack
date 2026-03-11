class Member:
    def __init__(self, id, uid, pw, name, role="user", active=True, created_at=None, profile_photo=None, cover_photo=None, last_active=None, email=None):
        self.id = id
        self.uid = uid
        self.pw = pw
        self.name = name
        self.role = role
        self.active = active
        self.created_at = created_at
        self.profile_photo = profile_photo
        self.cover_photo = cover_photo
        self.last_active = last_active
        self.email = email

    @classmethod
    def from_db(cls, row: dict):
        if not row:
            return None
        return cls(
            id=row.get('id'),
            uid=row.get('uid'),
            pw=row.get('password'),
            name=row.get('name'),
            role=row.get('role'),
            active=bool(row.get('active')),
            created_at=row.get('created_at'),
            profile_photo=row.get('profile_photo'),
            cover_photo=row.get('cover_photo'),
            last_active=row.get('last_active'),
            email=row.get('email')
        )

    def is_admin(self):
        return self.role == "admin"
