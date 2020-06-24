import typing
from pathlib import Path

import qgis.core
from PyQt5 import QtCore
from PyQt5.QtCore import QAbstractItemModel

from .constants import DatasetType


def log_message(message, level=None):
    qgis.core.QgsMessageLog.logMessage(message)


def get_checklists_dir() -> Path:
    base_dir = get_profile_base_path()
    checklists_dir = base_dir / 'checklists'
    if not checklists_dir.is_dir():
        log_message(f'Creating checklists directory at {checklists_dir}...')
        checklists_dir.mkdir(parents=True, exist_ok=True)
    return checklists_dir


def get_profile_base_path() -> Path:
    return Path(qgis.core.QgsApplication.qgisSettingsDirPath())


def match_maplayer_type(type_: qgis.core.QgsMapLayerType) -> typing.Optional[DatasetType]:
    return {
        qgis.core.QgsMapLayerType.VectorLayer: DatasetType.VECTOR,
        qgis.core.QgsMapLayerType.RasterLayer: DatasetType.RASTER,
    }.get(type_)


class TreeNode:

    def __init__(self, parent, row):
        self.parent = parent
        self.row = row
        self.sub_nodes = self._get_children()

    def _get_children(self):
        raise NotImplementedError


class TreeModel(QAbstractItemModel):

    def __init__(self):
        super().__init__()
        self.root_nodes = self._get_root_nodes()

    def _get_root_nodes(self):
        raise NotImplementedError

    def index(self, row: int, column: int, parent: typing.Optional[QtCore.QModelIndex] = QtCore.QModelIndex()):
        if not parent.isValid():
            result = self.createIndex(row, column, self.root_nodes[row])
        else:
            parent_node: TreeNode = parent.internalPointer()
            result = self.createIndex(row, column, parent_node.sub_nodes[row])
        return result

    def parent(self, index: QtCore.QModelIndex):
        if not index.isValid():
            result = QtCore.QModelIndex()
        else:
            node: TreeNode = index.internalPointer()
            if node.parent is None:
                result = QtCore.QModelIndex()
            else:
                result = self.createIndex(node.parent.row, 0, node.parent)
        return result

    def reset(self):
        self.root_nodes = self._get_root_nodes()
        super().reset()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            result = len(self.root_nodes)
        else:
            node: TreeNode = parent.internalPointer()
            result = len(node.sub_nodes)
        return result