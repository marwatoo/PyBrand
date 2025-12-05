#!/usr/bin/python3

import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QComboBox, QFileDialog, QListView,
    QMessageBox, QSpinBox, QAbstractItemView
)
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt6.QtCore import QSize

# Import my functions
from batch import square_batch, rectangle_batch, cover_batch
from photos import create_post, footix
from files import get_dir
from preview import PreviewWindow

class ImageFolderSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.myimages = []  # full paths of images
        self.dest_folder_path = None
        self.preview_window = None  # keep reference to preview window
        icon_path = os.path.join(get_dir(), 'vic.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.setObjectName("Victoria Badazz's")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Folder or single image selector
        self.folder_selector = QPushButton('Select Folder or Image', self)
        self.folder_selector.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_selector)

        # ListView to show images
        self.image_list_view = QListView(self)
        self.image_model = QStandardItemModel(self.image_list_view)
        self.image_list_view.setModel(self.image_model)
        self.image_list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.image_list_view.setIconSize(QSize(150, 150))
        layout.addWidget(self.image_list_view)

        # Reorder Buttons
        self.up_button = QPushButton('Move Up', self)
        self.up_button.clicked.connect(self.move_up)
        self.up_button.setVisible(False)
        layout.addWidget(self.up_button)

        self.down_button = QPushButton('Move Down', self)
        self.down_button.clicked.connect(self.move_down)
        self.down_button.setVisible(False)
        layout.addWidget(self.down_button)

        # Remove Button
        self.remove_button = QPushButton('Remove', self)
        self.remove_button.clicked.connect(self.remove_item)
        self.remove_button.setVisible(False)
        layout.addWidget(self.remove_button)

        # Logo selector
        self.logo_label = QLabel('Choose Logo:', self)
        self.logo_selector = QComboBox(self)
        self.logo_selector.addItems(['Le360', 'Afrique', 'Sport', 'None'])
        self.logo_selector.setCurrentIndex(0)
        layout.addWidget(QLabel('Choose element:', self))
        layout.addWidget(self.logo_label)
        layout.addWidget(self.logo_selector)

        # Mode selector
        self.mode_selector = QComboBox(self)
        self.mode_selector.addItems(['Rectangle', 'Post', 'Diapo', '16/9', 'Footix'])
        self.mode_selector.setCurrentIndex(0)
        self.mode_selector.currentIndexChanged.connect(self.update_ui)
        layout.addWidget(self.mode_selector)

        # Diapo mode widgets
        self.title_label = QLabel('Title:', self)
        self.title_input = QLineEdit(self)
        self.city_label = QLabel('City:', self)
        self.city_input = QLineEdit(self)
        self.language_list = QListWidget(self)
        self.language_list.addItems(['fr', 'ar'])
        self.title_label.setVisible(False)
        self.title_input.setVisible(False)
        self.city_label.setVisible(False)
        self.city_input.setVisible(False)
        self.language_list.setVisible(False)
        layout.addWidget(self.title_label)
        layout.addWidget(self.title_input)
        layout.addWidget(self.city_label)
        layout.addWidget(self.city_input)
        layout.addWidget(self.language_list)

        # Post mode widgets
        self.post_label = QLabel('Title:', self)
        self.post_input = QLineEdit(self)
        self.word_label = QLabel('Words:', self)
        self.word_input = QLineEdit(self)
        self.tsize_label = QLabel('Title size:', self)
        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(10)
        self.spin_box.setMaximum(200)
        self.spin_box.setValue(100)
        self.tspace_label = QLabel('Title spacing:', self)
        self.spin_box2 = QSpinBox(self)
        self.spin_box2.setMinimum(-50)
        self.spin_box2.setMaximum(50)
        self.spin_box2.setValue(20)
        self.lang_selector = QComboBox(self)
        self.lang_selector.addItems(['fr', 'ar'])
        self.lang_selector.setCurrentIndex(0)
        self.position_list = QComboBox(self)
        self.position_list.addItems(['center', 'right', 'left'])
        self.position_list.setCurrentIndex(0)
        self.tag_list = QComboBox(self)
        self.tag_list.addItems(['none', 'archive', 'illustration'])
        self.tag_list.setCurrentIndex(0)
        self.post_label.setVisible(False)
        self.post_input.setVisible(False)
        self.word_label.setVisible(False)
        self.word_input.setVisible(False)
        self.tsize_label.setVisible(False)
        self.tspace_label.setVisible(False)
        self.spin_box.setVisible(False)
        self.spin_box2.setVisible(False)
        self.lang_selector.setVisible(False)
        self.position_list.setVisible(False)
        self.tag_list.setVisible(False)

        # Preview button (for Post mode)
        self.preview_button = QPushButton('Preview', self)
        self.preview_button.clicked.connect(self.on_preview_clicked)
        self.preview_button.setVisible(False)

        # Connect title changes to update preview visibility
        self.post_input.textChanged.connect(self.check_generate_button_visibility)
        # Also update preview visibility when other relevant fields change
        self.mode_selector.currentIndexChanged.connect(self.check_generate_button_visibility)
        # When tag or position changes, not strictly necessary for visibility, but might be used later
        self.position_list.currentIndexChanged.connect(self.check_generate_button_visibility)
        self.tag_list.currentIndexChanged.connect(self.check_generate_button_visibility)

        layout.addWidget(self.post_label)
        layout.addWidget(self.post_input)
        layout.addWidget(self.word_label)
        layout.addWidget(self.word_input)
        layout.addWidget(self.tsize_label)
        layout.addWidget(self.spin_box)
        layout.addWidget(self.tspace_label)
        layout.addWidget(self.spin_box2)
        layout.addWidget(self.lang_selector)
        layout.addWidget(self.position_list)
        layout.addWidget(self.tag_list)
        layout.addWidget(self.preview_button)

        # Destination folder selector
        self.dest_folder_selector = QPushButton('Select Destination Folder', self)
        self.dest_folder_selector.clicked.connect(self.select_dest_folder)
        layout.addWidget(self.dest_folder_selector)
        self.dest_folder_label = QLabel('Destination Folder Path:', self)
        layout.addWidget(self.dest_folder_label)

        # Generate button
        self.generate_button = QPushButton('Generate', self)
        self.generate_button.clicked.connect(self.on_generate_clicked)
        self.generate_button.setVisible(False)
        layout.addWidget(self.generate_button)

        self.setLayout(layout)
        self.resize(450, 700)

    def update_ui(self):
        mode = self.mode_selector.currentText()
        self.logo_selector.setVisible(True)
        self.logo_label.setVisible(True)
        is_diapo = (mode == 'Diapo')
        self.title_label.setVisible(is_diapo)
        self.title_input.setVisible(is_diapo)
        self.city_label.setVisible(is_diapo)
        self.city_input.setVisible(is_diapo)
        self.language_list.setVisible(is_diapo)
        is_post = (mode == 'Post')
        self.post_label.setVisible(is_post)
        self.post_input.setVisible(is_post)
        self.word_label.setVisible(is_post)
        self.word_input.setVisible(is_post)
        self.tsize_label.setVisible(is_post)
        self.tspace_label.setVisible(is_post)
        self.spin_box.setVisible(is_post)
        self.spin_box2.setVisible(is_post)
        self.lang_selector.setVisible(is_post)
        self.position_list.setVisible(is_post)
        self.tag_list.setVisible(is_post)
        if is_post or mode == 'Footix':
            self.logo_selector.setVisible(False)
            self.logo_label.setVisible(False)
        # Update visibility of preview/generate and reorder buttons
        self.check_generate_button_visibility()
        self.update_reorder_button_visibility()

    def select_folder(self):
        mode = self.mode_selector.currentText()
        if mode in ['Post', 'Footix']:
            file_path, _ = QFileDialog.getOpenFileName(self, 'Select an Image', '', 
                'Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)')
            if file_path:
                self.myimages = [file_path]
                self.image_model.clear()
                file_name = os.path.basename(file_path)
                item = QStandardItem(QIcon(file_path), file_name)
                item.setData(file_path)
                self.image_model.appendRow(item)
        else:
            folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder with Images')
            if folder_path:
                self.image_model.clear()
                self.myimages = []
                image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
                for file_name in os.listdir(folder_path):
                    if any(file_name.lower().endswith(ext) for ext in image_extensions):
                        file_path = os.path.join(folder_path, file_name)
                        self.myimages.append(file_path)
                        item = QStandardItem(QIcon(file_path), file_name)
                        item.setData(file_path)
                        self.image_model.appendRow(item)

        # Ensure UI state updates after selecting (important for preview button)
        self.check_generate_button_visibility()
        self.update_reorder_button_visibility()

    def select_dest_folder(self):
        self.dest_folder_path = QFileDialog.getExistingDirectory(self, 'Select Destination Folder')
        if self.dest_folder_path:
            self.dest_folder_label.setText(f'Destination Folder Path: {self.dest_folder_path}')
            self.check_generate_button_visibility()

    def check_generate_button_visibility(self):
        # Generate button: visible only when there's a dest folder and images
        self.generate_button.setVisible(bool(self.dest_folder_path and self.myimages))

        # Preview button rules:
        mode = self.mode_selector.currentText()
        is_post_mode = (mode == 'Post')
        has_image = bool(self.myimages)
        has_title = bool(self.post_input.text().strip())

        # Show preview when post mode + at least one image selected + title is entered
        self.preview_button.setVisible(is_post_mode and has_image and has_title)

    def update_reorder_button_visibility(self):
        count = self.image_model.rowCount()
        self.up_button.setVisible(count >= 2)
        self.down_button.setVisible(count >= 2)
        self.remove_button.setVisible(count >= 1)

    def move_up(self):
        index = self.image_list_view.currentIndex()
        if index.isValid() and index.row() > 0:
            current_row = index.row()
            # original logic kept as provided
            item_current = self.image_model.takeItem(current_row)
            item_above = self.image_model.takeItem(current_row - 1)
            self.image_model.setItem(current_row, 0, item_above)
            self.image_model.setItem(current_row - 1, 0, item_current)
            self.myimages[current_row - 1], self.myimages[current_row] = self.myimages[current_row], self.myimages[current_row - 1]
            self.update_reorder_button_visibility()
            self.check_generate_button_visibility()

    def move_down(self):
        index = self.image_list_view.currentIndex()
        if index.isValid() and index.row() < self.image_model.rowCount() - 1:
            current_row = index.row()
            # original logic kept as provided
            item_current = self.image_model.takeItem(current_row)
            item_below = self.image_model.takeItem(current_row + 1)
            self.image_model.setItem(current_row, 0, item_below)
            self.image_model.setItem(current_row + 1, 0, item_current)
            self.myimages[current_row + 1], self.myimages[current_row] = self.myimages[current_row], self.myimages[current_row + 1]
            self.update_reorder_button_visibility()
            self.check_generate_button_visibility()

    def remove_item(self):
        index = self.image_list_view.currentIndex()
        if index.isValid():
            self.image_model.removeRow(index.row())
            self.myimages.pop(index.row())
            self.update_reorder_button_visibility()
            self.check_generate_button_visibility()
            

    def on_generate_clicked(self):
        if not self.myimages or not self.dest_folder_path:
            print("No images or destination selected.")
            return

        stime = time.time()
        mode = self.mode_selector.currentText()
        if mode == 'Diapo':
            title = self.title_input.text().upper()
            city = self.city_input.text().upper()
            language = self.language_list.currentItem().text() if self.language_list.currentItem() else 'None'
            square_batch(self.myimages, self.logo_selector.currentText(), self.dest_folder_path, city, title, language)
        elif mode == 'Rectangle':
            rectangle_batch(self.myimages, self.logo_selector.currentText(), self.dest_folder_path)
        elif mode == '16/9':
            cover_batch(self.myimages, self.logo_selector.currentText(), self.dest_folder_path)
        elif mode == 'Post':
            titre = self.post_input.text().upper()
            mot = self.word_input.text().upper()
            create_post(
                self.myimages[0], self.dest_folder_path, 1080, 1350,
                self.position_list.currentText(), titre, mot,
                self.lang_selector.currentText(), self.spin_box.value(),
                self.spin_box2.value(), '#FFFFFF', '#FF7A14',
                self.tag_list.currentText()
            )
        elif mode == 'Footix':
            footix(self.myimages[0], self.dest_folder_path, 'center')

        etime = time.time()
        elapsed_time = etime - stime
        QMessageBox.information(self, 'Message', f"Took {elapsed_time:.2f} seconds to execute.")
        self.myimages.clear()
        self.image_model.clear()
        self.update_ui()

    def on_preview_clicked(self):
        # Validate preconditions
        if not self.myimages:
            QMessageBox.warning(self, "Preview", "No image selected to preview.")
            return
        if self.mode_selector.currentText() != 'Post':
            QMessageBox.warning(self, "Preview", "Preview is only available in Post mode.")
            return
        titre = self.post_input.text().upper().strip()
        if not titre:
            QMessageBox.warning(self, "Preview", "Please enter a title before previewing.")
            return

        mot = self.word_input.text().upper()

        try:
            pil_img = create_post(
                self.myimages[0], "preview", 1080, 1350,
                self.position_list.currentText(), titre, mot,
                self.lang_selector.currentText(), self.spin_box.value(),
                self.spin_box2.value(), '#FFFFFF', '#FF7A14',
                self.tag_list.currentText()
            )
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Failed to create preview:\n{str(e)}")
            return

        # Show preview window and keep a reference so it doesn't get GC'ed
        try:
            self.preview_window = PreviewWindow(pil_img)
            self.preview_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Failed to open preview window:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageFolderSelector()
    window.setWindowTitle("Victoria's Badazz")
    window.show()
    sys.exit(app.exec())
