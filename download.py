#!/usr/bin/env python
# encoding: utf-8

# Download all PDF files.

import os

if os.environ.get('SOCKS5_PROXY'):
  import socks
  import socket
  proxy = os.environ['SOCKS5_PROXY'].split(':')
  print "Using socks5 proxy:",proxy
  server = proxy[0]
  port = int(proxy[1])
  socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, server, port)
  socket.socket = socks.socksocket


import cPickle as pickle
import urllib
import sys, markdown, requests, bs4 as BeautifulSoup
import os,glob,re,shutil,hashlib
from pyPdf import PdfFileReader
DIR = os.path.dirname(os.path.realpath(__file__))

spchars = {
  '(':u'（',
  ')':u'）',
  '|':u'｜',
  '/':u'／',
  ':':u'：',
  '&':u'＆',
  '!':u'！',
  ',':u'，',
  '%':u'％',
  '#':u'＃'
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

def md5(s):
  return hashlib.md5(s).hexdigest()

def md5_file(filepath):
  return md5(open(filepath, 'rb').read())

OK = 1
Skipped = -1

def download(url,manifest): # -> OK | Skip | False
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
    try:
      open(tmp_file,'wb').write(res.raw.read())
    except Exception as e:
      sys.stderr.write('Error downloading URL %s: %s\n' % (url, e))
      return False
    pdf = PdfFileReader(file(tmp_file, "rb"))
    title = pdf.getDocumentInfo().title or ""
    title = encode_title(title).strip()
    if not title and title.lower()!='untitled':
      filename = encode_title(urllib.unquote(os.path.basename(url)).decode('utf-8'))
    else:
      print title
      filename = title + '.pdf'

    target_file = DIR+'/PDF/'+ filename
    i = 1
    while os.path.exists(target_file) and md5_file(target_file) != md5_file(tmp_file):
      i += 1
      target_file = DIR+'/PDF/'+ str(i) + '_' + filename

    shutil.move(tmp_file,target_file)
    manifest[url]= filename
    return OK
  else:
    return Skipped



def download_all(filename,manifest):
  vfname = os.path.relpath(filename,DIR)
  ok = True
  for url in retrieve_urls(filename):
    if manifest.get(url):
      print 'Existed: %s,%s' % (url,manifest[url])
      continue
    msg = ' [%s] in %s' % (url,vfname)
    print 'Downloading'+msg
    status = download(url,manifest)
    if status is OK:
      print 'Downloaded' + msg
    elif status is Skipped:
      print 'Skipped' + msg
      manifest[url] = 'Not PDF'
    else:
      sys.stderr.write('Failed' + msg + '\n')
      ok = False
  return ok

manifest_path = DIR + '/PDF/manifest'

def main():
  if not os.path.exists(manifest_path):
    with open(manifest_path, 'wb') as f:
      pickle.dump({},f)
  manifest = pickle.load(open(manifest_path,'rb'))
  ok = True
  files = sys.argv[1:] if len(sys.argv) > 1 else glob.glob(DIR+'/List/*.md')
  for filename in files:
    try:
      ok &= download_all(filename,manifest)
    except IOError as e:
      sys.stderr.write(str(e) + "\n")
      ok = False
    except:
      print 'Saving manifest'
      with open(manifest_path,'wb') as f:
        pickle.dump(manifest,f)

  with open(manifest_path,'wb') as f:
    pickle.dump(manifest,f)
  exit(0 if ok else 1)




if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt as e:
    print "Ctrl-C exit!"
    exit(0)
