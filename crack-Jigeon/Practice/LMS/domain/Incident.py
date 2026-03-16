class Incident:
    def __init__(
        self,
        id,
        member_id,
        title,
        location,
        region_name,
        latitude,
        longitude,
        image_path=None,
        status="접수완료",
        first_created_at=None,
        last_checked_at=None
    ):
        self.id = id
        self.member_id = member_id
        self.title = title
        self.location = location
        self.region_name = region_name
        self.latitude = latitude
        self.longitude = longitude
        self.image_path = image_path
        self.status = status
        self.first_created_at = first_created_at
        self.last_checked_at = last_checked_at

    @classmethod
    def from_db(cls, row: dict):
        if not row:
            return None
        return cls(
            id=row.get('id'),
            member_id=row.get('member_id'),
            title=row.get('title'),
            location=row.get('location'),
            region_name=row.get('region_name'),
            latitude=row.get('latitude'),
            longitude=row.get('longitude'),
            image_path=row.get('image_path'),
            status=row.get('status'),
            first_created_at=row.get('first_created_at'),
            last_checked_at=row.get('last_checked_at')
        )


    def __str__(self):
        return f"[{self.id}] {self.title} / {self.location} / {self.status}"