#!/bin/python2
# -*- coding: utf-8 -*- 
import requests
import codecs
import md5
import os
import json
import time
import sys
import re
from subprocess import call
from clint.textui import progress
from time import gmtime, strftime
from lxml import html
import urllib
def parseVolName(str):
    return ' '.join(filter(None,re.split(u'\r|\n|\t|\xa0',str)))

def requestWA(url):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
    }
    r=requests.get(url,headers=headers)
    r.encoding='utf-8'
    return r
def DownloadImg(url,lf):
    print "getting %s"%url
    r = requests.get(url)
    f = open(lf, 'wb')
    for chunk in r.iter_content(chunk_size=512 * 1024): 
        if chunk: # filter out keep-alive new chunks
            f.write(chunk)
    f.close()
    return 
def escape(s):
    d=[[r'&',r'&amp;'],[r'>',r'&gt;'],[r'<',r'&lt;'],[u'“',u"「"],[u"”",u"」"]]
    for i in range(len(d)):
        s=re.sub(d[i][0],d[i][1],s)
    return s
def getChap(cus,cts,imgDir):
    chapters=[]
    images=[]
    firstImg=False
    for i in range(len(cus)):
        url=cus[i]

        r = requestWA(url)
        tree = html.fromstring(r.text)
        lines=tree.xpath('//div[@id="J_view"]/div|//div[@id="J_view"]/br')
        #print len(lines)
        t=""
        for c in lines:
            img=c.xpath(".//img/@data-cover")
            if(len(img)>0):
                img=img[0]
                imgname=img.split('/')[-1]
                fl=imgDir+"/"+imgname
                DownloadImg("http://lknovel.lightnovel.cn"+img,fl)

                if(firstImg==False):
                    firstImg="../"+fl
                t+="""<img src="../{0}"/>\n""".format(fl)
            elif(c.tag=='div'):
                text=c.text
                if(text!=None):
                    t+=('<p style="text-indent:2em">')
                    t+=(escape(text))
                    t+='</p>\n'
            else:
                t+='<br/>'
        chapters.append(t)
    return firstImg,chapters
def makeMobi(vol,author,name,bookname,base_dir="temp"):
    cus=vol.xpath('.//li/a/@href')
    cts=map(parseVolName,vol.xpath('.//li/a/span/text()'))

