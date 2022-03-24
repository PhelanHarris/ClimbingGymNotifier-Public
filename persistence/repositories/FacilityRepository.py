from persistence.models.Facility import Facility
from persistence.repositories.BaseRepository import BaseRepository


class FacilityRepository(BaseRepository):
    def __init__(self):
        self.model = Facility
