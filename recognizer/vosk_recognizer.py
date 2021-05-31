import os
import queue
import sounddevice as sd
import vosk
import sys
import json

END_PAUSE = 100
PARAGRAPH_PAUSE = 20
PEROID_PAUSE = 10

class VoskRecognizer:
  def __init__(self, model='en') -> None:
    self.model = model
    self.q = queue.Queue()
    self.document = ['']
    self.last_segment = ''
    self.pause_count = 0
    self.wait_to_add = False
    self.temp_add = False
    self.sample_rate = 44000
    self.idle = True

  def callback(self, indata, frames, time, status):
    '''This is called (from a separate thread) for each audio block.'''
    if status:
      print(status, file=sys.stderr)
    self.q.put(bytes(indata))

  def count_for_pause(self, partial):
    # if there is continous empty string for counts times, return true
    check_count = {'end': False, 'res': ''}
    if partial == '':
      self.pause_count += 1
      if self.pause_count >= END_PAUSE:
        # should end the recognition
        check_count = {'end': True, 'res': ''}
      else:
        check_count = {'end': False, 'res': ''}
    else:
      if self.pause_count >= PARAGRAPH_PAUSE:
        # should add '.\n' at the end
        check_count = {'end': False, 'res': '.\n'}
      elif self.pause_count >= PEROID_PAUSE and self.pause_count < PARAGRAPH_PAUSE:
        # should add '.  ' at the end
        check_count = {'end': False, 'res': '.  '}
      else:
        # should add ', ' at the end
        check_count = {'end': False, 'res': ', '}
      # reset pause
      self.pause_count = 0
    return check_count

  def add_punctuation(self, partial, punctuation):
    partial += punctuation
    if self.wait_to_add:
      self.last_segment += punctuation
      print(58, self.last_segment)
      self.document.pop()
      self.document.append(self.last_segment)
      self.wait_to_add = False
      self.temp_add = True
      self.last_segment = ''
    
    if self.temp_add:
      self.document.append(partial)
      self.temp_add = False
    
    # always update the document last element with partial
    self.document[-1] = partial


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
              self.last_segment = last_segment
              print('Transcript: {}'.format(self.last_segment))
              self.wait_to_add = True
          else:
            recJson = json.loads(rec.PartialResult())
            partial = recJson['partial']
            if self.model == 'zh':
              partial = partial.replace(' ', '')
            pause_check = self.count_for_pause(partial)
            if pause_check['end']:
              print('Paused long enough, end recording')
              self.document.append(self.last_segment + '.\n')
              break
            else:
              self.add_punctuation(partial, pause_check['res'])

    except KeyboardInterrupt:
      print('\nDone')
    except Exception as e:
      print(e)

    self.title = self.document[0].strip(',.\n')
    self.content = ''.join(self.document[1:])
    self.idle = True
