#coding: utf-8
import hashlib
import sys
import binascii
from threading import Thread
from StringIO import StringIO

reload(sys)
sys.setdefaultencoding('utf8')

import requests
from bs4 import BeautifulSoup

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
import evernote.edam.userstore.constants as UserStoreConstants
from evernote.edam.error.ttypes import EDAMUserException
from evernote.edam.error.ttypes import EDAMSystemException
from evernote.edam.error.ttypes import EDAMNotFoundException
from evernote.edam.error.ttypes import EDAMErrorCode

class EvernoteUtil(object):

    def __init__(self, token):
        try:
            self.client = EvernoteClient(token=token)
            self.user_store = self.client.get_user_store()
            self.note_store = self.client.get_note_store()
        except EDAMUserException as e:
            print "token error %s", e

    def save_note(self, ntitle, nbody, resources=[], parent_notebook=None):
        '''
        '''
        note = Types.Note()
        note.title = ntitle
        note.content = nbody
        if parent_notebook:
            note.notebookGuid = parent_notebook.guid
        try:
            self.note_store.CreateNote(note)
        except EDAMUserException, edue:
            print "EDAMUserException:", edue
            return None
        except EDAMNotFoundException, ednfe:
            print "EDAMNotFoundException: Invalid parent notebook GUID", ednfe
            return None
        return note

    def _format_html_to_enml(self, html):
        remove_tags = [
            "applet", "base", "basefont", "bgsound", "blink", "button", "dir", "embed", "fieldset",
             "form", "frame", "frameset", "head", "iframe", "ilayer", "input", "isindex","label",
             "layer", "legend", "link", "marquee", "menu", "meta", "noframes", "noscript", "object",
             "optgroup", "option", "param", "plaintext", "script", "select", "style",
             "textarea", "xml", "aside"
             ]
        replace_with_div_tags = ["html", "body", "header", "footer", "nav", "section","article"]

        soup = BeautifulSoup(html)

        jobs = []
        resources = []
        for img_node in soup.find_all('img'):
            thread = DownLoadImage(img_node)
            jobs.append(thread)
            thread.start()
        for job in jobs:
            job.join()
            resource = job.resource
            if resource is not None:
                resources.append(resource)
        for remove_tag in remove_tags:
            for tag in soup.find_all(remove_tag):
                tag.decompose()
        for replace_tag in replace_with_div_tags:
            for tag in soup.find_all(replace_tag):
                tag.name = "div"

        note = Types.Note()
        note.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
        <en-note>%s</en-note>''' %unicode(soup)
        print type(note.content)
        note.title = "test"
        note.resources = resources
        self.note_store.createNote(note)

class DownLoadImage(Thread):

    def __init__(self, img_node):
        Thread.__init__(self)
        self.resource = None
        self.img_node = img_node

    def run(self):
        '''
        '''
        if self.img_node.has_attr('src'):
            img_url = self.img_node['src']
        elif self.img_node.has_attr('data-src'):
            img_url = self.img_node['data-src']
        else:
            return sys.exit(1)
        print img_url
        try:
            response = requests.get(img_url)
            print response.headers
            img_content = StringIO(response.content)
        except Exception, ex:
            print('ffff')
            raise ex

        md5 = hashlib.md5()
        md5.update(img_content)
        md5hash = md5.hexdigest()
        hash_hex = binascii.hexlify(md5hash)

        data = Types.Data()
        data.size = len(img_content)
        data.body = img_content
        data.bodyHash = md5hash

        self.resource = Types.Resource()
        self.resource.data = data
        self.resource.mime = response.headers['content-type']
        print self.resource.mime
        print "1"

        for attr in self.img_node.attrs.keys():
            del self.img_node[attr]
        self.img_node.name = 'en-media'
        self.img_node['type'] = response.headers['content-type']
        self.img_node['hash'] = hash_hex
        print self.img_node

if __name__ == "__main__":
    url = 'http://mp.weixin.qq.com/s?__biz=MzAwNzA3MjgyMA==&mid=201926869&idx=1&sn=86d6b225361011a9f5eac5f3a93f137c&key=7c6f9eba607ea3e8e994d0b43536eb067a678ff5febc1b1200fdcd54cd4ed4c072c70ed7bc57709163fdfd3cbbeb96fb&ascene=7&uin=NTg0MjcxNjk1&devicetype=android-17&version=26000036&pass_ticket=I7TRHdpPNTFIoi9MYtaHwQvYn5KFGT5xj%2BNue%2BmQx6NNrr7VkPNWRNav5qYpxlg%2B'
    r = requests.get(url)
    EvernoteUtil('S=s1:U=8f297:E=1519f7019a1:C=14a47beeaf0:P=1cd:A=en-devtoken:V=2:H=ff23b1b629e0f2dd313e7d25b7701cc6')._format_html_to_enml(r.text)
