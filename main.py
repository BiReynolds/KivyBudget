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
from kivy.uix.button import Button

from datetime import date

## Helper functions
def editClicked(obj):
    app.getEditBillView(obj.dataIdx)


## View Functions

class AddBillView(Screen):
    def __init__(self):
        super().__init__(name='Add Bill')
        self.form = BillForm()
        self.add_widget(self.form)

class EditBillView(Screen):
    def __init__(self):
        super().__init__(name='Edit Bill')
        self.billObj = None
        self.form = BillForm()
        self.deleteButton = Button(text="Delete This Bill")
        self.deleteFutureButton = Button(text="Delete All Future Instances")
        self.form.add_widget(self.deleteButton)
        self.form.add_widget(self.deleteFutureButton)
        self.add_widget(self.form)

    def loadBillData(self,billId):
        billObj = QueryBillsAndIncome.byId(billId)
        billTypeObj = None
        if billObj.billTypeId:
            billTypeObj = QueryBillType.byId(billObj.billTypeId)
        self.billObj = billObj
        self.billTypeObj = billTypeObj
        self.form.nameField.text = billObj.name
        self.form.amountField.text = str(billObj.amount)
        self.form.nextDueField.setField(date.fromisoformat(billObj.dueDate))
        if billTypeObj:
            match billTypeObj.incType:
                    case -1:
                        self.form.incTypeField.text = 'None'
                        self.form.incAmountField.text = ''
                    case 0:
                        self.form.incTypeField.text = 'Day'
                        self.form.incAmountField.text = str(billTypeObj.incDays)
                    case 1:
                        self.form.incTypeField.text = 'Month'
                        self.form.incAmountField.text = str(billTypeObj.incMonths)
                    case 2:
                        self.form.incTypeField.text = 'Year'
                        self.form.incAmountField.text = str(billTypeObj.incYears)
        else:
            self.form.incTypeField.text = 'None'
            self.form.incAmountField.text = ''
        self.form.incTypeField.disabled = True
        self.form.incAmountField.readonly = True

        self.form.categoryField.text = str(billObj.category)
        self.form.constantField.text = str(billObj.constant)

class UpcomingBillsView(Screen):
    def __init__(self):
        self.queryData = QueryBillsAndIncome.getTopNByDueDate(N=50)
        self.startBal = GetUserInfo.getCurrentBalance()

        headers = ['Name','Amount','Due Date','Rolling Balance','Paid?']
        tableData = self.makeTableData()
        actionCols = ['Mark Paid','Edit']
        actions = [self.togglePaid,editClicked]
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
        self.mainWindow.selectedView.add_widget(EditBillView())
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

    def getEditBillView(self,id):
        self.mainWindow.selectedView.current = 'Edit Bill'
        # Change Title
        self.mainWindow.topBar.titleLabel.text = "Edit Bill"
        # Make Amount read-only
        self.mainWindow.topBar.amountInput.readonly = True
        # Load info for the selected bill to edit by default
        self.mainWindow.selectedView.current_screen.loadBillData(id)
        # Bind the form buttons to the correct actions
        self.mainWindow.selectedView.current_screen.form.cancelField.bind(on_press=self.getUpcomingBillsView)
        self.mainWindow.selectedView.current_screen.form.submitField.bind(on_press=self.saveEditBillView)
        self.mainWindow.selectedView.current_screen.deleteButton.bind(on_press = self.deleteBillInstance)
        self.mainWindow.selectedView.current_screen.deleteFutureButton.bind(on_press=self.deleteBillType)

    def saveEditBillView(self,obj):
        form = self.mainWindow.selectedView.current_screen.form
        billObj = self.mainWindow.selectedView.current_screen.billObj
        billTypeObj = self.mainWindow.selectedView.current_screen.billTypeObj
        ## Make changes to bill object
        billObj.name = form.nameField.text
        billObj.amount = float(form.amountField.text)
        billObj.dueDate = form.nextDueField.getDateValue().isoformat()
        billObj.category = int(form.categoryField.text)
        billObj.constant = int(form.constantField.active)
        ## Make changes to billType object (if applicable)
        if billTypeObj:
            billTypeObj.name = form.nameField.text
            billTypeObj.amount = float(form.amountField.text)
            billTypeObj.category = int(form.categoryField.text)
            billTypeObj.constant = int(form.constantField.active)
        ## Make changes in db
        if billTypeObj:
            QueryBillType.simpleEdit(billTypeObj)
            QueryBillsAndIncome.simpleEditByType(billObj)
        else:
            QueryBillsAndIncome.simpleEdit(billObj)
        self.getUpcomingBillsView()

    def deleteBillInstance(self,obj):
        print("Delete Bill Instance")

    def deleteBillType(self,obj):
        print("Delete Bill Type")

## Setup the db (duh...)
db_setup()
## For testing purposes, we have some dummy data we can load 
load_test_data()

if __name__ == '__main__':
    Window.size=(800,800)
    app = BudgetApp()
    app.run()