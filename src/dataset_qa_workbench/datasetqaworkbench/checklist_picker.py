import json
import typing
from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from . import models
from . import utils
from .constants import (
    ChecklistModelColumn,
    CustomDataRoles,
)

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
UI_DIR = Path(__file__).parents[1] / "ui"
FORM_CLASS, _ = uic.loadUiType(
    str(UI_DIR / 'checklist_picker.ui'))


class ChecklistPicker(QtWidgets.QDialog, FORM_CLASS):
    button_box: QtWidgets.QDialogButtonBox
    checklist_save_path_la: QtWidgets.QLabel
    checklists_tv: QtWidgets.QTreeView
    delete_checklist_pb: QtWidgets.QPushButton

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(ChecklistPicker, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.delete_checklist_pb.setEnabled(False)
        self.delete_checklist_pb.clicked.connect(self.delete_checklist)
        self.checklist_save_path_la.setText(f'Checklists are loaded from {utils.get_checklists_dir()}')
        checklists = models.load_checklists()
        self.model = QtGui.QStandardItemModel(len(checklists), 3)
        self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        self.checklists_tv.setModel(self.model)
        self.checklists_tv.selectionModel().selectionChanged.connect(self.enable_checklist_actions)
        self.checklists_tv.doubleClicked.connect(
            self.button_box.button(self.button_box.Ok).click)
        self.model.rowsRemoved.connect(self.toggle_delete_checklist_button)
        self.button_box.button(self.button_box.Ok).setEnabled(False)
        self.load_checklists(checklists)

    def enable_checklist_actions(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        button = self.button_box.button(self.button_box.Ok)
        button.setEnabled(bool(len(selected.indexes())))
        self.delete_checklist_pb.setEnabled(bool(len(selected.indexes())))

    def toggle_delete_checklist_button(self, parent: QtCore.QModelIndex, first: int, last: int):
        self.delete_checklist_pb.setEnabled(self.model.rowCount() != 0)

    def delete_checklist(self):
        idx = self.checklists_tv.currentIndex()
        if idx.isValid():
            model = self.checklists_tv.model()
            identifier_index = model.index(idx.row(), 0)
            checklist = identifier_index.data(role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
            path = utils.get_checklists_dir() / f'{sanitize_checklist_name(checklist.name)}.json'
            try:
                path.unlink()
            except FileNotFoundError as exc:
                utils.log_message(str(exc))
            else:
                model.removeRow(idx.row())

    def load_checklists(self, checklists: typing.List[models.CheckList]):
        self.checklists_tv.selectionModel().select(QtCore.QItemSelection(), QtCore.QItemSelectionModel.Clear)
        self.model.clear()
        self.model.setHorizontalHeaderLabels([i.name.replace('_', ' ').capitalize() for i in ChecklistModelColumn])
        for row_index, checklist in enumerate(checklists):
            checklist: models.CheckList
            identifier_item = QtGui.QStandardItem(str(checklist.identifier))
            identifier_item.setData(checklist, role=CustomDataRoles.CHECKLIST_DOWNLOADER_IDENTIFIER.value)
            self.model.setItem(row_index, ChecklistModelColumn.IDENTIFIER.value, identifier_item)
            self.model.setItem(
                row_index, ChecklistModelColumn.NAME.value, QtGui.QStandardItem(checklist.name))
            self.model.setItem(
                row_index,
                ChecklistModelColumn.DATASET_TYPE.value,
                QtGui.QStandardItem(checklist.dataset_type.value)
            )
            self.model.setItem(
                row_index,
                ChecklistModelColumn.APPLICABLE_TO.value,
                QtGui.QStandardItem(checklist.validation_artifact_type.value)
            )
        # self.checklists_tv.setModel(self.model)
        self.checklists_tv.setColumnHidden(ChecklistModelColumn.IDENTIFIER.value, True)
        header = self.checklists_tv.header()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        # self.checklists_tv.setSortingEnabled(True)
        # self.checklists_tv.sortByColumn(ChecklistModelColumn.DATASET_TYPES.value, QtCore.Qt.DescendingOrder)


def sanitize_checklist_name(name: str) -> str:
    return name.replace(' ', '_').lower()
