import urllib.parse
from typing import List, Dict, Any, Optional
from .util import divide_chunks, json
from .models import PointSelector
from .helpers import ClientBase


class APIClient(ClientBase):
    def __init__(self, api_url, user=None, pw=None, api_key=None, token=None,
                 name='') -> None:
        super().__init__(api_url, user, pw, api_key, token, name)

    @json
    def whoami(self) -> Dict[str, str]:
        """returns the current account's information"""
        return self.get('/whoami')

    @json
    def get_account_actions(self) -> List[Dict[str, str]]:
        """returns the action audit log by or affecting the current account"""
        return self.get('/account-actions')

    @json
    def get_users(self) -> List[Dict[str, str]]:
        """returns the list of visible user accounts
          For organization admins this is all users in the organization
          For non-admin users this is just the current account
        """
        return self.get('/users')

    @json
    def get_organizations(self) -> List[Dict[str, str]]:
        return self.get('/organizations')

    @json
    def get_all_buildings(self) -> List[Dict[str, str]]:
        return self.get('/buildings')

    @json
    def get_tags(self) -> List[Dict[str, str]]:
        return self.get('/tags')

    @json
    def get_equipment_types(self) -> List[Dict[str, str]]:
        return self.get('/equiptype')

    @json
    def get_building_equipment(self, building_id: int) -> List[Dict[str, str]]:
        return self.get(f'/buildings/{building_id}/equipment?points=true')

    @json
    def select_points(self, selector: PointSelector) -> Dict[str, List[int]]:
        return self.post('/points/select', json=selector.json())

    def get_all_points(self) -> List[int]:
        buildings = self.get_all_buildings()
        point_ids = []
        for b in buildings:
            bldg_id = b['id']
            equipment = self.get_building_equipment(bldg_id)
            for e in equipment:
                point_ids += e['points']
        return point_ids

    def get_points_by_ids(self, point_ids: List[int]) -> List[Dict[str, str]]:
        @json
        def get_points(url):
            return self.get(url)

        points = []
        for chunk in divide_chunks(point_ids, 500):
            points_str = '[' + ','.join(str(id) for id in chunk) + ']'
            url = f'/points?point_ids={points_str}'
            points_chunk = get_points(url)
            points += points_chunk
        return points

    def get_points_by_datasource(self, datasource_hashes: List[str]) \
            -> List[Dict[str, str]]:
        datasource_hashes_chunked = list(divide_chunks(datasource_hashes, 125))

        @json
        def get_points(url):
            return self.get(url)

        points = []
        for chunk in datasource_hashes_chunked:
            hashes_str = "[" + ','.join([r"'" + c + r"'" for c in chunk]) + "]"
            query = urllib.parse.quote(hashes_str)
            url = f'/points?datasource_hashes={query}'
            points_chunk = get_points(url)
            points += points_chunk
        return points

    @json
    def get_all_point_types(self) -> List[Dict[str, str]]:
        return self.get('/pointtypes')

    @json
    def get_all_measurements(self) -> List[Dict[str, str]]:
        return self.get('/measurements')

    @json
    def get_all_units(self) -> List[Dict[str, str]]:
        return self.get('/unit')

    @json
    def query_point_timeseries(self, point_ids: List[int],
                               start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Query a timespan for a set of point ids
        point_ids: a list of point ids
        start/end time: ISO formatted timestamp strings e.g. '2019-11-29T20:16:25Z'
        """
        query = {
            'point_ids': point_ids,
            'start_time': start_time,
            'end_time': end_time,
        }
        return self.post('/query', json=query)

    @json
    def update_point_data(self, updates=[]) -> None:
        """Bulk update point data, returns the number of updated points
        updates: an iterable of models.PointDataUpdate objects"""
        for batch in divide_chunks(updates, 500):
            json = [u.json() for u in batch]
            self.post('/points_update', json=json)

    @json
    def send_ingest_stats(self, ingest_stats) -> None:
        """Send timing and diagnostic info to the portal
        ingest_stats: an instance of models.IngestStats"""
        json = ingest_stats.json()
        self.post('/ingest-stats', json=json)

    @json
    def get_ingest_stats(self) -> List[Dict[str, str]]:
        """returns ingest stats for all buildings"""
        return self.get('/ingest-stats')

    @json
    def get_alerts(self) -> List[Dict[str, str]]:
        """returns a list of active alerts for all buildings"""
        return self.get('/alerts')

    @json
    def copy_point_data(self, point_id_map, start_time, end_time) -> str:
        """Copy data between points
        point_id_map: a map of source to destination point id
        start/end: ISO formatted timestamp strings e.g. '2019-11-29T20:16:25Z'
        returns: a string describing the operation
        """
        command = {
            'point_id_map': point_id_map,
            'start_time': start_time,
            'end_time': end_time,
        }
        return self.post('/point-data-copy', json=command)


class DevelopmentAPIClient(APIClient):
    def __init__(self, user=None, pw=None, api_key=None, token=None) -> None:
        super().__init__('https://devapi.onboarddata.io',
                         user, pw, api_key, token)


class ProductionAPIClient(APIClient):
    def __init__(self, user: Optional[str] = None, pw: Optional[str] = None,
                 api_key: Optional[str] = None,
                 token: Optional[str] = None) -> None:
        super().__init__('https://api.onboarddata.io',
                         user, pw, api_key, token)
