from PIL import Image
import pytesseract
from os import listdir
from os.path import isfile, join
from ebooklib import epub
from utils.sort import sort_by_number_name


EPUB_LANG = {
  'eng': 'en'
}

class OCRRecognizer:
  def __init__(self) -> None:
    # set the tesseract_cmd as the tesseract installation path, or add the path to env
    pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract'


  def ocr_core(self, file_path, config=r'--psm 3', lang='eng'):
    """
    This function will handle the core OCR processing of images.
    """
    img = Image.open(file_path)
    img = img.convert('L')
    text = pytesseract.image_to_string(img, config=config, lang=lang)
    return text

  def ocr_folder(self, folder_path, sort_lambda=sort_by_number_name, config=r'--psm 3', lang='eng'):
    file_names = []
    ocr_result = []
    for file in listdir(folder_path):
      if isfile(join(folder_path, file)):
        file_names.append(file)
    
    file_names.sort(key=sort_lambda)
    for file in file_names:
      file_path = join(folder_path, file)
      file_ocr = self.ocr_core(file_path, config, lang)
      ocr_result.append(file_ocr)
      print(f'File OCR done: {file_path}')
    return ocr_result

  def generate_epub_dom(self, ocr_lines):
    ocr_lines_split = ocr_lines.splitlines()
    epub_dom_out = ''
    for line in ocr_lines_split:
        # todo escape
        epub_dom_out += f'<p>{line}</p>'
    return epub_dom_out

  def create_epub(self, folder_path, title, author, sort_lambda=sort_by_number_name, config=r'--psm 3', lang='eng'):
    epub_book = epub.EpubBook()
    epub_lang = EPUB_LANG[lang]
    # set metadata
    epub_identifier = f'{title}_{author}'
    epub_book.set_identifier(epub_identifier)
    epub_book.set_title(title)
    epub_book.set_language(epub_lang)
    epub_book.add_author(author)
    # add cover
    cover = epub.EpubHtml(title='cover', file_name='cover.xhtml', lang=epub_lang)
    cover.content = u'<div><h1>{}</h1><h3>{}</h3></div>'.format(title, author)
    epub_book.add_item(cover)
    spines = ['nav', cover] 
    ocr_results = self.ocr_folder(folder_path, sort_lambda, config, lang)
    for idx, ocr_file_lines in enumerate(ocr_results):
      epub_dom_content = self.generate_epub_dom(ocr_file_lines)
      page_idx = idx + 1
      epub_component = epub.EpubHtml(title=f'Page_{page_idx}', file_name=f'Page_{page_idx}.xhtml', lang=epub_lang)
      epub_component.content = u'<div>{}</div>'.format(epub_dom_content)
      epub_book.add_item(epub_component)
      spines.append(epub_component)

    # add default NCX and Nav file
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())
    # define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    # add CSS file
    epub_book.add_item(nav_css)
    # basic spine
    epub_book.spine = spines
    # write to the file
    epub.write_epub(f'{folder_path}/{epub_identifier}.epub', epub_book, {})
    print(f'{epub_identifier}.epub is generated')
