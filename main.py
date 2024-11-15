## Project imports
from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome,GetUserInfo
from models import IncType,BillType,Bill
from widgets import MainWindow,DataGrid,BillForm
from kivy.uix.screenmanager import Screen,ScreenManager

## Kivy imports (for GUI)
import kivy 
kivy.require('2.1.0')
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock

from datetime import date

class AddBillView(Screen):
    def __init__(self):
        self.form = BillForm()
        super().__init__(name='Add Bill')
        self.add_widget(self.form)

class UpcomingBillsView(Screen):
    def __init__(self):
        self.queryData = QueryBillsAndIncome.getTopNByDueDate(N=50)
        self.startBal = GetUserInfo.getCurrentBalance()

        headers = ['Name','Amount','Due Date','Rolling Balance','Paid?']
        tableData = self.makeTableData()
        actionCols = ['Mark Paid','Edit']
        actions = [self.togglePaid,lambda x:print(f"Edit bill {x}")]
        self.grid = DataGrid(headers,tableData,actionCols=actionCols,actions=actions,hasIndex=True)
        super().__init__(name='Upcoming Bills')
        self.add_widget(self.grid)

    def hardRefresh(self):
        self.queryData = QueryBillsAndIncome.getTopNByDueDate(N=50)
        self.startBal = GetUserInfo.getCurrentBalance()
        tableData = self.makeTableData()
        
        self.grid.allData = tableData
        self.grid.presentData = tableData
        self.grid.reloadData()
    
    def makeTableData(self):
        tableData = []
        rollBal = self.startBal
        for bill in self.queryData:
            rollBal += bill.amount
            tableData.append((bill.id,bill.name,bill.amount,bill.dueDate,rollBal,bill.paidInSession))
        return tableData
    
    def setStartBal(self,startBal):
        self.startBal = startBal
        self.grid.presentData = self.makeTableData()
        self.grid.reloadData()
    
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

        for i,point in enumerate(self.grid.presentData):
            if point[3] >= paidBill.dueDate:
                if point[0] == paidBill.id:
                    self.grid.presentData[i]=(point[0],point[1],point[2],point[3],point[4]-changeAmount,bill.paidInSession)
                else:
                    self.grid.presentData[i]=(point[0],point[1],point[2],point[3],point[4]-changeAmount,point[5])

        self.grid.reloadData()
        

## Actual Application
class BudgetApp(App):
    mainWindow = None
    def build(self):
        ## Creates an instance of MainWindow, and selects "Upcoming Bills" as the selected view by default
        self.mainWindow = MainWindow()
        self.mainWindow.selectedView.add_widget(UpcomingBillsView())
        self.mainWindow.selectedView.add_widget(AddBillView())
        self.getUpcomingBillsView()
        return self.mainWindow

    def getUpcomingBillsView(self,dt=0):
        self.mainWindow.selectedView.current = 'Upcoming Bills'
        self.mainWindow.selectedView.current_screen.hardRefresh()
        ## Change Title
        self.mainWindow.topBar.titleLabel.text = "Upcoming Bills"
        ## Make Amount editable and default it to the saved starting amount. If user changes and presses Enter, will update the rolling balance column
        self.mainWindow.topBar.amountInput.readonly = False
        self.mainWindow.topBar.amountInput.text = str(self.mainWindow.selectedView.current_screen.startBal)
        self.mainWindow.topBar.amountInput.bind(on_text_validate=lambda obj:self.mainWindow.selectedView.current_screen.setStartBal(float(obj.text)))
        ## Bind the save button to the saveUpcomingBillsView function
        self.mainWindow.topBar.saveButton.bind(on_press=self.saveUpcomingBillsView)
        self.mainWindow.topBar.addBillButton.bind(on_press=self.getAddBillView)

    def saveUpcomingBillsView(self,obj):
        try:
            newCurrentBalance = self.mainWindow.topBar.amountInput.text
            changedBillIds = [str(bill.id) for bill in self.mainWindow.selectedView.current_screen.queryData if bill.paidInSession]
            QueryBillsAndIncome.deleteByIds(changedBillIds)
            GetUserInfo.setCurrentBalance(newCurrentBalance)
            self.getUpcomingBillsView()
        except:
            pass

    def getAddBillView(self,dt=0):
        self.mainWindow.selectedView.current = 'Add Bill'
        ## Change Title
        self.mainWindow.topBar.titleLabel.text = "Add New Bill"
        ## Make Amount read-only
        self.mainWindow.topBar.amountInput.readonly = True
        ## Bind the form buttons to the correct actions 
        self.mainWindow.selectedView.current_screen.form.cancelField.bind(on_press=self.getUpcomingBillsView)
        self.mainWindow.selectedView.current_screen.form.submitField.bind(on_press=self.saveAddBillView)
    
    def saveAddBillView(self,obj):
        form = self.mainWindow.selectedView.current_screen.form
        if not form.validateFields():
            print("Problem validating fields: see any error messages above.")
            return
        match form.incTypeField.text:
            case 'None':
                newBill = Bill('NULL',form.nameField.text,float(form.amountField.text),form.nextDueField.getDateValue().isoformat(),0,int(form.constantField.active))
                QueryBillsAndIncome.insertOne(newBill)
                form.nameField.text = ''
                form.amountField.text = ''
                form.nextDueField.clearField()
                form.incTypeField.text = 'Select'
                form.incAmountField.text = ''
                form.categoryField.text = ''
                form.constantField.active = False
                self.getUpcomingBillsView()
                return
            case 'Day':
                newBillType = BillType(form.nameField.text,float(form.amountField.text),form.nextDueField.getDateValue().isoformat(),IncType.DAY.value,int(form.incAmountField.text),0,0,0,int(form.constantField.active))
            case 'Month':
                newBillType = BillType(form.nameField.text,float(form.amountField.text),form.nextDueField.getDateValue().isoformat(),IncType.MONTH.value,0,int(form.incAmountField.text),0,0,int(form.constantField.active))
            case 'Year':
                newBillType = BillType(form.nameField.text,float(form.amountField.text),form.nextDueField.getDateValue().isoformat(),IncType.YEAR.value,0,0,int(form.incAmountField.text),0,int(form.constantField.active))
        newBillTypeId = QueryBillType.insertOne(newBillType)
        newBillType.id = newBillTypeId
        QueryBillsAndIncome.mergeBills(newBillType.makeBillInstances())
        form.nameField.text = ''
        form.amountField.text = ''
        form.nextDueField.clearField()
        form.incTypeField.text = 'Select'
        form.incAmountField.text = ''
        form.categoryField.text = ''
        form.constantField.active = False
        self.getUpcomingBillsView()



## Setup the db (duh...)
db_setup()
## For testing purposes, we have some dummy data we can load 
load_test_data()

if __name__ == '__main__':
    Window.size=(800,800)
    BudgetApp().run()