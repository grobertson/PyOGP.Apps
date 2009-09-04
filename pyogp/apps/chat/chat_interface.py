from Tkinter import *

class Login(object):
     
    def __init__(self, parent):
        
        self.parent = parent
        self.frame = Frame(parent)
        self.frame.pack()
        
        self.first_name_label = Label(self.frame, text="First Name") 
        self.first_name_label.pack(side=TOP)
        self.first_name = Entry(self.frame)
        self.first_name.pack(side=TOP)
        
        self.first_name_label = Label(self.frame, text="Last Name") 
        self.first_name_label.pack(side=TOP) 
        self.last_name = Entry(self.frame)
        self.last_name.pack(side=TOP)
         
        self.login_button = Button(self.frame, text="Login", command=self.login)
        self.login_button.pack(side=TOP)
        
    def login(self):
        self.frame.pack_forget()
        self.parent.chat = Chat(self.parent)

class Chat(object):
    
    def __init__(self, parent):
        self.frame = Frame(parent)
        self.frame.pack()
        self.list = Listbox(self.frame)
        self.list.pack(side=RIGHT, fill=Y)
        self.chat_log = Text(self.frame)
        self.chat_log.pack(side=TOP, fill=Y)        
        self.chat_entry = Text(self.frame, height=5)
        self.chat_entry.pack(side=BOTTOM, fill=X)

class Chat_window(object):
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = Frame(parent)
        self.frame.pack()
        self.login = Login(self.frame)
        self.chat = None  
        
root = Tk()
Chat_window(root)
root.mainloop()