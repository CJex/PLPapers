#!/usr/bin/env python
# encoding: utf-8

# Download all PDF files.

import sys, markdown, requests, bs4 as BeautifulSoup
import os,glob,re,shutil,hashlib
from pyPdf import PdfFileReader
DIR = os.path.dirname(os.path.realpath(__file__))

spchars = {
  '(':'（',
  ')':'）',
  '|':'｜',
  '/':'／',
  ':':'：',
  '&':'＆',
  '!':'！',
  ',':'，',
  '%':'％',
  '#':'＃'
}



def encode_title(title):
  title = title.decode('utf-8')
  return re.sub(r'[^a-zA-Z0-9 _-]',lambda m: ' ' if m.group(0) not in spchars else spchars[m.group(0)],title)


def retrieve_urls(filename): # -> [LinkURL]
  with open(filename) as fd:
    mdtext = unicode(fd.read().decode('utf-8'))
    html_text = markdown.markdown(mdtext)
    soup = BeautifulSoup.BeautifulSoup(html_text)
    return [a['href'] for a in soup.findAll('a')]

def md5sum(filepath):
  return hashlib.md5(open(filepath, 'rb').read()).hexdigest()

OK = 1
Skipped = -1

def download(url): # -> OK | Skip | False
  try:
    res = requests.head(url, allow_redirects=True)
    if not bool(res):
      return False
  except Exception as e:
    sys.stderr.write('Error checking URL %s: %s\n' % (url, e))
    return False

  ct = res.headers['content-type']
  if ct.endswith('/pdf') or ct.endswith('/x-pdf'):
    res = requests.get(url,allow_redirects=True,stream=True)
    tmp_file = DIR + '/PDF/temp.downloading.pdf'
    open(tmp_file,'wb').write(res.raw.read())
    pdf = PdfFileReader(file(tmp_file, "rb"))
    title = pdf.getDocumentInfo().title
    if not title:
      filename = os.path.basename(url)
    else:
      print title
      filename = encode_title(title) + '.pdf'

    target_file = DIR+'/PDF/'+ filename
    i = 1
    while os.path.exists(target_file) and md5sum(target_file) != md5sum(tmp_file):
      target_file = DIR+'/PDF/'+tr(i) + '_' + filename
      i += 1

    shutil.move(tmp_file,target_file)
    return OK
  else:
    return Skipped



def download_all(filename):
  vfname = os.path.relpath(filename,DIR)
  ok = True
  for url in retrieve_urls(filename):
    msg = ' [%s] in %s' % (url,vfname)
    status = download(url)
    if status is OK:
      print 'Downloaded' + msg
    elif status is Skipped:
      print 'Skipped' + msg
    else:
      sys.stderr.write('Failed' + msg + '\n')
      ok = False
  return ok

def main():
  ok = True
  files = sys.argv[1:] if len(sys.argv) > 1 else glob.glob(DIR+'/List/*.md')
  for filename in files:
    try:
      ok &= download_all(filename)
    except IOError as e:
      sys.stderr.write(str(e) + "\n")
      ok = False
  exit (0 if ok else 1)

if __name__ == '__main__':
  main()
