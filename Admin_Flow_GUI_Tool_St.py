import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import urllib
import cStringIO
from urllib import urlopen
import time
import random
import uuid
import nap
import json
import requests
import threading
import os

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

tdata = {}
tool_id = ""
bay_id = ""
statusinfo = ""
base_url = "http://152.135.122.61:8871/"  # Applied Url
# base_url = "http://192.168.6.149:8871/" #local Url
# base_url = "http://14.141.47.12:8871/" #ASM Url
tool_st = ""
admin = ""
owner = ""
user = ""
uid = ""
prid = ""
line = ""
selected_text = ''
timer = ''
timer = QtCore.QTimer()


def fontname():  # Fonts for the text in the pushbutton
    font = QtGui.QFont()
    font.setFamily(_fromUtf8("Times New Roman"))
    font.setPointSize(12)
    font.setBold(True)
    font.setWeight(75)
    return font


def authenitcate():  # Login authentication for the server communication
    token_url = base_url + "api-token-auth/"
    login_data = {"email": "bay@amat.com",
                  "password": "bay123"}  # Applied Login
    # login_data = {"email":"bay@gmail.com","password":"1234"} #ASM Login
    # login_data = {"email":"aravind@gmail.com","password":"1234"} #Local Login
    token_headers = {"content-type": "application/json"}
    token_response = requests.post(
        token_url, data=json.dumps(login_data), headers=token_headers)
    print "tk:", token_response
    token = json.loads(token_response.content)['token']
    authorization_header = "JWT " + token
    headers = {"content-type": "application/json",
               "Authorization": authorization_header}
    return headers


# This class contains the welcome screen and also reads rfid data and
# provides the login
class Entry_view(QtGui.QMainWindow):
    rfidscreen = pyqtSignal()

    def __init__(self, parent=None):
        super(Entry_view, self).__init__()
        self.start()

    def start(self, parent=None):
        self.line = ''
        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(-1, -1, 800, 480)
        font = fontname()
        t1 = QtGui.QPushButton(
            "\n\n\n\n\n\n\n\n Welcome to Applied Materials \n Please Swipe The Card", self)
        t1.setStyleSheet('QPushButton {color: #00BFFF}')
        t1.setFont(font)
        t1.setObjectName(_fromUtf8("t1"))
        # t1.clicked.connect(self.rfid_auth)
        # t1.clicked.connect(self.tool_click)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(
            QtGui.QPixmap("/home/pi/RPi_Lab/AMAT-Logo"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off)
        t1.setIcon(icon1)
        t1.setIconSize(QtCore.QSize(300, 300))
        t1.setObjectName(_fromUtf8("t1"))
        # logging.info('Started')
        self.thread = threading.Thread(target=self.rfidst)
        self.thread.start()
        self.rfidscreen.connect(self.display1)
        self.test = None
        # logging.info('Finished')
        t1.resize(800, 480)
        t1.move(0, 0)
        self.show()

    def rfid_auth(self):    # RFID login and authentication for the particular rfid
        global bay_id
        global admin
        global user
        global owner
        global uid

        headers = authenitcate()
        print "i'm here"
        url = base_url + "/api/bay/"
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(
            0, 8 * 6, 8)][::-1])  # Getting MAC-ID of the windows systems
        a = 'true'  # status update [Online/Offline]
        mac_data = {"mac_id": str(mac), "is_active": str(a)}
        response = requests.post(
            url, data=json.dumps(mac_data), headers=headers)
        data = json.loads(response.content)
        bay_id = data['id']
        print "bay_id:", bay_id

        uurl = base_url + "/api/user/user_info/"
        # list = [34628346382746387]
        # r = (random.choice(list))  #From given choice
        rfid = self.line  # (random.choice(list))
        print "rfid:", rfid
        # print "RFID = ", rfid
        rfid_data = {"RFID": str(rfid)}
        # print rfid_data
        response = requests.get(
            uurl, data=json.dumps(rfid_data), headers=headers)
        udata = json.loads(response.content)
        # print "udata:",udata
        count = 0
        for rdata in udata:
          #  print "rdata:",rdata
            if str(rfid) == str(rdata['rfid']):
                count += 1
                xdata = rdata
                break

        if count > 0:
            if rdata['is_active'] == True:
		admin = rdata['is_admin']
                print admin
                owner = rdata['is_owner']
                print owner
                uid = rdata['id']
                print "uid :", uid
	    else:
                self.showdialog()
                print "no access"

        else:
            self.showdialog()
            print "no access"

        self.close()
        self.test = first_view()
        self.test.show()

    def rfidst(self):   # It's a thread function to call the rfid data from the pipe

        pipein = open("/home/pi/RPi_Lab/rfidtest", 'r')
        self.line = pipein.readline()[:-1]
        print self.line
        pipein.close()
        self.rfidscreen.emit()

    def display1(self):
        self.thread.join()
        self.rfid_auth()

    def showdialog(self):  # Function is to display not authorized entry pop-up
        choice = QtGui.QMessageBox.information(
            self, 'Action', "Not Authorized")
        self.line = ''
        self.quit1()

    def quit1(self):
        self.close()
        test_quit = Entry_view(self)
        self.test_quit.show()


