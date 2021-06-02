import PySimpleGUI as sg
from datetime import datetime
from os import path
import threading
from recognizer.vosk_recognizer import VoskRecognizer

class MainWin:
  def __init__(self) -> None:
    menu_def = [
      ['&Tools', ['&Talk Capture', '&Web Scraping', '&OCR', '&Epub Maker']],            
      ['&Help', ['&About']]
    ]

    talk_capture_layout = [
      [sg.Text('Language:'), sg.Radio('Mandarin', "LANG", default=True, key='-ZH-'), sg.Radio('English', "LANG", key='-EN-')],
      [sg.Text('Dest Path:'), sg.InputText('D:\Home\Personal\Docs\\talkap', key='-DEST-'), sg.Button('Start', key='-START-'), sg.Button('Save', key='-SAVE-')],
      [sg.HorizontalSeparator(color='black')],
      [sg.Text('Ready', key='-STAT-', size=(70,1))],
      [sg.Multiline('Title:\nContent:', size=(100,40), key='-TRANS-', autoscroll=True)]
    ]

    web_scraping_layout = [
      [sg.Text('WebScraping:')]
    ]
    
    self.layout = [
      [sg.Menu(menu_def, tearoff=False,)],
      [sg.Column(talk_capture_layout, key='-TALK_CAPTURE_LAYOUT-', visible=True)],
      [sg.Column(web_scraping_layout, key='-WEB_SCRAPING_LAYOUT-', visible=False)]
    ]
    self.title = 'No-title'
    self.content = ''
    self.start = False
    self.vosk_rc = VoskRecognizer(model='en')

  def display_transcript(self):
    self.title = self.vosk_rc.getTitle()
    self.content = self.vosk_rc.getContent()
    trans = 'Title: {}\nContent:\n{}'.format(self.title, self.content)
    self.trans_texts.update(trans)

  
  def show(self):
    # Create the window
    sg.theme('Dark Blue 3')   # Add a touch of color
    window = sg.Window('Talkap', self.layout)
    # Create an event loop
    self.radio_zh = window['-ZH-']
    self.stat_text = window['-STAT-']
    self.trans_texts = window['-TRANS-']
    self.start_btn = window['-START-']
    self.dest_input = window['-DEST-']
    self.talk_cap_layout = window['-TALK_CAPTURE_LAYOUT-']
    self.web_scrap_layout = window['-WEB_SCRAPING_LAYOUT-']
    #self.ocr_layout = window['-OCR-LAYOUT-']
    #self.epub_maker_layout = window['-EPUB_MAKER_LAYOUT-']

    while True:
      event, values = window.read(timeout=500)
      if event == 'OK' or event == sg.WIN_CLOSED:
        break
      if event == 'Talk Capture':
        self.talk_cap_layout.update(visible=True)
        self.web_scrap_layout.update(visible=False)
      if event == 'Web Scraping':
        self.talk_cap_layout.update(visible=False)
        self.web_scrap_layout.update(visible=True)
      if event == '-START-':
        self.start = True
        self.start_btn.update(disabled=True)
        model = 'zh' if values['-ZH-'] else 'en'
        self.vosk_rc = VoskRecognizer(model=model)
        self.vosk_rc.idle = False
        trans_thread = threading.Thread(target=self.vosk_rc.start_recognize_loop, daemon=True)
        trans_thread.start()
        self.stat_text.update('Transcripting...')
      if event == '-SAVE-':
        file_name = '{}_{}.txt'.format(self.title, datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
        file_path = path.join(values['-DEST-'], file_name)
        with open(file_path, mode='w', encoding='utf-8') as data_file:
           data_file.write(self.content)
        self.stat_text.update('Ready, transcription is save to {}'.format(file_path))
      if self.vosk_rc.idle == True and self.start == True:
        # transcription is done, should enable button and save file
        self.start == False
        self.start_btn.update(disabled=False)
        self.stat_text.update('Ready')
      if self.vosk_rc.idle == False:
        # should update the transcription
        self.stat_text.update('Transcripting...')
        self.display_transcript()
    
    window.close()
