from itertools import count
from urllib import urlencode

from demands import HTTPServiceClient
from yoconfig import get_config


class CloudFlareService(HTTPServiceClient):
    def __init__(self, api_key, email, organization=None):
        config = get_config('cloudflare')
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Key': api_key,
            'X-Auth-Email': email,
        }
        self._organization = organization
        url = config['url'] + 'client/v4/'
        super(CloudFlareService, self).__init__(
            url, headers=headers, send_as_json=True)

    def _iter_pages(self, base_url, params=None, page_size=50):
        base_params = params or {}
        base_params['per_page'] = page_size

        for page in count():
            params = base_params.copy()
            params['page'] = page
            url = base_url + '?' + urlencode(params)
            batch = self.get(url).json()['result']
            for result in batch:
                yield result
            if len(batch) < page_size:
                return

    def iter_zones(self):
        return self._iter_pages('zones')

    def get_zones(self):
        return list(self.iter_zones())

    def get_zone(self, zone_id):
        return self.get('zones/%s' % zone_id).json()['result']

    def get_zone_by_name(self, name):
        url = 'zones?' + urlencode({'name': name})
        result = self.get(url).json()['result']
        assert len(result) <= 1
        return result[0]

    def iter_zone_settings(self, zone_id):
        for setting in self._iter_pages('zones/%s/settings' % zone_id):
            yield setting['id'], setting

    def get_zone_settings(self, zone_id):
        return dict(self.iter_zone_settings(zone_id))

    def get_zone_setting(self, zone_id, setting):
        url = 'zones/%s/settings/%s' % (zone_id, setting)
        return self.get(url).json()['result']

    def set_zone_setting(self, zone_id, setting, value):
        url = 'zones/%s/settings/%s' % (zone_id, setting)
        return self.patch(url, {'value': value}).json()['result']

    def create_zone(self, name, jump_start=False):
        data = {
            'name': name,
            'jump_start': jump_start,
        }
        if self._organization:
            data['organization'] = {'id': self._organization}
        return self.post('zones', data).json()['result']

    def delete_zone(self, zone_id):
        return self.delete('zones/%s' % zone_id)

    def iter_dns_records(self, zone_id):
        return self._iter_pages('zones/%s/dns_records' % zone_id)

    def get_dns_records(self, zone_id):
        return list(self.iter_dns_records(zone_id))

    def get_dns_record(self, zone_id, record_id):
        url = 'zones/%s/dns_records/%s' % (zone_id, record_id)
        return self.get(url).json()['result']

    def create_dns_record(self, zone_id, content):
        url = 'zones/%s/dns_records' % zone_id
        return self.post(url, content).json()['result']

    def update_dns_record(self, zone_id, record_id, content):
        url = 'zones/%s/dns_records/%s' % (zone_id, record_id)
        return self.patch(url, content).json()['result']

    def delete_dns_record(self, zone_id, record_id):
        url = 'zones/%s/dns_records/%s' % (zone_id, record_id)
        return self.delete(url).json()['result']
