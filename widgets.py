import kivy 
import re
kivy.require('2.1.0')
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty

from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome
from models import IncType,BillType,Bill

## Special widgets

class MoneyInput(TextInput):
    pat = re.compile('[^0-9]')

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

## General Layout widgets

class TopBar(BoxLayout):
    title = "Default Title"
    titleLabel = ObjectProperty(None)
    amountInput = ObjectProperty(None)
    saveButton = ObjectProperty(None)

class SideBar(StackLayout):
    pass

class SelectedView(FloatLayout):
    pass


## The big widget that holds everything
class MainWindow(FloatLayout):
    topBar = ObjectProperty(None)
    sideBar = ObjectProperty(None)
    selectedView = ObjectProperty(None)