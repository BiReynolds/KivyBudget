import kivy 
import re
from datetime import date
kivy.require('2.1.0')
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty

from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome
from models import IncType,BillType,Bill

## Special widgets

class EasyDropDown(Button):
    options = DropDown()
    
    def __init__(self,optionList,defaultText = 'Select',**kwargs):
        super().__init__(**kwargs)
        self.text = defaultText

        for option in optionList:
            btn = Button(text=str(option),size_hint_y=None,height=20)
            btn.bind(on_release=lambda btn: self.options.select(btn.text))
            self.options.add_widget(btn)
        
        self.bind(on_release=self.options.open)
        self.options.bind(on_select=lambda instance, x: setattr(self,'text',x)) 

class DateField(BoxLayout):
    orientation = 'horizontal'
    monthField = Button()
    monthOptions = DropDown()
    dayField = Button()
    dayOptions = DropDown()
    yearField = Button()
    yearOptions = DropDown()

    def __init__(self,defaultMonth = 'MM',defaultDay = 'DD', defaultYear='YYYY',minYear = 1900, maxYear = 2100,**kwargs):
        super().__init__(**kwargs)
        
        self.monthField.text = defaultMonth
        self.dayField.text = defaultDay
        self.yearField.text = defaultYear

        self.monthField.bind(on_release=self.monthOptions.open)
        self.dayField.bind(on_release=self.dayOptions.open)
        self.yearField.bind(on_release=self.yearOptions.open)

        self.monthOptions.bind(on_select=lambda instance, x: setattr(self.monthField,'text',x))
        self.dayOptions.bind(on_select=lambda instance, x: setattr(self.dayField,'text',x))
        self.yearOptions.bind(on_select=lambda instance, x: setattr(self.yearField,'text',x))

        for i in range(1,13):
            btn = Button(text=str(i),size_hint_y=None,height=20)
            btn.bind(on_release=lambda btn: self.monthOptions.select(btn.text))
            self.monthOptions.add_widget(btn)

        for i in range(1,32):
            btn = Button(text=str(i),size_hint_y=None,height=20)
            btn.bind(on_release=lambda btn: self.dayOptions.select(btn.text))
            self.dayOptions.add_widget(btn)
        
        for i in range(minYear,maxYear+1):
            btn = Button(text=str(i),size_hint_y=None,height=20)
            btn.bind(on_release=lambda btn: self.yearOptions.select(btn.text))
            self.yearOptions.add_widget(btn)

        self.add_widget(self.monthField)
        self.add_widget(self.dayField)
        self.add_widget(self.yearField)

    def getDateValue(self):
        try:
            return date(int(self.yearField.text),int(self.monthField.text),int(self.dayField.text))
        except:
            return None
        
    def clearField(self):
        self.monthField.text = 'MM'
        self.dayField.text = 'DD'
        self.yearField.text = 'YY'

