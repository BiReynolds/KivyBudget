import kivy 
kivy.require('2.1.0')
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty

class UpcomingBillsView(FloatLayout):
    dataBox = ObjectProperty()
    nameCol = ObjectProperty()
    amountCol = ObjectProperty()
    dueDateCol = ObjectProperty()
    categoryCol = ObjectProperty()

    def loadStuff(self):
        for i in range(30):
            self.nameCol.add_widget(Label(text='name'+str(i),color=(1,1,1,1),size_hint=(None,None)))
            self.amountCol.add_widget(Label(text='amount'+str(i),color=(1,1,1,1),size_hint=(None,None)))
            self.dueDateCol.add_widget(Label(text='dueDate'+str(i),color=(1,1,1,1),size_hint=(None,None)))
            self.categoryCol.add_widget(Label(text='category'+str(i),color=(1,1,1,1),size_hint=(None,None)))

            
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