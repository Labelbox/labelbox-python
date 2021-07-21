import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Generator, Iterable, Union
from uuid import uuid4

from tqdm import tqdm

from labelbox.schema.ontology import OntologyBuilder
from labelbox.orm.model import Entity
from ..generator import PrefetchGenerator
from .label import Label

logger = logging.getLogger(__name__)


class LabelCollection:
    """
    A container for interacting with a collection of labels.
    Less memory efficient than LabelGenerator but more performant and convenient to use.
    Use on smaller datasets.
    """

    def __init__(self, data: Iterable[Label]):
        self._data = data
        self._index = 0

    def assign_schema_ids(
            self, ontology_builder: OntologyBuilder) -> "LabelCollection":
        """
        Adds schema ids to all FeatureSchema objects in the Labels.
        This is necessary for MAL.

        Args:
            ontology_builder: The ontology that matches the feature names assigned to objects in this LabelCollection
        Returns:
            LabelCollection. useful for chaining these modifying functions
        """
        for label in self._data:
            label.assign_schema_ids(ontology_builder)
        return self

    def add_to_dataset(self,
                       dataset: "Entity.Dataset",
                       signer: Callable[[bytes], str],
                       max_concurrency=20) -> "LabelCollection":
        """
        Creates data rows from each labels data object and attaches the data to the given dataset.
        Updates the label's data object to have the same external_id and uid as the data row.
        It is reccomended to create a new dataset if memory is a concern because all dataset data rows are exported to make this faster.
        Also note that this relies on exported data that it cached.
        So this will not work on the same dataset more frequently than every 30 min.
        The workaround is creating a new dataset each time this function is used.

        Args:
            dataset: labelbox dataset object to add the new data row to
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            LabelCollection with updated references to new data rows
        """
        self._ensure_unique_external_ids()
        self.add_url_to_data(signer, max_concurrency=max_concurrency)
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

    def add_url_to_masks(self, signer, max_concurrency=20) -> "LabelCollection":
        """
        Creates signed urls for all masks in the LabelCollection.
        Multiple masks can reference the same RasterData mask so this makes sure we only upload that url once.
        Only uploads url if one doesn't already exist.

        Args:
            signer: A function that accepts bytes and returns a signed url.
            max_concurrency: how many threads to use for uploading.
                Should be balanced to match the signing services capabilities.
        Returns:
            LabelCollection with updated references to the new mask urls
        """
        for row in self._apply_threaded(
            [label.add_url_to_masks for label in self._data], max_concurrency,
                signer):
            ...
        return self

    def add_url_to_data(self, signer, max_concurrency=20) -> "LabelCollection":
        """
        Creates signed urls for the data
        Only uploads url if one doesn't already exist.

        Args:
            signer: A function that accepts bytes and returns a signed url.
            max_concurrency: how many threads to use for uploading.
                Should be balanced to match the signing services capabilities.
        Returns:
            LabelCollection with updated references to the new data urls
        """
        for row in self._apply_threaded(
            [label.add_url_to_data for label in self._data], max_concurrency,
                signer):
            ...
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

    def __iter__(self) -> "LabelCollection":
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

    def _apply_threaded(self, fns, max_concurrency, *args):
        futures = []
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            for fn in fns:
                futures.append(executor.submit(fn, *args))
            for future in tqdm(as_completed(futures)):
                yield future.result()


class LabelGenerator(PrefetchGenerator):
    """
    A container for interacting with a collection of labels.

    Use this class if you have larger data. It is slightly harder to work with
    than the LabelCollection but will be much more memory efficient.
    """

    def __init__(self, data: Generator[Label, None, None], *args, **kwargs):
        self._fns = {}
        super().__init__(data, *args, **kwargs)

    def as_collection(self) -> "LabelCollection":
        return LabelCollection(data=list(self))

    def assign_schema_ids(
            self, ontology_builder: OntologyBuilder) -> "LabelGenerator":

        def _assign_ids(label: Label):
            label.assign_schema_ids(ontology_builder)
            return label

        self._fns['assign_schema_ids'] = _assign_ids
        return self

    def add_url_to_data(self, signer: Callable[[bytes],
                                               str]) -> "LabelGenerator":
        """
        Creates signed urls for the data
        Only uploads url if one doesn't already exist.

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            LabelGenerator that signs urls as data is accessed
        """

        def _add_url_to_data(label: Label):
            label.add_url_to_data(signer)
            return label

        self._fns['_add_url_to_data'] = _add_url_to_data
        return self

    def add_to_dataset(self, dataset: "Entity.Dataset",
                       signer: Callable[[bytes], str]) -> "LabelGenerator":
        """
        Creates data rows from each labels data object and attaches the data to the given dataset.
        Updates the label's data object to have the same external_id and uid as the data row.

        This is a lot slower than LabelCollection.add_to_dataset but also more memory efficient.

        Args:
            dataset: labelbox dataset object to add the new data row to
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            LabelGenerator that updates references to the new data rows as data is accessed
        """

        def _add_to_dataset(label: Label):
            label.create_data_row(dataset, signer)
            return label

        self._fns['assign_datarow_ids'] = _add_to_dataset
        return self

    def add_url_to_masks(self, signer: Callable[[bytes],
                                                str]) -> "LabelGenerator":
        """
        Creates signed urls for all masks in the LabelGenerator.
        Multiple masks can reference the same RasterData mask so this makes sure we only upload that url once.
        Only uploads url if one doesn't already exist.

        Args:
            signer: A function that accepts bytes and returns a signed url.
            max_concurrency: how many threads to use for uploading.
                Should be balanced to match the signing services capabilities.
        Returns:
            LabelGenerator that updates references to the new mask urls as data is accessed
        """

        def _add_url_to_masks(label: Label):
            label.add_url_to_masks(signer)
            return label

        self._fns['add_url_to_masks'] = _add_url_to_masks
        return self

    def __iter__(self):
        return self

    def _process(self, value):
        for fn in self._fns.values():
            value = fn(value)
        return value

    def __next__(self):
        """
        Double checks that all values have been set.
        Items could have been processed before any of these modifying functions are called.
        None of these functions do anything if run more than once so the cost is minimal.
        """
        value = super().__next__()
        return self._process(value)


LabelData = Union[LabelCollection, LabelGenerator]
