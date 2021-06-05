import PySimpleGUI as sg
from datetime import datetime
from os import path
import threading
from recognizer.vosk_recognizer import VoskRecognizer
from recognizer.ocr_recognizer import OCRRecognizer

class MainWin:
  def __init__(self) -> None:
    self.menu_def = [
      ['&Tools', ['&Talk Capture', '&Epub Maker']],            
      ['&Help', ['&About']]
    ]

    self.talk_capture_layout = [
      [sg.Text('Language:'), sg.Radio('Mandarin', "LANG", default=True, key='-TALK-ZH-'), sg.Radio('English', "LANG", key='-TALK-EN-')],
      [sg.Text('Dest Path:'), sg.InputText('D:\Home\Personal\Docs\\talkap', key='-TALK-DEST-'), sg.Button('Start', key='-TALK-START-'), sg.Button('Stop', key='-TALK-STOP-'), sg.Button('Save', key='-TALK-SAVE-')],
      [sg.HorizontalSeparator(color='black')],
      [sg.Text('Ready', key='-TALK-STAT-', size=(70,1))],
      [sg.Multiline('Title:\nContent:', size=(100,40), key='-TALK-TRANS-', autoscroll=True)]
    ]

    self.epub_maker_layout = [
      [sg.Text('Title:'), sg.InputText('', key='-EPUB-TITLE-'), sg.Text('Author:'), sg.InputText('', key='-EPUB-AUTHOR-')],
      [sg.Text('Language:'), sg.Radio('Mandarin', "LANG", default=True, key='-EPUB-IMG-ZH-'), sg.Radio('English', "LANG", key='-EPUB-IMG-EN-')],
      [sg.HorizontalSeparator(color='black')],
      [sg.Text('Make Epub from images, image Folder: (images with file name as index)')],
      [sg.In(key='-IMG-FOLDER-'), sg.FolderBrowse(target='-IMG-FOLDER-', key='-IMG-FOLDER-BROWSE-')],
      [sg.Button('Start', key='-EPUB-IMG-START-'), sg.Text('Ready', key='-EPUB-IMG-STAT-', size=(70,1))],
      [sg.HorizontalSeparator(color='black')],
    ]

    self.title = 'No-title'
    self.content = ''
    self.work_dir = path.dirname(path.realpath(__file__))
    self.vosk_rc = VoskRecognizer(model='en')
    self.ocr_rc = OCRRecognizer()

  def make_talk_capture_window(self):
    talk_capture_layout = [
      [sg.Menu(self.menu_def, tearoff=False,)],
      [sg.Column(self.talk_capture_layout, key='-MAIN-LAYOUT-')],
    ]
    print(f'{self.work_dir}\icon.ico')
    return sg.Window('EBook-Tools', talk_capture_layout, finalize=True, icon=f'{self.work_dir}\icon.ico')
  
  def make_epub_maker_window(self):
    epub_maker_layout = [
      [sg.Menu(self.menu_def, tearoff=False,)],
      [sg.Column(self.epub_maker_layout, key='-MAIN-LAYOUT-')],
    ]
    return sg.Window('EBook-Tools', epub_maker_layout, finalize=True, icon=f'{self.work_dir}\icon.ico')

  def display_transcript(self):
    self.title = self.vosk_rc.getTitle()
    self.content = self.vosk_rc.getContent()
    trans = 'Title: {}\nContent:\n{}'.format(self.title, self.content)
    self.talk_trans_texts.update(trans)
  
  def show(self):
    # Create the window
    sg.theme('Dark Blue 3')   # Add a touch of color
    talk_capture_win = self.make_talk_capture_window()
    epub_maker_win = self.make_epub_maker_window()
    epub_maker_win.hide()

    self.talk_stat_text = talk_capture_win['-TALK-STAT-']
    self.talk_trans_texts = talk_capture_win['-TALK-TRANS-']
    self.talk_start_btn = talk_capture_win['-TALK-START-']
    self.epub_img_stat_text = epub_maker_win['-EPUB-IMG-STAT-']
    

    while True:
      window, event, values = sg.read_all_windows(timeout=500)
      # close window
      if event == 'OK' or event == sg.WIN_CLOSED:
        break
      # menu events
      if event == 'Talk Capture':
        epub_maker_win.hide()
        talk_capture_win.un_hide()
      if event == 'Epub Maker':
        epub_maker_win.un_hide()
        talk_capture_win.hide()
      # talk capture window events
      if event == '-TALK-START-':
        self.talk_start_btn.update(disabled=True)
        model = 'zh' if values['-TALK-ZH-'] else 'en'
        self.vosk_rc = VoskRecognizer(model=model)
        self.vosk_rc.idle = False
        trans_thread = threading.Thread(target=self.vosk_rc.start_recognize_loop, daemon=True)
        trans_thread.start()
        self.talk_stat_text.update('Transcripting...')
      if event == '-TALK-STOP-':
        self.vosk_rc.idle = True
      if event == '-TALK-SAVE-':
        file_name = '{}_{}.txt'.format(self.title, datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
        file_path = path.join(values['-TALK-DEST-'], file_name)
        with open(file_path, mode='w', encoding='utf-8') as data_file:
           data_file.write(self.content)
        self.talk_stat_text.update('Ready, transcription is save to {}'.format(file_path))
      if self.vosk_rc.idle == True:
        # transcription is done, should enable button and save file
        self.talk_start_btn.update(disabled=False)
        self.talk_stat_text.update('Ready')
      if self.vosk_rc.idle == False:
        # should update the transcription
        self.talk_stat_text.update('Transcripting...')
        self.display_transcript()
      # epub makter events
      if event == '-EPUB-IMG-START-':
        epub_title = values['-EPUB-TITLE-']
        epub_author = values['-EPUB-AUTHOR-']
        img_folder = values['-IMG-FOLDER-BROWSE-']
        lang = 'chi_sim' if values['-EPUB-IMG-ZH-'] else 'eng'
        epub_path = f'{img_folder}/{epub_title}_{epub_author}.epub'
        if epub_title != '' and epub_author != '' and img_folder != '':
          self.ocr_rc.idle = False
          epub_img_args = {
            'folder_path': img_folder,
            'title': epub_title,
            'author': epub_author,
            'lang': lang
          }
          epub_img_thread = threading.Thread(target=self.ocr_rc.create_epub, daemon=True, kwargs=epub_img_args)
          epub_img_thread.start()
          self.epub_img_stat_text.update(f'Generating Epub file to {epub_path}...')
        else:
          sg.popup('Please specify title, author and images', title='Warning')
      
      self.epub_img_stat_text.update(self.ocr_rc.stat)

    
    window.close()