# In this class all the pushbutton containing tool data is displayed
class first_view(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(first_view, self).__init__()
        self.start1()

    def start1(self, parent=None):
        global tdata
        global tool_id
        global bay_id
        global statusinfo
        global uid
        global prid
        global admin
        global owner
        global timer
        global selected_text

        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(-1, -1, 800, 480)

        button_num_six = [[0, 0, 266, 240], [266, 0, 266, 240], [532, 0, 266, 240], [0, 240, 266, 240], [
            266, 240, 266, 240], [532, 240, 266, 240]]  # dynamic display of number of  buttons
        button_num_five = [[0, 0, 266, 240], [266, 0, 266, 240], [
            532, 0, 266, 240], [0, 240, 400, 240], [400, 240, 400, 240]]
        button_num_four = [[0, 0, 400, 255], [400, 0, 400, 255], [
            0, 230, 400, 255], [400, 230, 400, 255]]
        button_num_three = [[0, 0, 266, 480], [
            266, 0, 266, 480], [532, 0, 266, 480]]
        button_num_two = [[0, 0, 415, 480], [400, 0, 415, 480]]
        button_num_one = [[0, 0, 800, 480]]
        button_num_zero = [[]]

        headers = authenitcate()
        # http://122.166.6.252:8871/api/tools/"+"/users/"
        url = base_url + "api/bay/"
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(
            0, 8 * 6, 8)][::-1])  # Getting MAC-ID of the windows systems
        a = 'true'  # status update [Online/Offline]
        # Gets the MAC-ID and online status.
        mac_data = {"mac_id": str(mac), "is_active": str(a)}
        response = requests.post(
            url, data=json.dumps(mac_data), headers=headers)
        # print response
        data = json.loads(response.content)
        bay_id = data['id']

        print "bay id = ", bay_id
        # print response

        if admin == True and owner == True:  # Condition to check the admin/owner
            turl = base_url + "api/bay/" + str(bay_id) + "/tools/"
            tresponse = requests.get(turl, headers=headers)
            print "tool response :", tresponse
            tdata = json.loads(tresponse.content)
            # print tdata
            tlen_id = len(tdata)

        elif admin == True and owner == False:  # Condition to check the admin
            turl = base_url + "api/bay/" + str(bay_id) + "/tools/"
            tresponse = requests.get(turl, headers=headers)
            print "tool response :", tresponse
            tdata = json.loads(tresponse.content)
            # print tdata
            tlen_id = len(tdata)

        elif admin == False and owner == False:  # Condition to check the user
            headers = authenitcate()
            print "User ID", str(uid)
            uurl = base_url + "api/user/user_info/" + \
                str(uid) + "/tools?bay_id=" + str(bay_id)
            uresponse = requests.get(uurl, headers=headers)
            print "User Tool Info:", uresponse
            tdata = json.loads(uresponse.content)
            tlen_id = len(tdata)

        elif admin == False and owner == True:  # Condition to check the owner
            headers = authenitcate()
            print "User ID", str(uid)
            uurl = base_url + "api/user/user_info/" + \
                str(uid) + "/tools?bay_id=" + str(bay_id)
            uresponse = requests.get(uurl, headers=headers)
            print "User Tool Info:", uresponse
            tdata = json.loads(uresponse.content)
        # print "User Data :", udata

            tlen_id = len(tdata)

        self.tooldata = tdata

        if tlen_id == 6:
            button_num = button_num_six
        elif tlen_id == 5:
            button_num = button_num_five
        elif tlen_id == 4:
            button_num = button_num_four
        elif tlen_id == 3:
            button_num = button_num_three
        elif tlen_id == 2:
            button_num = button_num_two
        elif tlen_id == 1:
            button_num = button_num_one
        elif tlen_id == 0:
            self.close()
            test3 = NoButton(self)
        else:  # elif tlen_id == 0 and tlen_id == '' and tlen_id = " "
            button_num = button_num_zero

        print len(button_num)

        for data in tdata:
            print data
        b = []
        icons = []

        for i in range(0, len(button_num)):  # Number of pushbutton is displayed
            # b.append(QtGui.QPushButton(
            #     tdata[i]['name'] + "\n" + tdata[i]['status_value'] + "\n" + tdata[i]['current_project']['name'] + "\n", self))

            # prid = tdata[i]['current_project']['id']
            if tdata[i]['current_project'] == None:
                pname = "No Project"  
            else:
                pname = tdata[i]['current_project']['first_name']

            b.append(QtGui.QToolButton(self))
            b[i].setText(str(tdata[i]['name'] )+ "\n" + str(tdata[i]['status_value'] )+ "\n"+str(pname) + "\n")
            b[i].setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

            if(os.path.exists("/home/pi/RPi_Lab//" + tdata[i]['name'] + ".png")):
                print "Image Already Exists"
            else:
                # Extracts tool image from the url
                urllib.urlretrieve(tdata[i]['image_url'], tdata[
                                   i]['name'] + ".png")
            icons.append(QtGui.QIcon())

        for i in range(0, len(button_num)):  # Displays tool status and status color
            if tdata[i]['status_value'] == "Productive":
                b[i].setStyleSheet("background-color: #90EE90")  # Green
            elif tdata[i]['status_value'] == "Maintenance":
                b[i].setStyleSheet("background-color: #00BFFF")  # Blue
            elif tdata[i]['status_value'] == "Installation/Config":
                b[i].setStyleSheet("background-color: #FFFF00")  # Yellow
            else:
                b[i].setStyleSheet("background-color: #8B0000")  # Dark Red

            b[i].setObjectName(_fromUtf8(str(tdata[i]['id'])))
            b[i].resize(button_num[i][2], button_num[i][3])
            b[i].move(button_num[i][0], button_num[i][1])
            # print "tname",tdata[i]['name']
            icons[i].addPixmap(QtGui.QPixmap("/home/pi/RPi_Lab/" + tdata[i]['name'] + ".png"),
                               QtGui.QIcon.Normal,
                               QtGui.QIcon.Off)  # Display tool image
            b[i].setIcon(icons[i])
            # icons[i].setGridSize(QtCore.QSize(100,100))
            b[i].setIconSize(QtCore.QSize(113, 113))
            b[i].clicked.connect(self.tool_click)

        timer.timeout.connect(self.tool_sleep)
        timer.setSingleShot(True)
        timer.start(30000)

        self.show()

    def tool_click(self):
        global tool_id
        global tool_st
        global admin
        global user
        global owner
        global timer

        sender_button = self.sender()
        tool_id = str(sender_button.objectName())
        print tool_id
        # print self.tooldata
        for tools in self.tooldata:
            # print tools
            if str(tool_id) == str(tools['id']):
                tool_st = tools['status']
        self.close()
        timer.stop()
        test1 = second_view(self)

    def tool_sleep(self):
        self.close()
        test = Entry_view(self)
        self.test.show()


