#!/usr/bin/env python
#coding=utf-8
"""
html网页克隆工具
使用方式：dlhtml.py url
例如：dlhtml.py http://www.abcd.com/html/index.html
注意：请求的文件名中不要带有 "/" 这种特殊字符。
"""

import sys,os,re,json,requests
from bs4 import BeautifulSoup

#########################################
print "\n作者：黄龙飞  QQ:282486518  email:phphome@qq.com ".decode('utf-8')
print "软件版本v1.0正式版，使用过程中如遇到bug请联系作者！".decode('utf-8')
print "本软件免费使用，可自由传播。 ".decode('utf-8')
print "使用本软件所带来的侵权或其他损失由使用者自行承担，软件作者不负任何责任！ \n\n".decode('utf-8')
#########################################

# 程序配置
#config = {
#    "header":{"User-Agent":"Mozilla-Firefox5.0"},
#    "webroot":"download_www",
#    
#}
try:
    data = open("config.json","r").read()
except:
    print "config.json 配置文件读取异常！".decode('utf-8')
    exit()
config = json.loads(data)  #字典类型

"""
整站下载类
全局属性包括以下一些：
self.s      requests 对象 
self.url    要下载的url http://www.abcd.com/html/index.html
self.list   存储要下载的文件的url，包括网页中的images、css、js 
self.header 保存http请求头参数
self.domain    要下载网站的域名 www.abcd.com
self.dirname   文件存储目录 www.abcd.com/html
self.basename  文件名 index.html
self.base = None  html文档中是否含有base标签,如果含有base标签，那么html中所有的相对链接都要发生变化
self.beiyong = None  备用全局字符串，*****特别注意，用完后请一定要还原None*****
"""
class dlhtml():
    def __init__(self,url):
        # 登录
        if config["is_login"] :
            self.s = self.login(config["login_url"],config["login_data"],config["header"])
            print "登录成功！".decode('utf-8')
        else:
            self.s = requests.Session()
            print "未登录！".decode('utf-8')
        
        self.url = url
        self.list = {"images":[],"css":[],"js":[]} #存储下载的字典
        #print config["header"]["User-Agent"]
        self.header = config["header"]
        self.base = None #html文档中是否含有base标签
        self.beiyong = None  # 备用字符串
        
        if not os.path.isdir(config["webroot"]):
            os.mkdir(config["webroot"])
        
        # 规范url结构
        if url.find("http://") == 0 :
            url = url[7:]
            if url.find("/",-1) != -1 :
                url = url + "index.html"
        else :
            print "url格式错误!正确格式为：".decode('utf-8')
            print " http://www.abcd.com/".decode('utf-8')
            print " http://www.abcd.com/cdef/abc.html".decode('utf-8')
            exit()
        print url
        
        dirname,basename = os.path.split(url)
        
        if not os.path.exists(config["webroot"]+"/"+dirname):
            os.makedirs(config["webroot"]+"/"+dirname)
            
        self.domain = dirname.split("/",1)[0]
        self.dirname = dirname
        self.basename = self.format_filename( basename )
        
        #print self.domain  #域名
        #print self.dirname  #域名+目录
        #print self.basename  #文件名
    
    def login ( self , login_url , login_data , headers  ) :
        s = requests.Session()
        s.post( login_url , data = login_data , headers = headers )
        return s
    
    # 下载并分析html文件
    # 分析html中images元素，并将images的绝对地址存入{“images”:[,,]}中，而且将html中的images换成相对地址。
    # 分析html中css文件，并将css文件的绝对地址存入{“css”:[,,]}中，而且将html中的css文件相对地址。
    # 分析html中js文件，并将css文件的绝对地址存入{“js”:[,,]}中，而且将html中的js文件相对地址。
    def fenxi_html(self):
        html = self.s.get(self.url,headers=self.header).content
        open("w.log","w").write(html)
        # 正则 处理html中 行内样式、<style>标签、background属性 中的图片
        html = self._parse_style_img(html)
        
        soup = BeautifulSoup(html)
        # 如果html中含有 <base href="http://www.abcde.net/"/> 标签，需要将相对链接处理掉
        #exit()
        self.base = soup.find("base")
        if self.base :
            self.base.extract()  # 移除 base 标签
        
        # 处理html中的图片
        images = soup.findAll("img",src=True)
        self.append_list("images",images,"src")
        # 处理html中的css
        css = soup.findAll("link",{"rel":["stylesheet","Stylesheet"]},href=True)
        self.append_list("css",css,"href")
        # 处理html中的js
        js = soup.findAll("script",src=True)
        self.append_list("js",js,"src")
        # 保存html
        file = open(config["webroot"]+"/"+self.dirname+"/"+self.format_filename(self.basename),"w")
        file.write(str(soup))
        file.close()
        
        #print self.list["js"]
        #print soup.findAll("link",{"rel":"stylesheet"},href=True)
        #print soup.findAll("script",src=True)
    
    # 下载js文件，并分析js中的imsges图片，并返回imsges的绝对地址{“images”:[,,]}
    def download_js(self):
        # 处理js文件中的图片
        
        self.download("js")
        
        pass
    
    # 下载css文件，并分析css中的background图片，并返回background的绝对地址{“images”:[,,]}
    def download_css(self):
        
        self.download("css")
        pass

    # 下载images
    def download_images(self):
        
        # 图片去重
        self.list["images"] = list(set(self.list["images"]))
        self.download("images")
        
        pass
    

    """
        格式化文件名，防止文件名中含有特殊符号而出现错误
        filename : 文件名
    """
    def format_filename(self,filename):
        teshu = ["/","\\","?","*",":","\"","<",">"]
        for i in teshu:
            filename = filename.replace(i,"_")
        return filename
    
    # 将元素加入到下载列表中
    """
        filetype : 文件类型 images,css,js
        tag_list : 文件列表
        attr     : 要处理的文件属性
    """
    def append_list(self,filetype,tag_list,attr):
        for tag in tag_list:
            #print tag[attr]
            
            # 截掉images,css,js文件url中"?"和之后的内容
            tag[attr] = self.del_url_wenhao(tag[attr])
            
            if tag[attr].find("http://") == 0 :
                #不需要修改images中该元素路径
                self.list[filetype].append(tag[attr])
                #但需要修改html中该元素的路径为相对路径
                src = tag[attr][7:]
                presrc = ""
                for i in self.dirname.split("/"):
                    presrc += "../"
                src = presrc + src
                tag[attr] = src
                pass
            elif tag[attr].find("//") == 0 :
                #需要修改images中该元素路径为http的方式
                self.list[filetype].append( "http:" + tag[attr] )
                #需要修改html中该元素的路径为相对路径
                src = tag[attr][2:]
                presrc = ""
                for i in self.dirname.split("/"):
                    presrc += "../"
                src = presrc + src
                tag[attr] = src
                pass
            elif tag[attr].find("/") == 0 :
                #需要修改images中该元素路径为http的方式
                self.list[filetype].append( "http://" + self.domain + tag[attr] )
                #需要修改html中该元素的路径为相对路径
                src = tag[attr][1:]
                presrc = ""
                for i in self.dirname.split("/"):
                    presrc += "../"
                src = presrc + self.domain + "/" + src
                tag[attr] = src
            else :
                if self.base :
                    if self.base["href"].find("/",-1) == -1 :
                        self.base["href"] = self.base["href"] + "/"
                    #需要修改images中该元素路径为http的方式
                    self.list[filetype].append( self.base["href"] + tag[attr])
                    #不需要修改html中该元素的路径
                    presrc = ""
                    for i in self.dirname.split("/"):
                        presrc += "../"
                    tag[attr] = presrc + self.base["href"][7:] + tag[attr]
                else :
                    #需要修改images中该元素路径为http的方式
                    self.list[filetype].append( "http://" + self.dirname + "/" + tag[attr])
    
    
    """
        批量下载self.list中的文件
        filetype : 文件类型 images,css,js
    """
    def download(self,filetype):
        for imgurl in self.list[filetype] :
            try:
                imgcontent = self.s.get(imgurl,headers=self.header).content
            except:
                print sys.exc_info()
                print imgurl + " open http error!!!!"
                continue
            # 对文件的内容进行处理
            if filetype == "css" :
                self.beiyong = imgurl  # 使用全局备用字符串
                imgcontent = self._parse_style_img(imgcontent)
                self.beiyong = None    # 还原全局备用字符串
            elif filetype == "js" :
                pass
            else :
                pass
            
            # 下载文件
            imgurl = imgurl[7:]
            dirname,basename = os.path.split(imgurl)
            try:
                if not os.path.exists(config["webroot"]+"/"+dirname):
                    os.makedirs(config["webroot"]+"/"+dirname)
                file = open(config["webroot"]+"/"+dirname+"/"+self.format_filename(basename),"wb") # 注意这里要格式化文件名，防止出错。
                file.write(imgcontent)
                file.close()
                print imgurl + " download success !"
            except:
                print "========================="
                print config["webroot"]+"/"+dirname+"/"+self.format_filename(basename) + " download error !"
                print "========================="
    
    """
        处理html中 行内样式、<style>标签、background属性 中的图片
        html : html文档源文件
    """
    def _parse_style_img(self,html):
        re_mod = re.compile('url\([\'"]?(.+?)[\'"]?\)')
        html = re_mod.sub(self._re_func,html)
        return html
    def _re_func(self,re_obg):
        url = re_obg.group(1).strip()
        abs,rel = self._rel_to_abs(url)
        if abs :
            self.list["images"].append( abs )
        return "url("+rel+")"
    """
        给定一个url，将url转化成 绝对地址和相对地址
        返回 file = ["http://www.abcd.com/abc/123.jpg","abc/123.jpg"]
        url     : 要处理的url
        httpurl : 要处理文件所在的绝对地址
    """
    def _rel_to_abs(self,url,httpurl=None):
        if self.beiyong != None :
            domain  = self.beiyong.split("/")[2]
            dirname = os.path.dirname(self.beiyong)[7:]
        else :
            domain  = self.domain
            dirname = self.dirname
        # 截掉images,css,js文件url中"?"和之后的内容
        file = ["",""]
        url = self.del_url_wenhao(url)
            
        # 处理 http://www.abcd.com/abc/123.jpg
        if url.find("http://") == 0 :
            file[0] = url
            
            file[1] = ""
            for i in dirname.split("/"):
                file[1] += "../"
            file[1] = file[1] + url[7:]
        
        # 处理 /bacd/123.jpg
        elif url.find("/") == 0 :
            file[0] = "http://" + domain + url
            
            file[1] = ""
            for i in dirname.split("/"):
                file[1] += "../"
            file[1] = file[1] + domain + url
        
        # 处理 ../bacd/123.jpg
        else :
            file[0] = "http://" + dirname + "/" + url
            file[1] = url
        
        return file
    # 删除url中？后的内容
    def del_url_wenhao(self,url):
        is_wenhao = url.find("?")
        if is_wenhao != -1 :
            url = url[:is_wenhao]
        return url
    

def main():
    argc = len( sys.argv )
    if argc != 2:
        print "请正确输入参数，例如：downloadhtml.exe http://www.baidu.com/".decode('utf-8')
        sys.exit( 1 )
    cmd = "http://brand.cps.com.cn/index.php?m=Member&c=Company&a=info"
    html = dlhtml(cmd)
    html.fenxi_html()
    html.download_css()
    html.download_js()
    html.download_images()


if __name__ == '__main__':
    main()