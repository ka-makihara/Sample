#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     13/02/2015
# Copyright:   (c) makihara 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
class Event:
    def __init__(self):
        self.listeners = []
    def __call__(self, *params):
        for l in self.listeners:
            l(*params)
    def __add__(self, listener):
        self.listeners.append(listener)
        return self
    def __sub__(self, listener):
        self.listeners.remove(listener)
        return self

class MyClass:
   def __init__(self):
    self.Clicked = Event()
   def click(self, button):
      self.Clicked(self, button)

def onClick(sender, button):
   print 'Button clicked: %s' % button

o = MyClass()
o.Clicked += onClick
o.click('Right')
