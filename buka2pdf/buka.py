#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, cookielib
import StringIO,pprint
cookie_jar = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
urllib2.install_opener(opener)
import json,gzip
# acquire cookie
import subprocess
import pickle
import sys
import re
import os
# do POST
pp = pprint.PrettyPrinter(indent=1)
type2rep=[u"第%s话",u"第%s卷",u"番外%s"]
type2name=[u"单话",u"单行本",u"番外篇"]
comics={}
class Episode:
    def __init__(self,d,mid,cname):
        self.cid=d["cid"]
        self.idx=d["idx"]
        self.title=d["title"]
        self.cname=cname
        self.type=d["type"]
        if(self.title==""):
            self.title=type2rep[int(self.type)]%self.idx
        self.mid=mid
    def Str(self):
        return u"{cid:%s\nidx:%s\ntitle:%s\ntype:%s\nmid:%s\ncname:%s}"%(self.cid,self.idx,self.title,self.type,self.mid,self.cname)
def talkToServer(s):
    url_2 = 'http://cs.bukamanhua.com:8000/request.php?t=1418854989733&u=63DAB80F631B8A2CFAC72D435DAC30C6SM'
    values ={'i':s,'c':"47ED5466224BE76E026103722EF32316",'z':1,'p':"android",'v':7,'cv':17301520,'chn':"home",'hd':0,'uc':"63DAB80F631B8A2CFAC72D435DAC30C6SM"}
    data = urllib.urlencode(values)
    req = urllib2.Request(url_2, data)
    rsp = urllib2.urlopen(req)
    buf = StringIO.StringIO(rsp.read())
    gzip_f = gzip.GzipFile(fileobj=buf)
    content = gzip_f.read()
    a=json.loads(content)
    return a

def search(name):
    s=r"%7B%22f%22%3A%22func_search%22%2C%22initc%22%3A%22%22%2C%22text%22%3A%22"+urllib2.quote(name)+r"%22%2C%22cate%22%3A0%2C%22count%22%3A20%2C%22order%22%3A0%2C%22start%22%3A0%2C%22recom%22%3A1%2C%22mask%22%3A7%7D"
    return talkToServer(s)
    
def getInfo(mid):
    s=r"%7B%22f%22%3A%22func_getdetail%22%2C%22mid%22%3A"+mid+"%7D"
    a=talkToServer(s)
    cs=[]
    for i in a["links"]:
        cs.append(Episode(i,mid,a['name']))
    return a,cs
    
def getOnlineInfo(mid,cid):
    url="http://index.bukamanhua.com:8000/req3.php?mid="+mid+"&cid="+cid+"&c=8ab2e7959f2a529581529d91e5abe686&s=ao&v=5&t=-1&restype=4"
    rsp = urllib2.urlopen(url)
    print rsp.read()
def getUrl(mid,cid):
    s=r"%7B%22f%22%3A%22func_getdownurl3%22%2C%22ver%22%3A3%2C%22mid%22%3A"+mid+r"%2C%22cid%22%3A"+cid+r"%2C%22restype%22%3A2%7D"
    a=talkToServer(s)
    return a['down'][0]['url']
def download(url,filename=''):
    if(filename==''):
        filename = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(filename, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (filename, file_size)
    
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()
    return filename
def getEpisode(ep):
    url=getUrl(ep.mid,ep.cid)
    fn=download(url)
    pdfname=u"%s - %s.pdf"%(ep.cname,ep.title)
    retcode = subprocess.call(["./dat2pdf.sh",fn,u"%s-%s"%(ep.cname,ep.cid), pdfname])


def addMid(mid):
    a,cs=getInfo(mid)
    print
    print "Adding \033[94m%s\033[0m by \033[93m%s\033[0m"%(a['name'] ,a['author'])

    cids=[[i.cid for i in cs if i.type=='0'],
          [i.cid for i in cs if i.type=='1'],
          [i.cid for i in cs if i.type=='2']]
    dd=[]
    for i in range(3):
        if(len(cids[i])>0):
            print "\033[92m%d\033[0m items found with type \033[92m%s\033[0m"%(len(cids[i]),type2name[i])
            choice=raw_input("How many of them do you wish to fetch in next refresh (-1 for All, default 0):")
            try:
                choice=int(choice)
            except ValueError:
                choice=0
            if(choice<0 or choice>=len(cids[i])):
                choice=len(cids[i])
            
            dd+=cids[i][choice:]
    comics[mid]=dd
    
def searchAdd(key):
    info=search(key)
    items=info["items"]
    print "\033[92m%d\033[0m book(s) found"%len(items)
    for i in range(len(items)):
		print "\nIndex: \033[95m%d\033[0m\nName: \033[94m%s\033[0m\nmid: \033[92m%s\033[0m\nAuthor: \033[93m%s\033[0m\n" % (i+1,items[i][u'name'],items[i][u'mid'],items[i][u'author'])
    choice=raw_input("Input choice (Index or A for All):")
    int_numbers = re.compile('\d[\d ]*')
    def extract_integers(text):
        for value_match in int_numbers.finditer(text):
            try:
                yield int(value_match.group().replace(' ', ''))
            except ValueError:
                # failed to create an int, ignore
                pass
    for i in extract_integers(choice):
        addMid(items[i-1]['mid'])

def refresh():
    for mid in comics.keys():
        dd=comics[mid]
        a,cs=getInfo(mid)
        cids=[i.cid for i in cs]
        for i in range(len(cids)):
            cid=cids[i]
            if cid in dd:
                pass
            else:
                print "New episode! ",cs[i].cname,cs[i].title
                getEpisode(cs[i])
                comics[mid].append(cid)
                with open("save.p",'wb') as output:
                    pickle.dump(comics,output)
if __name__=='__main__':
    if os.path.isfile('save.p'):
        with open("save.p",'rb') as input:
            comics=pickle.load(input)
    if(len(sys.argv)!=3 and len(sys.argv)!=2):
        print """usage: buka.py [search keyword|refresh]"""
    else:
        if(sys.argv[1]=="search"):
            searchAdd(sys.argv[2])
        elif(sys.argv[1]=="refresh"):
            refresh()


    with open("save.p",'wb') as output:
        pickle.dump(comics,output)

