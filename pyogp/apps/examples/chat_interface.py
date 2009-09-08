from Tkinter import *
from pyogp.lib.client.agent import Agent
from eventlet import api
import logging

class Login(object):
    """ Initial login screen """
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
        self.password = Entry(self.frame, show="*")
        self.password.bind("<Return>", self.login)
        self.password.pack(side=TOP)

        self.login_button = Button(self.frame, text="Login", command=self.login)
        self.login_button.pack(side=TOP)

    def login(self, entry=None):
        """ Logs in a pyogp agent """
        self.agent.login(
                         "https://login.agni.lindenlab.com/cgi-bin/login.cgi",
                         self.first_name.get(), 
                         self.last_name.get(),
                         self.password.get(),
                         start_location = None, 
                         connect_region = True)
        while self.agent.connected == False:
            api.sleep(0)
        while self.agent.region.connected == False:
            api.sleep(0)      
        self.agent.say("chat window")
        self.parent.init_chat()
        self.frame.pack_forget()

class Logout(object):
    """  Logout button """
    def __init__(self, parent,agent):
        self.parent = parent
        self.agent = agent
        self.frame = Frame(parent.frame)
        self.frame.pack()
        self.logout_button = Button(self.frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=BOTTOM)

    def logout(self):
        """ Logs out a PyOGP agent """
        self.agent.logout()
        self.parent.tear_down()

class Chat(object):
    """ Chat widgets: window, entry, and agent list """    
    def __init__(self, parent, agent):
        self.parent = parent
        self.agent = agent
        self.frame = Frame(parent.frame)
        self.frame.pack()
        self.list = Listbox(self.frame)
        self.list.pack(side=RIGHT, fill=Y)
        self.chat_log = Text(self.frame)
        self.chat_log.pack(side=TOP, fill=Y)        
        self.chat_entry = Entry(self.frame)
        self.chat_entry.bind("<Return>", self.send_chat)
        self.chat_entry.pack(side=BOTTOM, fill=X)

    def send_chat(self, event):
        """ sends a chat message """
        self.agent.say(self.chat_entry.get())
        event.widget.delete(0, END)

class Chat_window(object):
    """ Chat window """
    def __init__(self, frame):
        self.frame = Frame(frame)
        self.frame.pack()
        self.agent = Agent()
        self.login = Login(self, self.agent)
        self.logout = None
        self.chat = None 

    def init_chat(self):
        """ Initializes a chat widgets after login """
        self.chat = Chat(self, self.agent)
        self.logout = Logout(self, self.agent)
        

    def tear_down(self):
        """ Tears down chat widgets and logout widget after logout """
        self.chat.frame.pack_forget()
        self.logout.frame.pack_forget()

def main():
    root = Tk()
    Chat_window(root)
    root.title("PyOGP Chat interface")
    root.mainloop()