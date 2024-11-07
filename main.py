## Project imports
from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome
from models import IncType,BillType,Bill
from widgets import MainWindow

## Kivy imports (for GUI)
import kivy 
kivy.require('2.1.0')
from kivy.app import App
from kivy.core.window import WindowBase


## Actual Application
class BudgetApp(App):
    def build(self):
        bleh = MainWindow()
        bleh.selectedView.currentView.loadStuff()
        return bleh

## Setup the db (duh...)
db_setup()
## For testing purposes, we have some dummy data we can load 
load_test_data()

if __name__ == '__main__':
    WindowBase.height = 500
    WindowBase.width = 500
    BudgetApp().run()