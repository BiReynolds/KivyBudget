import kivy 
kivy.require('2.1.0')
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty

from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome
from models import IncType,BillType,Bill

class UpcomingBillsView(FloatLayout):
    dataBox = ObjectProperty()
    nameCol = ObjectProperty()
    amountCol = ObjectProperty()
    dueDateCol = ObjectProperty()
    rollBalCol = ObjectProperty()

    def loadStuff(self):
        data = QueryBillsAndIncome.getTopNByDueDate()
        rollBal = 1000
        for bill in data:
            rollBal += bill.amount
            self.nameCol.add_widget(Label(text=bill.name,color=(1,1,1,1),size_hint=(None,None)))
            self.amountCol.add_widget(Label(text=str(bill.amount),color=(1,1,1,1),size_hint=(None,None)))
            self.dueDateCol.add_widget(Label(text=str(bill.dueDate),color=(1,1,1,1),size_hint=(None,None)))
            self.rollBalCol.add_widget(Label(text=str(rollBal),color=(1,1,1,1),size_hint=(None,None)))

            
class TopBar(StackLayout):
    title = "Default Title"
    titleLabel = ObjectProperty(None)

class SideBar(StackLayout):
    pass

class SelectedView(FloatLayout):
    currentView = ObjectProperty()

class MainWindow(FloatLayout):
    topBar = ObjectProperty(None)
    sideBar = ObjectProperty(None)
    selectedView = ObjectProperty(None)