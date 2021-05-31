import os
import queue
import sounddevice as sd
import vosk
import sys
import json

END_PAUSE = 100
PARAGRAPH_PAUSE = 25
PEROID_PAUSE = 10
NOISE_PAUSE = 2

class VoskRecognizer:
  def __init__(self, model='en') -> None:
    self.model = model
    self.q = queue.Queue()
    self.document = []
    self.temp_segment = ''
    self.pause_count = 0
    self.trans_added = False
    self.sample_rate = 44000
    self.idle = True

  def callback(self, indata, frames, time, status):
    '''This is called (from a separate thread) for each audio block.'''
    if status:
      print(status, file=sys.stderr)
    self.q.put(bytes(indata))

  def count_for_pause(self):
    # if there is continous empty string for counts times, return true
    check_count = {'end': False, 'punct': ''}
    if self.temp_segment == '':
      self.pause_count += 1
      if self.pause_count >= END_PAUSE:
        # should end the recognition
        check_count = {'end': True, 'punct': ''}
      else:
        check_count = {'end': False, 'punct': ''}
    else:
      if self.pause_count >= PARAGRAPH_PAUSE:
        # should add '.\n' at the end
        check_count = {'end': False, 'punct': '.\n'}
      elif self.pause_count >= PEROID_PAUSE and self.pause_count < PARAGRAPH_PAUSE:
        # should add '.  ' at the end
        check_count = {'end': False, 'punct': '.  '}
      elif self.pause_count >= NOISE_PAUSE and self.pause_count < PEROID_PAUSE:
        # should add ', ' at the end
        check_count = {'end': False, 'punct': ', '}
      else:
        # here should be noise
        pass
      # reset pause
      self.pause_count = 0
    return check_count

  def add_punctuation(self, punctuation):
    self.temp_segment = self.temp_segment.strip(',.\n') + punctuation
    if self.trans_added and punctuation != '' and len(self.document) > 0:
      # should add the punctuation to document last segment
      self.document[-1] += punctuation
      self.trans_added = False

  def start_recognize_loop(self):
    try:
      if self.model is None:
        model_name = 'model_en'
      else:
        model_name = 'model_' + self.model
      if not os.path.exists(model_name):
        print ('Please download a model for your language from https://alphacephei.com/vosk/models')
        print ('and unpack as "model_<lang>" in the root folder.')
        return
      device_info = sd.query_devices(None, 'input')
      self.sample_rate = int(device_info['default_samplerate'])

      model = vosk.Model(model_name)
      self.idle = False
      with sd.RawInputStream(samplerate=self.sample_rate, blocksize = 8000, dtype='int16',
        channels=1, callback=self.callback):
        print('#' * 80)
        print('Press Ctrl+C to stop the recording')
        print('#' * 80)

        rec = vosk.KaldiRecognizer(model, self.sample_rate)
        while True:
          data = self.q.get()
          if rec.AcceptWaveform(data):
            recJson = json.loads(rec.Result())
            last_segment = recJson['text']
            if len(last_segment) > 0:
              if self.model == 'zh':
                last_segment = last_segment.replace(' ', '')
              self.document.append(last_segment)
              self.trans_added = True
          else:
            recJson = json.loads(rec.PartialResult())
            partial = recJson['partial']
            if self.model == 'zh':
              partial = partial.replace(' ', '')
            self.temp_segment = partial
            #storge and trscript segment and partial segment
            pause_check = self.count_for_pause()
            if pause_check['end']:
              print('Paused long enough, end recording')
              self.document.append('.\n')
              break
            else:
              # add punctionation at the end of last transcription
              self.add_punctuation(pause_check['punct'])

    except KeyboardInterrupt:
      print('\nDone')
    except Exception as e:
      print(e)

    self.idle = True

  def getTitle(self):
    if len(self.document) > 0:
      return self.document[0].strip(',.\n')
    else:
      return ''
  
  def getContent(self):
    if len(self.document) > 0:
      return ''.join(self.document[1:]) + self.temp_segment
    else:
      return ''