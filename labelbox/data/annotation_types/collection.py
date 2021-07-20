import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Generator, Iterable, Union
from uuid import uuid4

from labelbox.data.annotation_types.label import Label
from labelbox.data.generator import PrefetchGenerator
from labelbox.orm.model import Entity
from labelbox.schema.ontology import OntologyBuilder
from tqdm import tqdm

logger = logging.getLogger(__name__)


class LabelCollection:
    """
    A container for

    """

    def __init__(self, data: Iterable[Label]):
        self._data = data
        self._index = 0

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> Label:
        if self._index == len(self._data):
            raise StopIteration

        value = self._data[self._index]
        self._index += 1
        return value

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, idx: int) -> Label:
        return self._data[idx]

    def assign_schema_ids(
            self, ontology_builder: OntologyBuilder) -> "LabelCollection":
        """
        Based on an ontology:
            - Checks to make sure that the feature names exist in the ontology
            - Updates the names to match the ontology.
        """
        for label in self._data:
            label.assign_schema_ids(ontology_builder)
        return self

    def _ensure_unique_external_ids(self) -> None:
        external_ids = set()
        for label in self._data:
            if label.data.external_id is None:
                label.data.external_id = uuid4()
            else:
                if label.data.external_id in external_ids:
                    raise ValueError(
                        f"External ids must be unique for bulk uploading. Found {label.data.external_id} more than once."
                    )
            external_ids.add(label.data.external_id)

    def add_to_dataset(self,
                       dataset,
                       signer,
                       max_concurrency=20) -> "LabelCollection":
        """
        # It is reccomended to create a new dataset if memory is a concern
        # Also note that this relies on exported data that it cached.
        # So this will not work on the same dataset more frequently than every 30 min.
        # The workaround is creating a new dataset
        """
        self._ensure_unique_external_ids()
        self.add_urls_to_data(signer, max_concurrency=max_concurrency)
        upload_task = dataset.create_data_rows([{
            Entity.DataRow.row_data: label.data.url,
            Entity.DataRow.external_id: label.data.external_id
        } for label in self._data])
        upload_task.wait_til_done()

        data_row_lookup = {
            data_row.external_id: data_row.uid
            for data_row in dataset.export_data_rows()
        }
        for label in self._data:
            label.data.uid = data_row_lookup[label.data.external_id]
        return self

    def add_urls_to_masks(self,
                          signer,
                          max_concurrency=20) -> "LabelCollection":
        """
        Creates a data row id for each data row that needs it. If the data row exists then it skips the row.
        TODO: Add error handling..
        """
        for row in self._apply_threaded(
            [label.add_url_to_masks for label in self._data], max_concurrency,
                signer):
            ...
        return self

    def add_urls_to_data(self, signer, max_concurrency=20) -> "LabelCollection":
        """
        TODO: Add error handling..
        """
        for row in self._apply_threaded(
            [label.add_url_to_data for label in self._data], max_concurrency,
                signer):
            ...
        return self

    def _apply_threaded(self, fns, max_concurrency, *args):
        futures = []
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            for fn in fns:
                futures.append(executor.submit(fn, *args))
            for future in tqdm(as_completed(futures)):
                yield future.result()


class LabelGenerator(PrefetchGenerator):
    """
    Use this class if you have larger data. It is slightly harder to work with
    than the LabelCollection but will be much more memory efficient.
    """

    def __init__(self, data: Generator[Label, None, None], *args, **kwargs):
        self._fns = {}
        super().__init__(data, *args, **kwargs)

    def __iter__(self):
        return self

    def process(self, value):
        for fn in self._fns.values():
            value = fn(value)
        return value

    def as_collection(self) -> "LabelCollection":
        return LabelCollection(data=list(self))

    def assign_schema_ids(
            self, ontology_builder: OntologyBuilder) -> "LabelGenerator":

        def _assign_ids(label: Label):
            label.assign_schema_ids(ontology_builder)
            return label

        self._fns['assign_schema_ids'] = _assign_ids
        return self

    def add_urls_to_data(self, signer: Callable[[bytes],
                                                str]) -> "LabelGenerator":
        """
        Updates masks to have `url` attribute
        Doesn't update masks that already have urls
        """

        def _add_urls_to_data(label: Label):
            label.add_url_to_data(signer)
            return label

        self._fns['_add_urls_to_data'] = _add_urls_to_data
        return self

    def add_to_dataset(self, dataset,
                       signer: Callable[[bytes], str]) -> "LabelGenerator":

        def _add_to_dataset(label: Label):
            label.create_data_row(dataset, signer)
            return label

        self._fns['assign_datarow_ids'] = _add_to_dataset
        return self

    def add_urls_to_masks(self, signer: Callable[[bytes],
                                                 str]) -> "LabelGenerator":
        """
        Updates masks to have `url` attribute
        Doesn't update masks that already have urls
        """

        def _add_urls_to_masks(label: Label):
            label.add_url_to_masks(signer)
            return label

        self._fns['add_urls_to_masks'] = _add_urls_to_masks
        return self

    def __next__(self):
        """
        - Double check that all values have been set.
        - Items could have been processed before any of these modifying functions are called.
        - None of these functions do anything if run more than once so the cost is minimal.
        """
        value = super().__next__()
        return self.process(value)


LabelData = Union[LabelCollection, LabelGenerator]
