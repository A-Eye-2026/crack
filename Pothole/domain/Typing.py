class Typing:
    def __init__(self, id=None, ko_title=None, ko_content=None, en_title=None, en_content=None, lang='ko', hit_count=0):
        self.id = id
        self.ko_title = ko_title
        self.ko_content = ko_content
        self.en_title = en_title
        self.en_content = en_content
        self.lang = lang
        self.hit_count = hit_count

    @property
    def content(self):
        # 현재 언어에 맞는 내용을 자동으로 선택해서 반환
        return self.ko_content if self.lang == 'ko' else self.en_content

    @staticmethod
    def from_dict(row, lang='ko'):
        if not row: return None
        return Typing(
            id=row.get('id'),
            ko_title=row.get('ko_title'),
            ko_content=row.get('ko_content'),
            en_title=row.get('en_title'),
            en_content=row.get('en_content'),
            lang=lang,
            hit_count=row.get('hit_count', 0)
        )