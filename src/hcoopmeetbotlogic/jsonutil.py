# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
JSON utilities.
"""
from datetime import datetime

import cattr


class CattrConverter(cattr.Converter):
    """
    Cattr converter that knows how to correctly serialize/deserialize datetime to an ISO 8601 timestamp.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_unstructure_hook(datetime, lambda datetime: datetime.isoformat() if datetime else None)  # type: ignore
        self.register_structure_hook(datetime, lambda string, _: datetime.fromisoformat(string) if string else None)
