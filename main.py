#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__   = 'GPL v3'
__copyright__ = '2024, dogAteTaco'
__docformat__ = 'restructuredtext en'

if False:
    # This is here to keep my python error checker from complaining about
    # the builtin functions that will be defined by the plugin loading system
    # You do not need this code in your plugins
    get_icons = get_resources = None

from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel

from calibre_plugins.interface_demo.config import prefs


class DemoDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config

        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel(prefs['hello_world_msg'])
        self.l.addWidget(self.label)

        self.setWindowTitle('Reference Plugin')
        self.setWindowIcon(icon)

        self.about_button = QPushButton('About', self)
        self.about_button.clicked.connect(self.about)
        self.l.addWidget(self.about_button)

        self.apa_button = QPushButton(
            'Generate APA References', self)
        self.apa_button.clicked.connect(self.generate_apa_reference)
        self.l.addWidget(self.apa_button)

        self.bib_button = QPushButton(
            'Generate BIB References', self)
        self.bib_button.clicked.connect(self.generate_bib_reference)
        self.l.addWidget(self.bib_button)


        self.resize(self.sizeHint())

    def about(self):
        text = get_resources('about.txt')
        QMessageBox.about(self, 'About the ',
                text.decode('utf-8'))
        
    def generate_reference(self, format):
        from calibre.ebooks.metadata.meta import set_metadata
        from calibre.gui2 import error_dialog, info_dialog

        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, 'Cannot generate References',
                             'No books selected', show=True)
        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        
        reference_text = ''
        found_any_none = False
        for book_id in ids:
            result, found_none = self.get_reference(book_id,format)
            reference_text = reference_text + result +'\n\n'
            if found_none:
                found_any_none = True
        if found_any_none:
            self.show_dialog(QMessageBox.Warning, f'Empty fields found | {format} Reference',reference_text, found_any_none)
        else:
            self.show_dialog(QMessageBox.Information, f'{format} Reference',reference_text, found_any_none)
            
    def get_reference(self, book_id, format):

        found_none = False
        db = self.db.new_api
        metadata = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
        
        title = metadata.title
        authors = metadata.authors
        if isinstance(authors, list):
            authors = ', '.join(author.strip() for author in authors)
        else:
            authors = authors.strip()
        publisher = metadata.publisher
        pub_date = metadata.pubdate
        isbn = metadata.isbn

        if format == "BIB":
            reference = f"@book{{{book_id},<br/>&emsp;author ={{{authors}}},<br/>&emsp;year = {{{pub_date.strftime('%Y')}}},<br/>&emsp;title = {{{title}}},<br/>&emsp;publisher = {{{publisher}}},<br/>&emsp;note= {{{{ISBN}} {isbn}}}<br/>}}<br/><br/>"
        else:
            reference = f"{authors} ({pub_date.strftime('%Y')}). {title}. {publisher}. ISBN: {isbn}<br/>"

        if title == None or authors == None or publisher == None or pub_date == None or isbn == None:
            found_none = True
        return (reference,found_none)
    
    def generate_apa_reference(self):
        self.generate_reference("APA")

    def generate_bib_reference(self):
        self.generate_reference("BIB")
    
    def show_dialog(self, icon, title, message, none_found = False):
        from PyQt5.QtCore import Qt
        from functools import partial

        message_box = QMessageBox()
        message_box.setWindowTitle(title)
        message_box.setTextFormat(Qt.RichText)
        message_box.setText('<b>NOTE: One or more values have been found empty.</b><br/><br/>'+message)
        message_box.setIcon(icon)
        message_box.setStandardButtons(QMessageBox.Close)
        message_box.setDefaultButton(QMessageBox.Close)

        copy_button = message_box.addButton("Copy to Clipboard", QMessageBox.ActionRole)
        copy_button.clicked.connect(partial(self.copy_to_clipboard, message.replace('<br/>','\n').replace('&emsp;','\t')))
        # Show the message box and return the result
        return message_box.exec_()

    # Example function to copy text to clipboard
    def copy_to_clipboard(self,text):
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QClipboard

        clipboard = QApplication.clipboard()
        clipboard.setText(text)


    def config(self):
        self.do_user_config(parent=self)
        # Apply the changes
        self.label.setText(prefs['hello_world_msg'])


class CopyDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config

        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel(prefs['hello_world_msg'])
        self.l.addWidget(self.label)

        self.setWindowTitle('Reference Plugin')
        self.setWindowIcon(icon)

        self.apa_button = QPushButton(
            'Copy', self)
        self.apa_button.clicked.connect(self.generate_apa_reference)
        self.l.addWidget(self.apa_button)

        self.resize(self.sizeHint())