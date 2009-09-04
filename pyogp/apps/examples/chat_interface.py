from Tkinter import *
from pyogp.lib.client.agent import Agent
from eventlet import api
import logging

class Login(object):
     
    def __init__(self, parent, agent):
        
        self.parent = parent
        self.agent = agent
        self.frame = Frame(parent.frame)
        self.frame.pack()
        
        self.first_name_label = Label(self.frame, text="First Name") 
        self.first_name_label.pack(side=TOP)
        self.first_name = Entry(self.frame)
        self.first_name.pack(side=TOP)
        
        self.first_name_label = Label(self.frame, text="Last Name") 
        self.first_name_label.pack(side=TOP) 
        self.last_name = Entry(self.frame)
        self.last_name.pack(side=TOP)
        
        self.password_label = Label(self.frame, text="Password")
        self.password_label.pack(side=TOP)
        self.password = Entry(self.frame)
        self.password.pack(side=TOP)
         
        self.login_button = Button(self.frame, text="Login", command=self.login)
        self.login_button.pack(side=TOP)
        
    def login(self):
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG) # seems to be a no op, set it for the logger
        formatter = logging.Formatter('%(asctime)-30s%(name)-30s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

       # setting the level for the handler above seems to be a no-op
       # it needs to be set for the logger, here the root logger
       # otherwise it is NOTSET(=0) which means to log nothing.
        logging.getLogger('').setLevel(logging.DEBUG)        
        print self.first_name.get()
        api.spawn(self.agent.login,
                  "https://login.aditi.lindenlab.com/cgi-bin/login.cgi",
                  self.first_name.get(), 
                  self.last_name.get(),
                  self.password.get(),
                  start_location = None, 
                  connect_region = True)
        while self.agent.connected == False:
            api.sleep(0)
        while self.agent.region.connected == False:
            api.sleep(0)      

        self.parent.chat = Chat(self.parent, self.agent)
        self.frame.pack_forget()
        
class Logout(object):
    
    def __init__(self, parent,agent):
        
        self.parent = parent
        self.agent = agent
        self.frame = Frame(parent.frame)
        self.frame.pack()
        self.logout_button = Button(self.frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=BOTTOM)
        
    def logout(self):
        self.agent.logout()
        
class Chat(object):
    
    def __init__(self, parent, agent):
        self.parent = parent
        self.agent = agent
        self.frame = Frame(parent.frame)
        self.frame.pack()
        self.list = Listbox(self.frame)
        self.list.pack(side=RIGHT, fill=Y)
        self.chat_log = Text(self.frame)
        self.chat_log.pack(side=TOP, fill=Y)        
        self.chat_entry = Text(self.frame, height=5)
        self.chat_entry.pack(side=BOTTOM, fill=X)
        self.parent.logout = Logout(parent, agent)
        
class Chat_window(object):
    
    def __init__(self, frame):
        self.frame = Frame(frame)
        self.frame.pack()
        self.chat = None  
        self.agent = Agent()
        self.login = Login(self, self.agent)
        self.logout = None

def main():
    root = Tk()
    Chat_window(root)
    root.title("Foo")
    root.mainloop()