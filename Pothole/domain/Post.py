class Post:
    def __init__(self, id, member_id, title, content, view_count=0, created_at=None, writer_name=None, file_count=0, attachments=None):
        self.id = id
        self.member_id = member_id
        self.title = title
        self.content = content
        self.view_count = view_count
        self.created_at = created_at
        self.writer_name = writer_name  # JOIN을 통해 가져올 작성자 이름
        self.file_count = file_count    # 서브쿼리로 가져올 첨부파일 개수
        self.attachments = attachments or [] # 상세 페이지용 첨부파일 리스트

    @classmethod
    def from_db(cls, row: dict):
        if not row: return None
        return cls(
            id=row.get('id'),
            member_id=row.get('member_id'),
            title=row.get('title'),
            content=row.get('content'),
            view_count=row.get('view_count', 0),
            created_at=row.get('created_at'),
            writer_name=row.get('writer_name'),
            file_count=row.get('file_count', 0)
        )

class Attachment:
    def __init__(self, id, post_id, origin_name, save_name, file_path, created_at=None):
        self.id = id
        self.post_id = post_id
        self.origin_name = origin_name
        self.save_name = save_name
        self.file_path = file_path
        self.created_at = created_at

    @classmethod
    def from_db(cls, row: dict):
        if not row: return None
        return cls(
            id=row.get('id'),
            post_id=row.get('post_id'),
            origin_name=row.get('origin_name'),
            save_name=row.get('save_name'),
            file_path=row.get('file_path'),
            created_at=row.get('created_at')
        )