#    print cus,cts
    call(["rm","-fr","./temp"])
    call(["mkdir", "-p","./temp/img"])

    firstImg,chapters=getChap(cus,cts,"./temp/img")

    f=codecs.open("%s/main.html"%base_dir,'w',"utf-8")
    f.write(r"""<!doctype html>
<html>
    <head>
        <title>%s</title>
        <meta http-equiv="content-type" content="text/html; charset=utf-8">
    </head>
<body>
"""%(name))

    for i in range(len(cus)):
        if(i==0):
            cmd=u'<a name="chapter{0}"><h1>{1}</h1></a>'.format(i,cts[i])
            f.write(cmd)
        else:
            cmd=u'<a name="chapter{0}"><h1>{1}</h1></a>'.format(i,cts[i])
            f.write(cmd)
        g=chapters[i]
        f.write(g)
    f.write("</body></html>")
    f.close()
    uuid="book:rh:"+strftime("%Y-%m-%d %H:%M:%S", gmtime())
    opf=u"""<?xml version="1.0"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
 
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{title}</dc:title>
    <dc:language>zh-cn</dc:language>
    <dc:identifier id="BookId" opf:scheme="uuid">{uuid}</dc:identifier>
    <dc:creator opf:file-as="{author}" opf:role="aut">{author}</dc:creator>
    <dc:publisher>Roundhead</dc:publisher>
    <dc:subject>Light Novel</dc:subject>
    <dc:date>{date}</dc:date>
    <dc:description></dc:description>
    <meta name="cover" content="my-cover-image" />
  </metadata>
 
  <manifest>
    <item id="tc" href="toc.html" media-type="application/xhtml+xml"/>
    <item id="book" href="main.html" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>  
    <item id="my-cover-image" href="{cover}" media-type="image/jpeg" />
  </manifest>
 
  <!-- Each itemref references the id of a document designated in the manifest. The order of the itemref elements organizes the associated content files into the linear reading order of the publication.  -->
  <spine toc="ncx">
    <itemref idref="tc" />
    <itemref idref="book" />
  </spine>
 
  <!-- The Kindle reading system supports two special guide items which are both mandatory.
  type="toc" [mandatory]: a link to the HTML table of contents
  type="text" [mandatory]: a link to where the content of the book starts (typically after the front matter) -->
  <guide>
    <reference type="toc" title="Table of Contents" href="toc.html"/>
    <reference type="text" title="Beginning" href="toc.html"></reference>
  </guide>
 
</package>""".format(title=name,uuid=uuid,author=author,date=strftime("%Y-%m-%d", gmtime()),cover=firstImg)
    f=codecs.open("%s/mykindlebook.opf"%base_dir,'w',"utf-8")
    f.write(opf)
    f.close()
    f=codecs.open("%s/toc.html"%base_dir,'w',"utf-8")
    f.write(u"""<!doctype html>
<html>
<head>
    <title>目录</title>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    
</head>
<body>
<div id="toc">""")
    for i in range(len(cus)):
        f.write(u'<div><a href="main.html#chapter{0}">{1}</a></div>\n'.format(i,cts[i]))
    f.write(u"""</div>
</body>
</html>""")
    f.close()
    
    f=codecs.open("%s/toc.ncx"%base_dir,'w',"utf-8")
    f.write(u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
 
<ncx version="2005-1" xml:lang="zh-cn" xmlns="http://www.daisy.org/z3986/2005/ncx/">
 
  <head>
<!-- The following four metadata items are required for all NCX documents,
including those conforming to the relaxed constraints of OPS 2.0 -->
 
    <meta name="dtb:uid" content="{uuid}"/> <!-- same as in .opf -->
    <meta name="dtb:depth" content="1"/> <!-- 1 or higher -->
    <meta name="dtb:totalPageCount" content="0"/> <!-- must be 0 -->
    <meta name="dtb:maxPageNumber" content="0"/> <!-- must be 0 -->
  </head>
 
  <docTitle>
    <text>{title}</text>
  </docTitle>
 
  <docAuthor>
    <text>{author}</text>
  </docAuthor>

<navMap>
    <navPoint class="toc" id="table" playOrder="1">
        <navLabel><text>目录</text></navLabel>
        <content src="toc.html" /> 
    </navPoint>
    <navPoint class="titlepage" id="L1T" playOrder="2">
        <navLabel><text>{cname0}</text></navLabel>
        <content src="main.html#chapter0" /> 
    </navPoint>""".format(uuid=uuid,title=name,author=author,cname0=cts[0]))
    for i in range(1,len(cus)):
        f.write(u"""<navPoint class="book" id="level1-book{0}" playOrder="{2}">
        <navLabel><text>{1}</text></navLabel>
        <content src="main.html#chapter{0}" />
        """.format(i,cts[i],i+2))
    f.write("""    </navPoint>
</navMap>

</ncx>""")
    f.close()
    print "here"
    call("zip -r {0} {0}/*".format(base_dir),shell=True)
    call("mv {0}.zip {0}.epub".format(base_dir),shell=True)
    
    call("./kindlegen %s.epub"%base_dir,shell=True)
    if(bookname):
        call(["mv","%s.mobi"%base_dir,"%s/%s.mobi"%(bookname,name)])
    else:
        call(["mv","%s.mobi"%vid,"%s.mobi"%(name)])
    call("rm -fr %s"%base_dir ,shell=True)
    call("rm -fr %s.epub"%base_dir,shell=True)


    

def getBook(url,bookname=False):
    def parseVolName(str):
        return ' '.join(filter(None,re.split(u'\r|\n|\t|\xa0',str)))
    r=requestWA(url)
#    print r.text
    tree = html.fromstring(r.text)
#    print r.text
    author=tree.xpath("//table//td/a/text()")[0]
#    print author
    
    vols= tree.xpath("//dd")
#    print vols[0].xpath("div/h2/strong/a/text()")[0]
    if(bookname):
        if not os.path.exists(bookname):
            os.makedirs(bookname)
    for i in (range(len(vols))):
        name=parseVolName(vols[i].xpath("div/h2/strong/a/text()")[0])
        if bookname:
            print u"Getting \033[94m%s\033[0m - \033[96m%s\033[0m"%(bookname,name)
        else:
            print u"Getting \033[96m%s\033[0m"%name
        makeMobi(vols[i],author,name,bookname)
def listSearch(key):

    r=requestWA("http://lknovel.lightnovel.cn/main/booklist/%s.html"%urllib.quote(key))

    tree = html.fromstring(r.text)

    urls_raw=tree.xpath('//a[@class="lk-ellipsis"]/@href')
    titles_raw=tree.xpath('//a[@class="lk-ellipsis"]/@title')
    #books=tree.xpath('//div[@class="lk-block"]/p/a/text()')
    urls=[]
    titles=[]

    for i in range(len(urls_raw)):
        url=urls_raw[i]
        title=titles_raw[i]
        if(not url in urls):
            urls.append(url)
            titles.append(unicode(title))


    print "\033[92m%d\033[0m book(s) found"%len(urls)
    
    for i in range(len(urls)):
        print "\nIndex: \033[95m%d\033[0m\nName: \033[94m%s\033[0m\nURL: \033[92m%s\033[0m\n" % (i+1,titles[i],urls[i])
    choice=raw_input("Input choice (Index or A for All):")
    if(choice=='A'):
        for i in range(len(books)):
            getBook(urls[i],titles[i])
    else:
        int_numbers = re.compile('\d[\d ]*')
        def extract_integers(text):
            for value_match in int_numbers.finditer(text):
                try:
                    yield int(value_match.group().replace(' ', ''))
                except ValueError:
                    # failed to create an int, ignore
                    pass
        for i in extract_integers(choice):
            getBook(urls[i-1],titles[i-1])
if __name__=='__main__':
    if(len(sys.argv)!=3):
        print """usage: work.py [search keyword|download bookid]"""
    else:
        if(sys.argv[1]=="search"):
            listSearch(sys.argv[2])
        elif(sys.argv[1]=="download"):
            getBook(int(sys.argv[2]))
#            makePDF(668,2388,{'Name':"a"})






