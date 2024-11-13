## Project imports
from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome
from models import IncType,BillType,Bill
from widgets import MainWindow,DataGrid

## Kivy imports (for GUI)
import kivy 
kivy.require('2.1.0')
from kivy.app import App
from kivy.core.window import Window,WindowBase


## Actual Application
class BudgetApp(App):
    def build(self):
        bleh = MainWindow()

        headers = ['Name','Amount','Due Date','Rolling Balance']
        queryData = QueryBillsAndIncome.getTopNByDueDate(N=50)
        tableData = []
        rollBal = 1000
        for bill in queryData:
            rollBal += bill.amount
            tableData.append((bill.id,bill.name,bill.amount,bill.dueDate,rollBal))
        actionCols = ['Mark Paid','Edit']
        actions = [lambda x:print(f"Marked bill {x} paid!"),lambda x:print(f"Edit bill {x}")]
        bleh.selectedView.add_widget(DataGrid(headers,tableData,actionCols=actionCols,actions=actions))
        return bleh

## Setup the db (duh...)
db_setup()
## For testing purposes, we have some dummy data we can load 
load_test_data()

if __name__ == '__main__':
    Window.size=(500,500)
    BudgetApp().run()