class MoneyInput(TextInput):
    pat = re.compile('[^0-9]')
    multiline = False
    write_tab = False

    def insert_text(self,substring,from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s=re.sub(pat,'',substring)
        else:
            s='.'.join(re.sub(pat,'',s) for s in substring.split('.',1))
        return super().insert_text(s,from_undo = from_undo)

class DataButton(Button):
    def __init__(self,dataIdx,colIdx=0,**kwargs):
        super().__init__(**kwargs)
        self.colIdx = colIdx
        self.dataIdx = dataIdx

class DataGrid(BoxLayout):
    orientation = 'vertical'

    def __init__(self,headers,data,row_height = 50,actionCols=[],actions=[], hasIndex=True, **kwargs):
        if not hasIndex and len(headers)!=len(data[0]):
            print("Data width does not match headers")
            return
        if hasIndex and len(headers)!=len(data[0])-1:
            print("Data width does not match headers")
            return
        if len(actionCols)!=len(actions):
            print("Action columns length does not match actions length")
            return
        super().__init__(**kwargs)
        ## Headers and allData represent the read-only data to be displayed.  Present data stores what the user
        ## is currently seeing in the grid (subject to filters / sorting).  Action cols represent any actions we want
        ## to appear on every row ("Mark Paid" for example), and the actions input is the actual function that should
        ## that should be called (should accept )
        self.headers = headers
        self.allData = data
        self.presentData = data[:]
        self.row_height = row_height
        self.actionCols = actionCols
        self.actions=actions
        self.hasIndex = hasIndex

        ## Set up the visual aspect of the widget
        self.reloadData()

    def reloadData(self):
        self.clear_widgets()

        N = len(self.headers)+len(self.actionCols)

        headerBar = BoxLayout(orientation = 'horizontal',size_hint=(1,None),height=self.row_height)
        scrollView = ScrollView(size_hint=(1,1))
        newLayout = GridLayout(cols=N,row_force_default=True,row_default_height=self.row_height,size_hint=(1,None))
        newLayout.bind(minimum_height=newLayout.setter('height'))

        for i,header in enumerate(self.headers):
            newButton = DataButton(dataIdx = i,text=header,size_hint_x=1/N)
            newButton.bind(on_press = lambda obj: self.sortBy(obj.dataIdx))
            headerBar.add_widget(newButton)
        for actionHeader in self.actionCols:
            headerBar.add_widget(Label(text=actionHeader,size_hint_x=1/N))
        
        for data in self.presentData:
            if self.hasIndex:
                for point in data[1:]:
                    newLayout.add_widget(Label(text=str(point),size_hint_x=1/N))
            else:
                for point in data:
                    newLayout.add_widget(Label(text=str(point),size_hint_x=1/N))
            for i,action in enumerate(self.actionCols):
                actionButton = DataButton(colIdx=i,dataIdx = data[0], text = action,size_hint_x = 1/N)
                actionButton.bind(on_press=lambda obj: self.actions[obj.colIdx](obj))
                newLayout.add_widget(actionButton)

        self.add_widget(headerBar)
        scrollView.add_widget(newLayout)
        self.add_widget(scrollView)

    def sortBy(self,idx):
        if self.hasIndex:
            idx+=1
        workingData = self.presentData[:]
        workingData.sort(key=lambda x:x[idx])
        self.presentData = workingData
        self.reloadData()

class BillForm(GridLayout):

    def __init__(self,id=None,name=None,amount=None,nextDue=None,incType=None,incDays=None,incMonths=None,incYears=None,category=None,constant=None):
        super().__init__()
        self.orientation = 'lr-tb'
        self.cols = 2
        self.row_force_default = True
        self.row_default_height = 30
        self.spacing = 10

        self.id = id
        self.nameField = TextInput(multiline=False,write_tab = False,size_hint_x=None,width=550)
        if name:
            self.nameField.text = name
        self.amountField = MoneyInput(size_hint_x=None,width=550)
        if amount:
            self.amountField.text = amount
        if nextDue:
            self.nextDueField = DateField(nextDue.month,nextDue.day,nextDue.year,size_hint_x=None,width=550)
        else:
            self.nextDueField = DateField(minYear=2020,maxYear=2100,size_hint_x=None,width=550)
        self.incTypeField = EasyDropDown(['None','Day','Month','Year'],size_hint_x=None,width=550)
        self.incAmountField = MoneyInput(size_hint_x=None,width=550)
        if incType:
            match incType:
                case -1:
                    self.incTypefield = 'None'
                    self.incAmountField.text = 0
                case 1:
                    self.incTypeField.text = 'Day'
                    self.incAmountField.text = str(incDays)
                case 2:
                    self.incTypeField.text = 'Month'
                    self.incAmountField.text = str(incMonths)
                case 3:
                    self.incTypeField.text = 'Year'
                    self.incAmountField.text = str(incYears)

        self.categoryField = TextInput(multiline=False,size_hint_x=None,width=550)
        if category:
            self.categoryField.text = category
        self.constantField = CheckBox(size_hint_x=None,width=550)
        if constant:
            self.constantField.active = True
        self.cancelField = Button(text="Cancel",size_hint_x = None,width = 150)
        self.submitField = Button(text="Submit Bill",size_hint_x = None, width=500)

        self.add_widget(Label(text='Name',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.nameField)
        self.add_widget(Label(text='Amount',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.amountField)
        self.add_widget(Label(text='nextDue',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.nextDueField)
        self.add_widget(Label(text='incType',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.incTypeField)
        self.add_widget(Label(text='incAmount',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.incAmountField)
        self.add_widget(Label(text='category',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.categoryField)
        self.add_widget(Label(text='constant',halign='right',size_hint_x=None,width=200))
        self.add_widget(self.constantField)
        anchorLayout1 = AnchorLayout(anchor_x='right')
        anchorLayout1.add_widget(self.cancelField)
        self.add_widget(anchorLayout1)
        anchorLayout2 = AnchorLayout(anchor_x='center')
        anchorLayout2.add_widget(self.submitField)
        self.add_widget(anchorLayout2)

    def validateFields(self):
        result = True
        if len(self.nameField.text)==0:
            print("Cannot save bill: name field is blank")
            result = False
        if len(self.amountField.text)==0:
            print("Cannot save bill: amount field is blank")
            result = False
        if not self.nextDueField.getDateValue():
            print("Next Due Date is not valid.")
            result = False
        if self.incTypeField.text=='Select':
            print("Must select an Increment Type")
            result = False
        if self.incTypeField.text != 'None' and (len(self.incAmountField.text)== 0 or int(self.incAmountField.text)<=0):
            print("Not a valid increment value: please ensure it is a positive integer")
            result = False
        return result


## General Layout widgets

class TopBar(BoxLayout):
    title = "Default Title"
    titleLabel = ObjectProperty(None)
    amountInput = ObjectProperty(None)
    saveButton = ObjectProperty(None)
    addBillButton = ObjectProperty(None)

class SideBar(StackLayout):
    pass

class SelectedView(ScreenManager):
    pass


## The big widget that holds everything
class MainWindow(FloatLayout):
    topBar = ObjectProperty(None)
    sideBar = ObjectProperty(None)
    selectedView = ObjectProperty(None)