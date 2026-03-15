class UserInterestRegion:
    def __init__(
        self,
        id,
        member_id,
        region_name,
        latitude,
        longitude,
        created_at=None
    ):
        self.id = id
        self.member_id = member_id
        self.region_name = region_name
        self.latitude = latitude
        self.longitude = longitude
        self.created_at = created_at

    @classmethod
    def from_db(cls, row: dict):
        if not row:
            return None
        return cls(
            id=row.get('id'),
            member_id=row.get('member_id'),
            region_name=row.get('region_name'),
            latitude=row.get('latitude'),
            longitude=row.get('longitude'),
            created_at=row.get('created_at')
        )

    def __str__(self):
        return f"[{self.id}] member={self.member_id}, 관심지역={self.region_name}"