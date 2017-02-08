import logging
import json

import requests

from mesoshttp.core import CoreMesosObject
from mesoshttp.exception import MesosException

from google.protobuf.json_format import MessageToJson


class Offer(CoreMesosObject):

    def __init__(self, mesos_url, frameworkId, streamId, mesosOffer):
        CoreMesosObject.__init__(self, mesos_url, frameworkId, streamId)
        self.logger = logging.getLogger(__name__)
        self.offer = mesosOffer

    def accept(self, operations):
        '''
        Accept offer with task operations
        '''
        offer_ids = [{'value': self.offer['id']['value']}]

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Mesos-Stream-Id': self.streamId
        }
        self.logger.debug('Mesos:ACCEPT Offer ids:' + str(offer_ids))

        tasks = []
        for operation in operations:
            if not operation.slave_id.value:
                operation.slave_id.value = self.offer['agent_id']['value']
            json_operation = MessageToJson(operation)
            task = json.loads(json_operation)
            task['task_id'] = task['taskId']
            task['agent_id'] = task['slaveId']
            del task['taskId']
            del task['slaveId']
            tasks.append(task)

        message = {
            "framework_id": {"value": self.frameworkId},
            "type": "ACCEPT",
            "accept": {
                "offer_ids": offer_ids,
                "operations": {
                    'type': 'LAUNCH',
                    'launch': {'task_infos': tasks}
                }
            }
        }
        try:
            requests.post(
                self.mesos_url + '/api/v1/scheduler',
                json.dumps(message),
                headers=headers
            )
            self.logger.debug('Mesos:Accept:Answer:' + str(message))
        except Exception as e:
            raise MesosException(e)
        return True

    def decline(self):
        '''
        Decline offer
        '''
        if not self.offer:
            return
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Mesos-Stream-Id': self.streamId
        }
        offers_decline = {
            "framework_id": {"value": self.frameworkId},
            "type": "DECLINE",
            "decline": {
                "offer_ids": []
            }
        }

        self.logger.debug('Mesos:Decline:Offer:' + self.offer['id']['value'])
        offers_decline['decline']['offer_ids'].append(
            {'value': self.offer['id']['value']}
        )
        try:
            self.r = requests.post(
                self.mesos_url + '/api/v1/scheduler',
                json.dumps(offers_decline),
                headers=headers
            )
        except Exception as e:
            raise MesosException(e)
        return True