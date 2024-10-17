import logging
from typing import Callable, Generator, Iterable, Union


from ..generator import PrefetchGenerator
from .label import Label

logger = logging.getLogger(__name__)


class LabelGenerator(PrefetchGenerator):
    """
    A container for interacting with a large collection of labels.
    For a small number of labels, just use a list of Label objects.
    """

    def __init__(self, data: Generator[Label, None, None], *args, **kwargs):
        self._fns = {}
        super().__init__(data, *args, **kwargs)

    def add_url_to_masks(
        self, signer: Callable[[bytes], str]
    ) -> "LabelGenerator":
        """
        Creates signed urls for all masks in the LabelGenerator.
        Multiple masks can reference the same MaskData so this makes sure we only upload that url once.
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

        self._fns["add_url_to_masks"] = _add_url_to_masks
        return self

    def register_background_fn(
        self, fn: Callable[[Label], Label], name: str
    ) -> "LabelGenerator":
        """
        Allows users to add arbitrary io functions to the generator.
        These functions will be exectuted in parallel and added to a prefetch queue.

        Args:
            fn: Callable that modifies a label and then returns the same label
                - For performance reasons, this function shouldn't run if the object already has the desired state.
            name: Register the name of the function. If the name already exists, then the function will be replaced.
        """
        self._fns[name] = fn
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


LabelCollection = Union[LabelGenerator, Iterable[Label]]
