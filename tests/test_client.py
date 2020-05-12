"""
Tests for the client
"""

from copy import deepcopy
from datetime import date

try:
    from unittest import mock
except ImportError:
    import mock

from orb_api.api import OrbClient


class TestResourceListing(object):
    """
    The pagination method should allow for iterating over the entirety of
    a result set, no matter how long it is.
    """

    initial_response = {
        "meta": {
            "limit": 3,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 3,
        },
        "objects": [
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]
    }

    def test_paginate_one_page(self):
        """Pagination should return all results without calling next"""
        client = OrbClient("", "", "")

        def error_stub(*args, **kwargs):
            raise TypeError

        client.get = error_stub

        paginated_content = list(client._paginator(self.initial_response))

        assert len(paginated_content) == 3

        assert [{"id": 1}, {"id": 2}, {"id": 3}] == paginated_content

    def test_paginate_two_pages(self, mocker):
        first_page = deepcopy(self.initial_response)
        next_url = "http://anywhere.com/v83/next/"
        first_page['meta']['next'] = next_url

        second_page = deepcopy(self.initial_response)
        second_page['objects'] = [{"id": 8}, {"id": 78}]
        assert not self.initial_response['meta']['next']
        assert not second_page['meta']['next']

        client = OrbClient("", "", "")

        mocker.patch('orb_api.api.OrbClient.get', return_value=second_page)

        paginated_content = list(client._paginator(first_page))

        client.get.assert_called_with(fullpath=next_url)

        assert len(paginated_content) == 5
        assert [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 8}, {"id": 78}] == paginated_content

    def test_resource_listing(self, mocker):
        """list_resources should return tuple with count and the generator"""
        client = OrbClient("", "", "")
        mocker.patch('orb_api.api.OrbClient.get', return_value=self.initial_response)

        count, results = client.list_resources()
        assert count == 3

    def test_resource_filtering(self, mocker):
        """Listed resources should be orderable and filterable (as allowed by API)"""
        client = OrbClient("http://localhost", "", "")
        mocked_response = mock.Mock()
        mocked_response.status_code = 200
        mocked_response.json = mock.Mock(return_value=self.initial_response)
        mocker.patch('orb_api.api.requests.Session.request', return_value=mocked_response)
        count, results = client.list_resources(order_by="-update_date", update_date__gte=date(2016, 1, 1))
        assert count == 3

        client.session.request.assert_called_with(
            "GET",
            "http://localhost/api/v1/resource/",
            params={
                "username": "",
                "api_key": "",
                "format": "json",
                "order_by": "-update_date",
                "update_date__gte": date(2016, 1, 1),
            },
            data={},
        )
