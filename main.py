## Project imports
from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome,GetUserInfo
from models import IncType,BillType,Bill
from widgets import MainWindow,DataGrid

## Kivy imports (for GUI)
import kivy 
kivy.require('2.1.0')
from kivy.app import App
from kivy.core.window import Window

from datetime import date

class UpcomingBillsView(DataGrid):
    def __init__(self):
        self.queryData = QueryBillsAndIncome.getTopNByDueDate(N=50)
        self.startBal = GetUserInfo.getCurrentBalance()

        headers = ['Name','Amount','Due Date','Rolling Balance','Paid?']
        tableData = self.makeTableData()
        actionCols = ['Mark Paid','Edit']
        actions = [self.togglePaid,lambda x:print(f"Edit bill {x}")]
        super().__init__(headers,tableData,actionCols=actionCols,actions=actions,hasIndex=True)

    def makeTableData(self):
        tableData = []
        rollBal = self.startBal
        for bill in self.queryData:
            rollBal += bill.amount
            tableData.append((bill.id,bill.name,bill.amount,bill.dueDate,rollBal,bill.paidInSession))
        return tableData
    
    def setStartBal(self,startBal):
        self.startBal = startBal
        self.presentData = self.makeTableData()
        self.reloadData()
    
    def togglePaid(self,obj):
        for bill in self.queryData:
            if bill.id == obj.dataIdx:
                paidBill = bill
                break
        
        if paidBill.paidInSession:
            changeAmount = -paidBill.amount
            paidBill.paidInSession = False
        else:
            changeAmount = paidBill.amount
            paidBill.paidInSession = True

        for i,point in enumerate(self.presentData):
            if point[3] >= paidBill.dueDate:
                if point[0] == paidBill.id:
                    self.presentData[i]=(point[0],point[1],point[2],point[3],point[4]-changeAmount,bill.paidInSession)
                else:
                    self.presentData[i]=(point[0],point[1],point[2],point[3],point[4]-changeAmount,point[5])

        self.reloadData()
        

## Actual Application
class BudgetApp(App):
    mainWindow = None
    currentView = None
    def build(self):
        ## Creates an instance of MainWindow, and selects "Upcoming Bills" as the selected view by default
        self.mainWindow = MainWindow()
        self.currentView = self.getUpcomingBillsView()
        return self.mainWindow

    def getUpcomingBillsView(self):
        newView = UpcomingBillsView()
        self.mainWindow.topBar.titleLabel.text = "Upcoming Bills"
        self.mainWindow.topBar.amountInput.text = str(newView.startBal)
        self.mainWindow.topBar.amountInput.bind(on_text_validate=lambda obj:newView.setStartBal(float(obj.text)))
        self.mainWindow.topBar.saveButton.bind(on_press=self.saveUpcomingBillsView)
        self.mainWindow.selectedView.clear_widgets()
        self.mainWindow.selectedView.add_widget(newView)
        return newView

    def saveUpcomingBillsView(self,obj):
        newCurrentBalance = self.mainWindow.topBar.amountInput.text
        changedBillIds = [str(bill.id) for bill in self.currentView.queryData if bill.paidInSession]
        QueryBillsAndIncome.deleteByIds(changedBillIds)
        GetUserInfo.setCurrentBalance(newCurrentBalance)
        self.getUpcomingBillsView()



## Setup the db (duh...)
db_setup()
## For testing purposes, we have some dummy data we can load 
load_test_data()

if __name__ == '__main__':
    Window.size=(800,800)
    BudgetApp().run()