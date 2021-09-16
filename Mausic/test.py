from tkinter import ttk 


s = ttk.Style()
print(s.theme_names())
print(s.theme_use())
s.theme_use('winnative')