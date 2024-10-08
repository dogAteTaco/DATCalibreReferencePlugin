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

from qt.core import QCheckBox, QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel,QTextEdit, QHBoxLayout
from qt.core import Qt
from calibre_plugins.datreference.config import prefs


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
		#Title and Icon for the Plugin Menu
		self.setWindowTitle('Reference Plugin')
		self.setWindowIcon(icon)
		
		# Sets the layout for the menu
		self.l = QVBoxLayout()
		self.setLayout(self.l)
		self.setFixedWidth(350)

		self.label = QLabel(prefs['hello_world_msg'])
		self.l.addWidget(self.label)
		self.label.setWordWrap(True)

		self.note = QLabel('Note: The ISBN needs to be added in the metadata in the section of <i>Ids</i>. It needs to be added in the following format <i>isbn:XXXXXXXX</i>. Calibre will automatically verify if the number is valid.')
		self.l.addWidget(self.note)
		self.note.setWordWrap(True)

		self.isbn_cb = QCheckBox('Show ISBN')
		self.l.addWidget(self.isbn_cb)
		self.isbn_cb.setChecked(prefs['show_isbn'])
		self.isbn_cb.stateChanged.connect(self.updateISBNCheckboxState)
		
		self.hide_missing_isbn_cb = QCheckBox('Skip missing ISBN numbers automatically')
		self.l.addWidget(self.hide_missing_isbn_cb)
		self.hide_missing_isbn_cb.setChecked(prefs['skip_missing_isbn'])
		self.hide_missing_isbn_cb.stateChanged.connect(self.updateSkipISBNCheckboxState)

		self.apa_button = QPushButton('Generate APA References', self)
		self.apa_button.clicked.connect(self.generate_apa_reference)
		self.l.addWidget(self.apa_button)

		self.bib_button = QPushButton(
			'Generate BIB References', self)
		self.bib_button.clicked.connect(self.generate_bib_reference)
		self.l.addWidget(self.bib_button)

		self.about_button = QPushButton('About', self)
		self.about_button.clicked.connect(self.about)
		self.l.addWidget(self.about_button)

		self.resize(self.sizeHint())

	def about(self):
		text = get_resources('about.txt')
		QMessageBox.about(self, 'About the ',
				text.decode('utf-8'))
		
	def updateISBNCheckboxState(self, state):
		checked = state
		prefs['show_isbn'] = checked

	def updateSkipISBNCheckboxState(self, state):
		checked = state
		prefs['skip_missing_isbn'] = checked
		
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
		authorNames = metadata.authors
		authorsSorted = metadata.author_sort_map

		publisher = metadata.publisher
		pub_date = metadata.pubdate
		isbn = metadata.isbn
		
		# Checks if the user wants the ISBN to be shown
		show_isbn = prefs['show_isbn']
		skip_missing_isbn = prefs['skip_missing_isbn']
		# Checks which format was asked for
		if format == "BIB":
			# Generates the authors as separated by comma and first name on the start
			authors = ''
			if isinstance(authorNames, list):
				authors = ', '.join(author.strip() for author in authorNames)
			else:
				authors = authorNames.strip()
			reference = f"@book{{{book_id},\n\tauthor ={{{authors}}},\n\tyear = {{{pub_date.strftime('%Y')}}},\n\ttitle = {{{title}}},\n\tpublisher = {{{publisher}}},\n"
			if show_isbn and not (isbn == None and skip_missing_isbn):
				reference = reference + f"\tnote= {{{{ISBN}} {isbn}}}\n"
			reference = reference + f"}}"
		else:
			# Changes the format of the authors to Last Name first based on the Sorted field on the Metadata
			authors = ''
			first = True
			for author in authorNames:
				if first: 
					authors = authors+ authorsSorted[author]
					first = False
				else:
					authors = authors+', & '+authorsSorted[author]
			reference = f"{authors} ({pub_date.strftime('%Y')}). {title}. {publisher}."
			if show_isbn and not (isbn == None and skip_missing_isbn):
				reference = reference + f" ISBN: {isbn}."

		if title == None or authors == None or publisher == None or pub_date == None or (isbn == None and show_isbn and not skip_missing_isbn):
			found_none = True
		return (reference,found_none)
	
	def generate_apa_reference(self):
		self.generate_reference("APA")

	def generate_bib_reference(self):
		self.generate_reference("BIB")
	
	def show_dialog(self, icon, title, message, none_found = False):
		from PyQt5.QtCore import Qt
		from functools import partial
		message = message.rstrip('\n')

		message_box = QDialog()
		message_box.resize(500, 300)
		layout = QVBoxLayout()
		message_box.setLayout(layout)

		label = QLabel()
		layout.addWidget(label)
		message_box.label = label

		text_editor = QTextEdit()
		layout.addWidget(text_editor)
		text_editor.setPlainText(message)
		text_editor.setReadOnly(True)
		message_box.text_edit = QTextEdit()

		# Creates the button layout and adds it to the main layout
		buttons_layout = QHBoxLayout()
		layout.addLayout(buttons_layout)
		# Add stretch to push buttons to the right
		buttons_layout.addStretch(1)
		buttons_layout.setAlignment(Qt.AlignRight)

		copy_button = QPushButton('Copy to Clipboard')
		copy_button.clicked.connect(partial(self.copy_to_clipboard, message))
		buttons_layout.addWidget(copy_button)

		close_button = QPushButton('Close')
		close_button.clicked.connect(message_box.close)
		buttons_layout.addWidget(close_button)
		
		message_box.setWindowTitle(title)
		if none_found:
			label.setText('NOTE: One or more fields were empty.')
		
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