class second_view(QtGui.QMainWindow):   # This screen displays tool status button

    def __init__(self, parent=None):
        global tool_id
        global bay_id
        global tool_st
        global timer

        headers = authenitcate()

        lurl = base_url + "/api/log/"
        log_data = {"c"}

        turl = base_url + "api/bay/" + str(bay_id) + "/tools/"
        tresponse = requests.get(turl, headers=headers)
        print "tool response :", tresponse
        tdata = json.loads(tresponse.content)
        for tools in tdata:
            # print tools
            if str(tool_id) == str(tools['id']):
                tool_st = tools['status']

        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(-1, -1, 800, 480)
        self.setWindowTitle("Tool Status")

        print tool_id
        print statusinfo
        font = fontname()
        
        prjurl = base_url + "api/bay/" + \
                str(bay_id) + "/tools/" + str(tool_id) + "/"

        prjresponse = requests.get(prjurl, headers=headers)
            # prid = prdata['current_project']['id']
        prjdata = json.loads(prjresponse.content)

        t5 = QtGui.QPushButton("Idle", self)
        t5.setFont(font)
        t5.setObjectName(_fromUtf8("ID"))
        if tool_st == "ID":
            t5.setStyleSheet("background-color: #8B0000")
        else:
            t5.setStyleSheet("background-color: #ffffff")

        if prjdata['current_project'] == None:
            t5.clicked.connect(self.showdialog2)
        else:
            t5.clicked.connect(self.showdialog)
        t5.resize(291, 41)
        t5.move(230, 30)

        t6 = QtGui.QPushButton("Productive", self)
        t6.setFont(font)
        t6.setObjectName(_fromUtf8("PR"))
        if tool_st == "PR":
            t6.setStyleSheet("background-color: #90EE90")
        else:
            t6.setStyleSheet("background-color: #ffffff")

        if prjdata['current_project'] == None:
            t6.clicked.connect(self.showdialog2)
        else:
            t6.clicked.connect(self.showdialog)
        # t6.clicked.connect(self.showdialog)
        t6.resize(291, 41)
        t6.move(230, 90)

        t7 = QtGui.QPushButton("Installation/Config", self)
        t7.setFont(font)
        t7.setObjectName(_fromUtf8("IN"))
        if tool_st == "IN":
            t7.setStyleSheet("background-color: #FFFF00")
        else:
            t7.setStyleSheet("background-color: #ffffff")

        if prjdata['current_project'] == None:
            t7.clicked.connect(self.showdialog2)
        else:
            t7.clicked.connect(self.showdialog)
        # t7.clicked.connect(self.showdialog)
        t7.resize(291, 41)
        t7.move(230, 150)

        t15 = QtGui.QPushButton("Maintenance", self)
        t15.setFont(font)
        t15.setObjectName(_fromUtf8("MA"))
        if tool_st == "MA":
            t15.setStyleSheet("background-color: #00BFFF")
        else:
            t15.setStyleSheet("background-color: #ffffff")

        if prjdata['current_project'] == None:
            t15.clicked.connect(self.showdialog2)
        else:
            t15.clicked.connect(self.showdialog)
        # t15.clicked.connect(self.showdialog)
        t15.resize(100, 300)
        t15.move(580, 30)

        t8 = QtGui.QPushButton("Statistics", self)
        t8.setFont(font)
        t8.setObjectName(_fromUtf8("t8"))
        # t8.clicked.connect(self.showdialog1)
        t8.clicked.connect(self.showdialog1)
        t8.resize(291, 41)
        t8.move(230, 210)

        t9 = QtGui.QPushButton("Project", self)
        t9.setFont(font)
        t9.setObjectName(_fromUtf8("t9"))
        t9.clicked.connect(self.work)
        t9.resize(291, 41)
        t9.move(230, 280)

        t10 = QtGui.QPushButton("Back", self)
        t10.setFont(font)
        t10.setObjectName(_fromUtf8("t10"))
        t10.clicked.connect(self.back1)
        t10.resize(291, 41)
        t10.move(50, 350)

        t11 = QtGui.QPushButton("Save/Exit", self)
        t11.setFont(font)
        t11.setObjectName(_fromUtf8("t11"))
        t11.clicked.connect(self.quit1)
        t11.resize(291, 41)
        t11.move(420, 350)

        # timer.timeout.connect(self.tool_sleep)
        # timer.setSingleShot(True)
        # timer.start(5000)

        self.show()

    def showdialog(self):
        global tool_id
        global bay_id
        global uid
        global prid

        quit_msg = "Confirm your action !"
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:

            headers = authenitcate()
            sender_button = self.sender()
            tstatus = str(sender_button.objectName())
            # print tstatus
            purl = base_url + "api/bay/" + \
                str(bay_id) + "/tools/" + str(tool_id) + "/"
            if tstatus == "PR":
                status = "PR"
            elif tstatus == "ID":
                status = "ID"
            elif tstatus == "IN":
                status = "IN"
            elif tstatus == "MA":
                status = "MA"

            tool_name_status = {"status": str(status)}
            response = requests.patch(
                purl,
                data=json.dumps(tool_name_status),
                headers=headers)

            headers = authenitcate()
            sender_button = self.sender()
            tstatus = str(sender_button.objectName())
            # print tstatus

            prurl = base_url + "api/bay/" + \
                str(bay_id) + "/tools/" + str(tool_id) + "/"

            prresponse = requests.get(prurl, headers=headers)
            prdata = json.loads(prresponse.content)
            prid = prdata['current_project']['id']

            url = base_url + "api/log/"
            post_data = {"user": uid,
                         "project": prid,
                         "status": tstatus,
                         "tool": tool_id}

            response = requests.post(
                url,
                data=json.dumps(post_data),
                headers=headers)
            print"log response", response

            self.close()
            est = second_view(self)

        else:
            pass

    
    def showdialog1(self):
        headers = authenitcate()
        uzurl = base_url + "api/tools/" + str(tool_id) + "/utilization/"
        uzresponse = requests.get(uzurl, headers=headers)
        # print "util response :", uzresponse
        tdata = json.loads(uzresponse.content)
        choice = QtGui.QMessageBox.information(
            self, 'Stats', "Productive:" + str(tdata['Productive']) + '\n' + "Install/Config:" + str(tdata['Installation']) + '\n' + "Idle:" + str(tdata['Idle']) + '\n' + "Maintenance:" + str(tdata['Maintenance']))

    def showdialog2(self):
        choice = QtGui.QMessageBox.information(self, 'Message',"Please Select the project before changing the status."
            )      

    def back1(self):
        self.close()
        test1 = first_view(self)
        self.test1.show()

    def work(self):
        global timer
        self.close()
        # timer.stop()
        test = work_view(self)

    def stats(self):
        self.close()
        test = StatsView(self)

    def quit1(self):
        self.close()
        test_quit = Entry_view(self)
        self.test_quit.show()

    def tool_sleep(self):
        self.close()
        test5 = Entry_view(self)
        self.test5.show()

