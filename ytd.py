import os
import re
import subprocess
from selenium import webdriver
import time


class YtdAdder:

    def __init__(self, url=None, path=None):
        self.IDMan = self.find_idm()
        self.base_url, self.base_path = self.input_user(url, path)
        self.__unquote = re.compile('''(^")|(^')|("$)|('$)''')
        pass

    def find_idm(self):
        idm = r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"
        if not os.path.isfile(idm):
            idm = r"C:\Program Files\Internet Download Manager\IDMan.exe"
        while True:
            if not os.path.isfile(idm):
                idm = raw_input("Plz Enter Internet Download Manager (IDMan.exe) file location : ")
                idm = self.__unquote.sub("", idm)
            else:
                break
        return idm

    def input_user(self, url, path):
        if url is None:
            url = raw_input("Plz Enter Playlist URL : ")
            url = self.__unquote.sub("", url)
        if path is None:
            path = raw_input("Plz Enter Base Path : ")
            path = self.__unquote.sub("", path)
        if not os.path.isdir(path):
            os.mkdir(path)
        return url, path

    @staticmethod
    def read_execute(command):
        execute = subprocess.Popen(command, stdout=subprocess.PIPE)
        return execute.stdout.read()

    def get_vdo_list(self):
        playlist_url = self.base_url
        solid_path = self.base_path + "\\" + "link.url"
        link_code = '''[{000214A0-0000-0000-C000-000000000046}]\nProp3=19,11\n[InternetShortcut]\nURL=''' + \
                    playlist_url + '''\nIDList='''
        with open(solid_path, "w") as lp:
            lp.write(link_code)

        command = """youtube-dl --get-filename --restrict-filenames -g {}""".format(playlist_url)
        raw_vco_list = self.read_execute(command)
        vdo_list = raw_vco_list.split("\n")
        result = []
        for counter in range(1, len(vdo_list), 2):
            link, title = vdo_list[counter - 1], vdo_list[counter]
            result.append((link, title))
        return result

    def add_to_idm_que(self, vdo):
        url, file_name = vdo
        command = '''"{0}" /d "{1}" /f "{2}" /q /a /n /p "{3}"'''.format(self.IDMan, url, file_name, self.base_path)
        if not os.path.exists(self.base_path + "\\" + file_name):
            subprocess.call(command, shell=True)
            return True
        else:
            return False

    def create_playlist(self, vdo_list):
        solid_path = self.base_path + "\\" + "Playlist.m3u"
        with open(solid_path, "w") as playlist:
            playlist.write("#EXTM3U\n")
            for vdo in vdo_list:
                vdo_file_name = vdo[1]
                playlist.write(str(vdo_file_name) + "\n")
        pass


class Collector:

    def __init__(self, url=None):
        self.__unquote = re.compile('''(^")|(^')|("$)|('$)''')
        self.base_url = self.input(url)
        self.driver = webdriver.Chrome()
        pass

    def input(self, url):
        if url is None:
            url = raw_input("Plz provide url : ")
        url = self.__unquote.sub("", url)
        return url

    def collect(self):
        url = self.base_url
        counter = 1
        if url is None:
            url = raw_input("Plz provide URL : ")
        url = self.__unquote.sub("", url)
        db = self.driver
        db.get(url)
        result = []
        vdo_list = db.find_elements_by_xpath("""//div[@id='content']/div//div//div[contains(@class,'clearfix')]//ul//ul//div[contains(@class,'clearfix')]//div//h3/a""")
        for vdo in vdo_list:
            vdo_title = vdo.text
            vdo_title = str(counter).zfill(3) + " " + vdo_title.encode("ascii", errors="ignore")
            vdo_title = re.sub("""[\\\/\:\*\?\"\<\>\|]""", "_", vdo_title)
            vdo_title = re.sub("""\s+""", " ", vdo_title)
            result.append((vdo_title, vdo.get_property("href")))
            counter = counter + 1
        return result

    def playlist_n_vdo(self, url):
        db = self.driver
        db.get(url)
        vdo_number = db.find_element_by_xpath("""//*[@id="pl-header"]/div[2]/ul/li[2]""").text
        return int(re.sub("""[\D]""", "", vdo_number))

    def close(self):
        self.driver.close()
        self.driver.quit()


class Fallback:

    def __init__(self, base_path):
        self.log_file_path = base_path + "\\" + "success.log"
        pass

    def fallen(self, link):
        ptt_link = re.compile("""\<link\>(?P<link>.+)\<\/link\>""")
        log_file_path = self.log_file_path
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as log:
                all_log = log.read().split("\n")
                for item in range(len(all_log) - 1):
                    found_link = ptt_link.search(all_log[item]).group("link")
                    if found_link == link:
                        return True
                return False
        else:
            return False

    def log(self, url, title):
        log_file_path = self.log_file_path
        with open(log_file_path, "a") as log:
            log.write("""<link>{link}</link>  <title>{title}</title>\n""".format(link=url, title=title))

if __name__ == '__main__':
    tt = time.time()
    # base_path = r"C:\Users\Robotboy\Desktop\Youtube2"
    # base_url = "https://www.youtube.com/user/OnnorokomPathshala/playlists?flow=grid&view=50&shelf_id=4"

    added, failed = 0, 0
    base_path = raw_input("Plz enter base path : ")
    base_url = raw_input("Plz enter base URL : ")
    base_path = re.sub('''(^")|(^')|("$)|('$)''', "", base_path)
    base_url = re.sub('''(^")|(^')|("$)|('$)''', "", base_url)

    fall_back = Fallback(base_path)
    collector = Collector(base_url)

    cc = collector.collect()
    for item in cc:
        title, link = item
        if fall_back.fallen(link):
            pass
        else:
            path = base_path + "\\" + title
            ytd = YtdAdder(link, path)
            vdo_list = ytd.get_vdo_list()
            if collector.playlist_n_vdo(link) == len(vdo_list):
                for vdo in vdo_list:
                    vdo_added = ytd.add_to_idm_que(vdo)
                    if vdo_added:
                        added = added + 1
                        print "Adding {number} : {title}".format(number=str(added).zfill(4), title=vdo[1])
                    else:
                        print "Video already downloaded : {title}".format(title=vdo[1])
                ytd.create_playlist(vdo_list)
                fall_back.log(link, title)
            else:
                failed = failed + 1
                print "{fail} Failed to collect all link ".format(fail=str(failed).zfill(3))
    if added:
        print "Total added : {} video".format(added)
    if failed:
        print "Total failed : {} list".format(failed)
    collector.close()
    print time.time() - tt
