#!/bin/python3

#This version is using PySide2, it solves Dark theme issue on Openbox, bspwm, i3

import sys
import os
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QComboBox, QFileDialog, QListView,
    QMessageBox, QSpinBox, QAbstractItemView
)
from PySide2.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide2.QtCore import Qt, QSize

from batch import square_batch, rectangle_batch, cover_batch
from photos import create_post, footix
from files import get_dir
import time

class ImageFolderSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.myimages = []  # Initialize the list to store full paths of images
        self.dest_folder_path = None
        icon_path=os.path.join(get_dir(),'vic.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.setObjectName("Victoria Badazz's")
        self.initUI()

    def initUI(self):

        layout = QVBoxLayout()

        # Folder Selector
        self.folder_selector = QPushButton('Select Folder with Images', self)
        self.folder_selector.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_selector)

        # ListView to show images
        self.image_list_view = QListView(self)
        self.image_model = QStandardItemModel(self.image_list_view)
        self.image_list_view.setModel(self.image_model)
        layout.addWidget(self.image_list_view)
        self.image_list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.image_list_view.setIconSize(QSize(150, 150))

        # Reorder Buttons
        self.up_button = QPushButton('Move Up', self)
        self.up_button.clicked.connect(self.move_up)
        self.up_button.setVisible(False)  # Hide initially
        layout.addWidget(self.up_button)

        self.down_button = QPushButton('Move Down', self)
        self.down_button.clicked.connect(self.move_down)
        self.down_button.setVisible(False)  # Hide initially
        layout.addWidget(self.down_button)

        # Remove Button
        self.remove_button = QPushButton('Remove', self)
        self.remove_button.clicked.connect(self.remove_item)
        self.remove_button.setVisible(False)  # Hide initially
        layout.addWidget(self.remove_button)

        # Choose Logo Label and ComboBox
        self.logo_label = QLabel('Choose Logo:', self)

        self.logo_selector = QComboBox(self)
        self.logo_selector.addItems(['Le360', 'Afrique', 'Sport', 'None'])
        self.logo_selector.setCurrentIndex(0)  # Set 'Le360' as the default choice

        #Add logo label and combo
        self.logo_labelS = QLabel('Choose element:', self)
        layout.addWidget(self.logo_labelS)

        # ComboBox with 'Diapo', 'Rectangle', '16/9'
        self.mode_selector = QComboBox(self)
        self.mode_selector.addItems(['Rectangle','Post', 'Diapo', '16/9', 'Footix'])
        self.mode_selector.setCurrentIndex(0)  # Set 'Rectangle' as the default choice
        self.mode_selector.currentIndexChanged.connect(self.update_ui)
        layout.addWidget(self.mode_selector)

        layout.addWidget(self.logo_label)
        layout.addWidget(self.logo_selector)

        # Textboxes and ListBox for 'Diapo' mode
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

        #Elements for 'Post' Mode

        self.post_label = QLabel('Title:', self)
        self.post_input = QLineEdit(self)
        self.word_label = QLabel('Words:', self)
        self.word_input = QLineEdit(self)
        self.tsize_label = QLabel('Title size:', self)
        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(10)  # Minimum value
        self.spin_box.setMaximum(200)  # Maximum value
        self.spin_box.setValue(100)
        self.tspace_label = QLabel('Title spacing:', self)
        self.spin_box2= QSpinBox(self)
        self.spin_box2.setMinimum(-50)  # Minimum value
        self.spin_box2.setMaximum(50)  # Maximum value
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

        # Destination Folder Selector
        self.dest_folder_selector = QPushButton('Select Destination Folder', self)
        self.dest_folder_selector.clicked.connect(self.select_dest_folder)
        layout.addWidget(self.dest_folder_selector)

        # Label to show selected destination folder path
        self.dest_folder_label = QLabel('Destination Folder Path:', self)
        layout.addWidget(self.dest_folder_label)

        # Generate Button
        self.generate_button = QPushButton('Generate', self)
        self.generate_button.clicked.connect(self.on_generate_clicked)
        self.generate_button.setVisible(False)  # Hide the button initially
        layout.addWidget(self.generate_button)

        self.setLayout(layout)
        self.resize(450, 600)

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

        if is_post==True:
            self.logo_selector.setVisible(False)
            self.logo_label.setVisible(False)

        is_footix = (mode == 'Footix')
        
        if is_footix==True:
            self.logo_selector.setVisible(False)
            self.logo_label.setVisible(False)

        self.check_generate_button_visibility()
        self.update_reorder_button_visibility()

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder with Images')
        if folder_path:
            self.image_model.clear()
            self.myimages = []  # Clear previous image paths
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp' '.PNG', '.JPG', '.JPEG', '.BMP', '.GIF', '.WEBP']
            for file_name in os.listdir(folder_path):
                if any(file_name.lower().endswith(ext) for ext in image_extensions):
                    file_path = os.path.join(folder_path, file_name)
                    self.myimages.append(file_path)  # Store the full path
                    item = QStandardItem(QIcon(file_path), file_name)
                    item.setData(file_path)  # Store the full path in the item
                    self.image_model.appendRow(item)
            print("Selected folder:", folder_path)
            print("Image paths:", self.myimages)
            self.check_generate_button_visibility()
            self.update_reorder_button_visibility()

    def select_dest_folder(self):
        self.dest_folder_path = QFileDialog.getExistingDirectory(self, 'Select Destination Folder')
        if self.dest_folder_path:
            self.dest_folder_label.setText(f'Destination Folder Path: {self.dest_folder_path}')
            print("Selected destination folder:", self.dest_folder_path)
            self.check_generate_button_visibility()

    def check_generate_button_visibility(self):
        if self.dest_folder_path and self.myimages:
            self.generate_button.setVisible(True)
        else:
            self.generate_button.setVisible(False)

    def update_reorder_button_visibility(self):
        if self.image_model.rowCount() >= 2:
            self.up_button.setVisible(True)
            self.down_button.setVisible(True)
            self.remove_button.setVisible(True)
        elif self.image_model.rowCount() == 1:
            self.up_button.setVisible(False)
            self.down_button.setVisible(False)
            self.remove_button.setVisible(True)
        elif self.image_model.rowCount() <= 0:
            self.up_button.setVisible(False)
            self.down_button.setVisible(False)
            self.remove_button.setVisible(False)
        else:
            self.up_button.setVisible(False)
            self.down_button.setVisible(False)
            self.remove_button.setVisible(False)

    def move_up(self):
        index = self.image_list_view.currentIndex()
        if index.isValid() and index.row() > 0:
            current_row = index.row()
            
            # Get items
            item_current = self.image_model.takeItem(current_row)
            item_above = self.image_model.takeItem(current_row - 1)
            
            # Swap items
            self.image_model.setItem(current_row,0,item_above)
            self.image_model.setItem(current_row-1,0,item_current)
            ix=self.image_model.index(current_row-1,0)
            self.image_list_view.setCurrentIndex(ix)
            
            # Update myimages list
            self.myimages[current_row - 1], self.myimages[current_row] = self.myimages[current_row], self.myimages[current_row - 1]
            
            # Update button visibility
            self.update_reorder_button_visibility()

    def move_down(self):
        index = self.image_list_view.currentIndex()
        if index.isValid() and index.row() < self.image_model.rowCount() - 1:
            current_row = index.row()
            
            # Get items
            item_current = self.image_model.takeItem(current_row)
            item_below = self.image_model.takeItem(current_row + 1)
            
            # Swap items
            self.image_model.setItem(current_row,0,item_below)
            self.image_model.setItem(current_row+1,0,item_current)
            ix=self.image_model.index(current_row+1,0)
            self.image_list_view.setCurrentIndex(ix)
            # Update myimages list
            self.myimages[current_row + 1], self.myimages[current_row] = self.myimages[current_row], self.myimages[current_row + 1]
            
            # Set the current index to the moved item
            new_index = self.image_model.index(current_row + 1, 0)  # row, column
            self.image_list_view.setCurrentIndex(new_index)
            
            # Update button visibility
            self.update_reorder_button_visibility()

    def remove_item(self):
        index = self.image_list_view.currentIndex()
        if index.isValid():
            # Remove item from the model
            self.image_model.removeRow(index.row())
            # Remove corresponding path from myimages
            self.myimages.pop(index.row())
            self.update_reorder_button_visibility()

    def on_generate_clicked(self):
        if not self.myimages:
            print("No images selected.")
            return

        if self.dest_folder_path:
            stime=time.time()
            print(f"Selected images: {self.myimages}")
            print(f"Destination folder: {self.dest_folder_path}")
            print("Processing images...")
            
            if self.mode_selector.currentText() == 'Diapo':
                title = self.title_input.text().upper()
                city = self.city_input.text().upper()
                language = self.language_list.currentItem().text() if self.language_list.currentItem() else 'None'

                square_batch(self.myimages,self.logo_selector.currentText(),self.dest_folder_path,city,title,language)
            elif self.mode_selector.currentText() == 'Rectangle':
                rectangle_batch(self.myimages, self.logo_selector.currentText(), self.dest_folder_path)
            elif self.mode_selector.currentText() == '16/9':
                cover_batch(self.myimages, self.logo_selector.currentText(), self.dest_folder_path)
            elif self.mode_selector.currentText() == 'Post':
                titre=self.post_input.text().upper()
                mot=self.word_input.text().upper()
                create_post(self.myimages[0],self.dest_folder_path,1080,1350,self.position_list.currentText(),titre,mot,self.lang_selector.currentText(),self.spin_box.value(),self.spin_box2.value(),'#FFFFFF','#FF7A14',self.tag_list.currentText())
            elif self.mode_selector.currentText()=='Footix':
                footix(self.myimages[0],self.dest_folder_path,'center')
            # Show message box
            print("Generate action executed.")
            etime=time.time()
            elapsed_time=etime-stime
            print(f"took {elapsed_time:.6f} seconds to execute.")
            QMessageBox.information(self, 'Message', f"took {elapsed_time:.6f} seconds to execute.")
            self.myimages.clear()
            self.image_model.clear()
            self.update_ui()
        else:
            print("No destination folder selected.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageFolderSelector()
    ex.setWindowTitle("Victoria's Badazz")
    ex.show()
    sys.exit(app.exec_())