class StatsView(QtGui.QMainWindow):
    def __init__(self, parent=None):
        global tool_id
        global bay_id
        global uid
        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(40,40, 800, 480)
        font = fontname()
        headers = authenitcate()
        uzurl = base_url + "api/tools/" + str(tool_id) + "/utilization/"
        uzresponse = requests.get(uzurl, headers=headers)
        print "util response :", uzresponse
        tdata = json.loads(uzresponse.content)
        
        p = str(tdata['Productive_Time'])
        ie = str(tdata['Idle_Time'])
        ic = str(tdata['Installation_Time'])
        m = str(tdata['Maintenance_Time'])

        sizes = [ic,p,ie,m]
        labels = 'Install/Config','Productive','Idle','Maintenance'
        colors = ['yellow', 'yellowgreen', 'red', 'skyblue']
        explode = (0, 0, 0, 0)  # explode 1st slice
 
# Plot
        plt.pie(sizes,  labels=labels, explode = explode, colors=colors, autopct='%1.1f%%')
        centre_circle = plt.Circle((0,0),0.39,color='black', fc='white',linewidth=1.25)
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)

        plt.axis('equal')
        plt.savefig('/home/pi/RPi_Lab/pie.png')
        # plt.show()

        t1 = QtGui.QPushButton(self)
        t1.setObjectName(_fromUtf8("t1"))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(
            QtGui.QPixmap("/home/pi/RPi_Lab/pie.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off)
        t1.setIcon(icon1)
        t1.setIconSize(QtCore.QSize(750,450))
        t1.setFont(font)
        t1.resize(800, 480)
        t1.move(0, 0)

        timer.timeout.connect(self.tool_sleep)
        timer.setSingleShot(True)
        timer.start(3000)

        self.show()

    def tool_sleep(self):
        self.close()
        test = Entry_view(self)
        self.test.show()

class work_view(QtGui.QMainWindow):

    def __init__(self, parent=None):
        global timer
        global selectecd_text
        global tool_id

        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(-1, -1, 800, 480)
        self.setWindowTitle("Project Selection")

        headers = authenitcate()
        font = fontname()

        purl = base_url + "api/tools/" + str(tool_id) + "/assign-projects/"
        project_list_data = requests.get(purl, headers=headers)

        presponse = json.loads(project_list_data.content)
        print presponse
        # print presponse['name']
        projects = []
        for data in presponse:
            # print data
            projects.append(data['project']['name'])

        comboBox = QtGui.QComboBox(self)
        print type(projects)
        print projects
        comboBox.addItems(projects)
        comboBox.activated[str].connect(self.selected)
        comboBox.move(123, 180)
        comboBox.resize(480, 50)

        t15 = QtGui.QPushButton("Back", self)
        t15.setFont(font)
        t15.setObjectName(_fromUtf8("t15"))
        t15.clicked.connect(self.back)
        t15.resize(211, 41)
        t15.move(60, 400)

        t16 = QtGui.QPushButton("Save/Exit", self)
        t16.setFont(font)
        t16.setObjectName(_fromUtf8("t16"))
        t16.clicked.connect(self.quit)
        t16.resize(211, 41)
        t16.move(450, 400)

        self.show()

    def back(self):
        global timer
        self.close()
        # timer.stop()
        test3 = second_view(self)

    def quit(self):
        self.close()
        test_quit3 = Entry_view(self)
        self.test_quit3.show()

    def tool_sleep(self):
        self.close()
        test5 = Entry_view(self)
        self.test5.show()

    def selected(self,text):
        global tool_id
        global bay_id
        global uid
        global tool_id
        global selected_text
        selected_text = text
        print "Selected :",selected_text

        headers = authenitcate()
        purl = base_url+"api/tools/"+str(tool_id)+"/assign-projects/"
        project_list_data = requests.get(purl,headers=headers)
        presponse = json.loads(project_list_data.content)
        print presponse
        # print presponse['name']  
        count = 0     
        for pdata in presponse:
          #  print "rdata:",rdata
            if str(selected_text) == str(pdata['project']['name']):
                count += 1
                xpdata = pdata
                break
        if count > 0:
            pid = pdata['project']['id']

        print "Project ID:",pid

        piurl = base_url+"api/tools/"+str(tool_id)+"/"
        project_id_data = {"current_project": str(pid)}
        response = requests.patch(
                piurl,
                data=json.dumps(project_id_data),
                headers=headers)

class NoButton(QtGui.QMainWindow):

    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(-1, -1, 800, 480)
        font = fontname()
        t1 = QtGui.QPushButton("No Button Added/Contact Administrator", self)
        t1.setFont(font)
        t1.resize(800, 480)
        t1.move(0, 0)

        timer.timeout.connect(self.tool_sleep)
        timer.setSingleShot(True)
        timer.start(30000)

        self.show()

    def tool_sleep(self):
        self.close()
        test = Entry_view(self)
        self.test.show()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())

    myapp = Entry_view()
    sys.exit(app.exec_())
