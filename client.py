import asyncio
import json
import time
from pydicom import Dataset
from scp import ModalityStoreSCP

import requests


class SeriesCollector:
    """A Series Collector is used to build up a list of instances (a DICOM series) as they are received by the modality.
    It stores the (during collection incomplete) series, the Series (Instance) UID, the time the series was last updated
    with a new instance and the information whether the dispatch of the series was started.
    """

    def __init__(self, first_dataset: Dataset) -> None:
        """Initialization of the Series Collector with the first dataset (instance).

        Args:
            first_dataset (Dataset): The first dataset or the regarding series received from the modality.
        """
        # print("SeriesCollector Started 1")
        self.series_instance_uid = first_dataset.SeriesInstanceUID
        self.series: list[Dataset] = [first_dataset]
        self.last_update_time = time.time()
        self.dispatch_started = False
        # print(f"Data Recived : {self.series[0].SeriesInstanceUID}\n")

    def add_instance(self, dataset: Dataset) -> bool:
        # print("add_instance 2 ")
        """Add a dataset to the series collected by this Series Collector if it has the correct Series UID.

        Args:
            dataset (Dataset): The dataset to add.

        Returns:
            bool: `True`, if the Series UID of the dataset to add matched and the dataset was therefore added, `False` otherwise.
        """
        if self.series_instance_uid == dataset.SeriesInstanceUID:
            self.series.append(dataset)
            self.last_update_time = time.time()
            return True

        return False


class SeriesDispatcher:
    """This code provides a template for receiving data from a modality using DICOM.
    Be sure to understand how it works, then try to collect incoming series (hint: there is no attribute indicating how
    many instances are in a series, so you have to wait for some time to find out if a new instance is transmitted).
    For simplification, you can assume that only one series is transmitted at a time.
    You can use the given template, but you don't have to!
    """

    def __init__(self) -> None:
        """Initialize the Series Dispatcher.
        """
        # print("SeriesDispatcher Started 3")
        self.loop: asyncio.AbstractEventLoop
        self.modality_scp = ModalityStoreSCP()
        self.series_collector = None
        self.maximum_wait_time = 1

    async def main(self) -> None:
        # print("Main Function 4")
        """An infinitely running method used as hook for the asyncio event loop.
        Keeps the event loop alive whether or not datasets are received from the modality and prints a message
        Regularly when no datasets are received.
        """
        while True:
            # TODO: Regularly check if new datasets are received and act if they are.
            # Information about Python asyncio: https://docs.python.org/3/library/asyncio.html
            # When datasets are received you should collect and process them
            # (e.g. using `asyncio.create_task(self.run_series_collector()`)
            if self.modality_scp.datalist:
                asyncio.create_task(self.run_series_collectors())
            asyncio.create_task(self.dispatch_series_collector())
            print("Waiting for Modality")
            await asyncio.sleep(0.2)

    async def run_series_collectors(self) -> None:
        # print("run_series_collectors 5")
        """Runs the collection of datasets, which results in the Series Collector being filled.
        """
        # TODO: Get the data from the SCP and start dispatching
        data = self.modality_scp.datalist.pop(0)
        if not self.series_collector:
            self.series_collector = SeriesCollector(data)
        else:
            is_instance = self.series_collector.add_instance(data)
            if not is_instance:
                self.modality_scp.datalist.append(data)
                time.sleep(0.2)

    async def dispatch_series_collector(self) -> None:
        # print("dispatch_series_collector 6")
        """Tries to dispatch a Series Collector, i.e. to finish its dataset collection and scheduling of further
        methods to extract the desired information.
        """
        # Check if the series collector hasn't had an update for a long enough timespan and send the series to the
        # server if it is complete
        # NOTE: This is the last given function, you should create more for extracting the information and
        # sending the data to the server

        if self.series_collector:
            if self.old_to_be_moved():
                data = self.compact_data_to_json()
                # print(data)
                await self.send_put_req(data)
                # todo: Send data to the server to be stored in the database
                self.series_collector = None

    async def send_put_req(self, data):
        jdata = json.dumps(data)
        res = requests.post("http://localhost:5000", headers={'Content-Type': 'application/json'}, data=jdata)
        print("Request sent to server...")
        print(res.json())

    def compact_data_to_json(self):
        data = {
            'SeriesInstanceUID': self.series_collector.series[0].StudyInstanceUID,
            'PatientName': str(self.series_collector.series[0].PatientName),
            'PatientID': self.series_collector.series[0].PatientID,
            'StudyInstanceUID': self.series_collector.series[0].StudyInstanceUID,
            'NumberOfInstances': len(self.series_collector.series)
                    }
        return data



    def old_to_be_moved(self):
        curr_time = time.time()
        if (curr_time - self.series_collector.last_update_time) > self.maximum_wait_time:
            return True
        return False


if __name__ == "__main__":
    """Create a Series Dispatcher object and run it's infinite `main()` method in a event loop.
    """
    engine = SeriesDispatcher()
    engine.loop = asyncio.get_event_loop()
    engine.loop.run_until_complete(engine.main())
