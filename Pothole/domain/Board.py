class Board:
    def __init__(self, id, title, content, member_id, active=True, writer_name=None, writer_uid=None, created_at=None, likes_count=0, is_liked=False, image_url=None):
        self.id = id
        self.title = title
        self.content = content
        self.member_id = member_id
        self.active = active
        self.writer_name = writer_name
        self.writer_uid = writer_uid
        self.created_at = created_at
        self.likes_count = likes_count
        self.is_liked = is_liked
        self.image_url = image_url

    @classmethod
    def from_db(cls, row: dict):
        if not row: return None
        return cls(
            id=row.get('id'),
            title=row.get('title'),
            content=row.get('content'),
            member_id=row.get('member_id'),
            active=bool(row.get('active', True)),
            writer_name=row.get('writer_name'),
            created_at=row.get('created_at'),
            writer_uid=row.get('writer_uid'),
            image_url=row.get('image_url')
        )