# MIT License
#
# Copyright (c) 2024 carpaty https://github.com/carpaty
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -*- coding: utf-8 -*-

"""
DB Module
"""

from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter


class Sql:
    """
    DB for users.

    :ivar client: Datastore client
    :vartype client: google.cloud.datastore.Client
    :ivar kind: Kind of the datastore entity
    :vartype kind: str
    """

    def __init__(self):
        self.client = datastore.Client()
        self.kind = "Users"

    def qselect(self, uid: str) -> str:
        """
        Select a user by uid.

        :param uid: User ID
        :type uid: str
        :return: UUID of the user if exists
        :rtype: str
        """
        task_key = self.client.key(self.kind, uid)
        entity = self.client.get(task_key)
        if entity and 'uuid' in entity:
            return entity['uuid']
        return None

    def qselect_hash(self, uuid: str):
        """
        Select a user by UUID.

        :param uuid: UUID of the user
        :type uuid: str
        :return: Result of the query
        :rtype: google.api_core.page_iterator.Iterator
        """
        query = self.client.query(kind=self.kind)
        query.add_filter(filter=PropertyFilter("uuid", '=', uuid))
        result = query.fetch()
        return result

    def qinsert(self, uid: str, uuid: str) -> None:
        """
        Insert a new user.

        :param uid: User ID
        :type uid: str
        :param uuid: UUID of the user
        :type uuid: str
        :return: None
        """
        task_key = self.client.key(self.kind, uid)
        task = datastore.Entity(key=task_key)
        task["uuid"] = uuid
        self.client.put(task)


class Cache:
    """
    Cache DB for button and state position.

    :ivar client: Datastore client
    :vartype client: google.cloud.datastore.Client
    :ivar kind: Kind of the datastore entity
    :vartype kind: str
    """

    def __init__(self):
        self.client = datastore.Client()
        self.kind = "Position"

    def qselect(self, name: str) -> dict:
        """
        Get state/button position.

        :param name: Name of the state/button
        :type name: str
        :return: State dictionary if exists
        :rtype: dict
        """
        task_key = self.client.key(self.kind, name)
        entity = self.client.get(task_key)
        if entity and 'state' in entity:
            return dict(entity['state'])
        return None

    def qinsert(self, name: str, val: dict) -> None:
        """
        Update state/button position.

        :param name: Name of the state/button
        :type name: str
        :param val: Value of the state
        :type val: dict
        :return: None
        """
        task_key = self.client.key(self.kind, name)
        task = datastore.Entity(key=task_key)
        task["state"] = val
        self.client.put(task)

    def qdelete(self, name: str) -> None:
        """
        Delete state/button position.

        :param name: Name of the state/button
        :type name: str
        :return: None
        """
        self.client.delete(self.client.key(self.kind, name))
