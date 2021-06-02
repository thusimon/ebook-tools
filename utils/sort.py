def sort_by_number_name(file_name):
  #split file name by name and extension
  file_name_no_ext = file_name.split('.')[0]
  file_name_int = 0
  try:
    file_name_int = int(file_name_no_ext)
  except ValueError:
    print('can not convert file name to integer')
  return file_name_int