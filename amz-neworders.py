# Created on May 31, 2013
# @author: Tom Eaton
#
# This is the Tk frontend for new orders from key accounts.  Orders are 
# converted from incoming format into Everest Advanced Edition 5.0 compatible
# CSV header and data files.

from lib import model
from views import viewcontroller

app = Application(model.title, model.description, model.filetypes)
app.mainloop()