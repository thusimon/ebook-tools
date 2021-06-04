import PySimpleGUI as sg
from datetime import datetime
from os import path
import threading
from recognizer.vosk_recognizer import VoskRecognizer

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
      [sg.HorizontalSeparator(color='black')],
      [sg.Text('Make Epub from images')],
      [sg.Text('Image Folder: (images with file name as index)'), sg.InputText('', key='-EPUB-IMG-DEST-')],
      [sg.Button('Start', key='-EPUB-IMG-MAKE-')],
      [sg.HorizontalSeparator(color='black')],
    ]

    self.title = 'No-title'
    self.content = ''
    self.vosk_rc = VoskRecognizer(model='en')

  def make_talk_capture_window(self):
    talk_capture_layout = [
      [sg.Menu(self.menu_def, tearoff=False,)],
      [sg.Column(self.talk_capture_layout, key='-MAIN-LAYOUT-')],
    ]
    return sg.Window('EBook-Tools', talk_capture_layout, finalize=True)
  
  def make_epub_maker_window(self):
    epub_maker_layout = [
      [sg.Menu(self.menu_def, tearoff=False,)],
      [sg.Column(self.epub_maker_layout, key='-MAIN-LAYOUT-')],
    ]
    return sg.Window('EBook-Tools', epub_maker_layout, finalize=True)

  def display_transcript(self):
    self.title = self.vosk_rc.getTitle()
    self.content = self.vosk_rc.getContent()
    trans = 'Title: {}\nContent:\n{}'.format(self.title, self.content)
    self.trans_texts.update(trans)
  
  def show(self):
    # Create the window
    sg.theme('Dark Blue 3')   # Add a touch of color
    talk_capture_win = self.make_talk_capture_window()
    epub_maker_win = self.make_epub_maker_window()
    epub_maker_win.hide()

    self.radio_zh = talk_capture_win['-TALK-ZH-']
    self.stat_text = talk_capture_win['-TALK-STAT-']
    self.trans_texts = talk_capture_win['-TALK-TRANS-']
    self.start_btn = talk_capture_win['-TALK-START-']
    self.dest_input = talk_capture_win['-TALK-DEST-']

    while True:
      window, event, values = sg.read_all_windows(timeout=500)
      if event == 'OK' or event == sg.WIN_CLOSED:
        break
      if event == 'Talk Capture':
        epub_maker_win.hide()
        talk_capture_win.un_hide()
      if event == 'Epub Maker':
        epub_maker_win.un_hide()
        talk_capture_win.hide()
      if event == '-TALK-START-':
        self.start_btn.update(disabled=True)
        model = 'zh' if values['-TALK-ZH-'] else 'en'
        self.vosk_rc = VoskRecognizer(model=model)
        self.vosk_rc.idle = False
        trans_thread = threading.Thread(target=self.vosk_rc.start_recognize_loop, daemon=True)
        trans_thread.start()
        self.stat_text.update('Transcripting...')
      if event == '-TALK-STOP-':
        self.vosk_rc.idle = True
      if event == '-TALK-SAVE-':
        file_name = '{}_{}.txt'.format(self.title, datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
        file_path = path.join(values['-TALK-DEST-'], file_name)
        with open(file_path, mode='w', encoding='utf-8') as data_file:
           data_file.write(self.content)
        self.stat_text.update('Ready, transcription is save to {}'.format(file_path))
      if self.vosk_rc.idle == True:
        # transcription is done, should enable button and save file
        self.start_btn.update(disabled=False)
        self.stat_text.update('Ready')
      if self.vosk_rc.idle == False:
        # should update the transcription
        self.stat_text.update('Transcripting...')
        self.display_transcript()
    
    window.close()
