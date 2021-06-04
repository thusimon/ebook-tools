import os
import queue
import sounddevice as sd
import vosk
import sys
import json

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
    punct = ''
    if self.temp_segment == '':
      self.pause_count += 1
    else:
      if self.pause_count >= PARAGRAPH_PAUSE:
        # should add '.\n' at the end
        punct = '.\n'
      elif self.pause_count >= PEROID_PAUSE and self.pause_count < PARAGRAPH_PAUSE:
        # should add '.  ' at the end
        punct = '.  '
      elif self.pause_count >= NOISE_PAUSE and self.pause_count < PEROID_PAUSE:
        # should add ', ' at the end
        punct = ', '
      else:
        # here should be noise
        pass
      # reset pause
      self.pause_count = 0
    return punct

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
          if self.idle == True:
            print('end recording')
            self.document.append('.\n')
            break
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
            puncture = self.count_for_pause()
            self.add_punctuation(puncture)
    except KeyboardInterrupt:
      print('\nDone')
    except Exception as e:
      print(e)

  def stop_recognize_loop(self):
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