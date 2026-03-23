class FeedTarget:
    def __init__(
        self,
        id,
        incident_id,
        member_id,
        is_read=0,
        created_at=None
    ):
        self.id = id
        self.incident_id = incident_id
        self.member_id = member_id
        self.is_read = bool(is_read)
        self.created_at = created_at

    @classmethod
    def from_db(cls, row: dict):
        if not row:
            return None
        return cls(
            id=row.get('id'),
            incident_id=row.get('incident_id'),
            member_id=row.get('member_id'),
            is_read=row.get('is_read'),
            created_at=row.get('created_at')
        )

    def mark_as_read(self):
        self.is_read = True

    def __str__(self):
        read_text = "읽음" if self.is_read else "안읽음"
        return f"[{self.id}] incident={self.incident_id}, member={self.member_id}, {read_text}"