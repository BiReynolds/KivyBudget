from enum import Enum
from datetime import date,datetime,timedelta

class IncType(Enum):
    DAY = 0
    MONTH = 1
    YEAR = 2

class BillType():
    def __init__(self,name,amount,nextDue,incType=IncType.MONTH.value,incDays=None,incMonths=1,incYears=None,category=0,constant=1,id=None):
        self.id = id
        self.name = name
        self.amount = amount
        self.nextDue = nextDue
        self.incType = incType
        self.incDays = incDays
        self.incMonths = incMonths
        self.incYears = incYears
        self.category = category
        self.constant = constant

    def makeBillInstances(self,numYears = 10):
        result = []

        currDate = date.fromisoformat(self.nextDue)
        while currDate < (datetime.today() + numYears*timedelta(days=365)).date():
            ## Append the new Bill object
            result.append(Bill(self.id,self.name,self.amount,currDate.isoformat(),self.category,self.constant))
            ## Increment the date based on the incType and increment value
            match self.incType:
                case IncType.YEAR.value:
                    try: currDate = currDate.replace(year = currDate.year + self.incYears)
                    except ValueError as err:
                        ## Only case where a date exists one year but not the next is a leap year... I think? 
                        if currDate.month == 2 and currDate.day == 29:
                            currDate = date(currDate.year + self.incYears,2,28)
                        else:
                            print("Error while getting next year\n","Date Given: "+currDate.isoformat()+"\n","Error received: "+err)
                case IncType.MONTH.value:
                    try: currDate = currDate.replace(month = currDate.month + self.incMonths)
                    except ValueError as err:
                        ## If date exists one month but does not exist after adding 1 to the month, either month = 12 or day is close to EOM.  Lazy solution, replace day with 28 to ensure we're always good
                        if currDate.month + self.incMonths > 12:
                            currDate = currDate.replace(month = currDate.month + self.incMonths - 12, year = currDate.year + 1, day = min(28,currDate.day))
                        elif currDate.day > 28:
                            currDate = currDate.replace(month = currDate.month + self.incMonths,day = 28)
                        else:
                            print("Error while getting next month\n","Date Given: "+currDate.isoformat()+"\n","Error received:",err)
                case IncType.DAY.value:
                    currDate = currDate + timedelta(days = self.incDays)
        return result


    
class Bill():
    def __init__(self,billTypeId,name,amount,dueDate,category=0,constant=1,id=None):
        self.id = id
        self.billTypeId = billTypeId
        self.name = name
        self.amount = amount
        self.dueDate = dueDate
        self.category = category
        self.constant = constant
