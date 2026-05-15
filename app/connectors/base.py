from abc import ABC, abstractmethod
import pandas as pd
from app.schemas import SourceDefinition


class Connector(ABC):
    def __init__(self, source: SourceDefinition):
        self.source = source

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        raise NotImplementedError
