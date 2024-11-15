import sqlite3
from models import IncType,BillType,Bill


def db_setup():
    ## Initiate a connection to db
    con = sqlite3.connect("KivyBudget.db")
    cur = con.cursor()

    ## Create UserInfo table.  This will store miscellaneous info about the user.  For now, we only allow a single user 
    ## so this db will act mostly like a dictionary.  There are only two columns: name (the name of the attribute) and value
    ## (the value of said attribute).  Later we will likely allow more than one user per instance of this application, and
    ## so we will add a more robust solution 
    cur.execute("CREATE TABLE if not exists UserInfo(id INTEGER PRIMARY KEY, name TEXT UNIQUE, value TEXT)")
    ## Below, we insert a default value for any properties we've established thus far 
    try:
        cur.execute("INSERT INTO UserInfo (name,value) VALUES ('currentBalance','0.00')")
    except:
        print("Couldn't insert userinfo data")

    ## Create Category table
    cur.execute("CREATE TABLE if not exists Category(id INTEGER PRIMARY KEY, name TEXT UNIQUE)")

    ## Create BillType table and indices for that table
    cur.execute("CREATE TABLE if not exists BillType(id INTEGER PRIMARY KEY, name TEXT UNIQUE, amount REAL, nextDue TEXT, incType INTEGER, incDays INTEGER, incMonths INTEGER, incYears INTEGER, category INTEGER, constant INTEGER, FOREIGN KEY(category) REFERENCES Category(id))")
    cur.execute("CREATE INDEX if not exists bill_type_nextDue_idx ON BillType (nextDue)")
    cur.execute("CREATE INDEX if not exists bill_type_category_idx ON BillType (category)")

    ## Create BillsAndIncome table and indices for that table
    cur.execute("CREATE TABLE if not exists BillsAndIncome(id INTEGER PRIMARY KEY,billTypeId INTEGER, name TEXT, amount INTEGER, dueDate TEXT, category INTEGER, constant INTEGER, FOREIGN KEY(billTypeId) REFERENCES BillType(id))")
    cur.execute("CREATE INDEX if not exists bills_and_income_dueDate_idx ON BillsAndIncome (dueDate)")
    cur.execute("CREATE INDEX if not exists bills_and_income_category_idx ON BillsAndIncome (category)")
    cur.execute("CREATE INDEX if not exists bills_and_income_billTypeId_idx ON BillsAndIncome (billTypeId)")

    ## Commit changes and close connection
    cur.close()
    con.commit()
    con.close()

def load_test_data():
    con = sqlite3.connect("KivyBudget.db")
    cur = con.cursor()
    ## Check if test data already exists
    cur.execute("SELECT * FROM Category WHERE name = 'test'")
    if (cur.fetchone()):
        cur.close()
        con.close()
        return
    ## Add the test data
    test_data = [
        BillType('Yearly Bill',-1000,'2024-11-10',IncType.YEAR.value,None,None,1,1,1,id=1),
        BillType('Monthly Bill',-500,'2024-11-15',IncType.MONTH.value,None,1,None,1,1,id=2),
        BillType('Weekly Bill',-100,'2024-11-09',IncType.DAY.value,7,None,None,1,1,id=3),
        BillType('Biweekly Income',1000,'2024-11-10',IncType.DAY.value,14,None,None,1,0,id=4)
    ]
    cur.execute("INSERT INTO Category (name) VALUES ('test')")
    cur.close()
    con.commit()
    con.close()
    QueryBillType.insertmany(test_data)
    for point in test_data:
        instances = point.makeBillInstances()
        QueryBillsAndIncome.mergeBills(instances)

class QueryBillType():
    def byId(id):
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM BillType WHERE id = "+str(id))
        raw_data = cur.fetchone()
        res = BillType(raw_data[1],raw_data[2],raw_data[3],raw_data[4],raw_data[5],raw_data[6],raw_data[7],raw_data[8],raw_data[9],raw_data[0])
        cur.close()
        con.close()
        return res
    
    def insertOne(billTypeObj):
        insertString = f"INSERT INTO BillType (name,amount,nextDue,incType,incDays,incMonths,incYears,category,constant) VALUES ('{billTypeObj.name}',{billTypeObj.amount},'{billTypeObj.nextDue}',{billTypeObj.incType},{billTypeObj.incDays},{billTypeObj.incMonths},{billTypeObj.incYears},{billTypeObj.category},{billTypeObj.constant})"
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        try:
            cur.execute(insertString)
            cur.execute("SELECT last_insert_rowid()")
            lastIndex = cur.fetchone()[0]
        except sqlite3.Error as er:
            print(f"Could not insert {billTypeObj.name} into table BillType.  Error received: ",er)
            lastIndex = -1
        cur.close()
        con.commit()
        con.close()
        print(lastIndex)
        return lastIndex

    def insertmany(billTypeObjs):
        insertString = "INSERT INTO BillType (name,amount,nextDue,incType,incDays,incMonths,incYears,category,constant) VALUES (?,?,?,?,?,?,?,?,?)"
        insertData = []
        for bill in billTypeObjs:
            insertData.append((bill.name,bill.amount,bill.nextDue,bill.incType,bill.incDays,bill.incMonths,bill.incYears,bill.category,bill.constant))
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute('begin')
        try:
            cur.executemany(insertString,insertData)
        except sqlite3.IntegrityError as err:
            cur.execute('rollback')
            print("insertMany could not be completed due to database error: ",err)
        cur.close()
        con.commit()
        con.close()

    def simpleEdit(billTypeObj):
        sqlString = f"UPDATE BillType SET name='{billTypeObj.name}',amount={billTypeObj.amount},category={billTypeObj.category},constant={billTypeObj.constant} WHERE id={billTypeObj.id}"
        con=sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute(sqlString)
        cur.close()
        con.commit()
        con.close()

class QueryBillsAndIncome():
    def byId(id):
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM BillsAndIncome WHERE id = "+str(id))
        row = cur.fetchone()
        res = Bill(row[1],row[2],row[3],row[4],row[5],row[6],row[0])
        cur.close()
        con.close()
        return res

    def getTopNByDueDate(N=100):
        sqlString = f"SELECT * FROM BillsAndIncome ORDER BY date(dueDate) LIMIT {N}"
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute(sqlString)
        raw_data = cur.fetchall()
        cur.close()
        con.close()
        res=[]
        for row in raw_data:
            res.append(Bill(row[1],row[2],row[3],row[4],row[5],row[6],row[0]))
        return res

    def byBillTypeIdAndDueDates(billTypeId,dateString):
        queryString = f"SELECT dueDate FROM BillsAndIncome WHERE billTypeId = {billTypeId} AND dueDate in ('{dateString[0]}'"
        for dueDate in dateString[1:]:
            queryString += ",'"+dueDate+"'"
        queryString += ")"
        try:
            con = sqlite3.connect("KivyBudget.db")
            cur = con.cursor()
            cur.execute(queryString)
            result = cur.fetchall()
        except:
            print(queryString)
            result = 0
        cur.close()
        con.close()
        return result
    
    def insertOne(billObj):
        insertString = f"INSERT INTO BillsAndIncome (billTypeId, name, amount, dueDate, category, constant) VALUES ({billObj.billTypeId},'{billObj.name}',{billObj.amount},'{billObj.dueDate}',{billObj.category},{billObj.constant})"
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        try:
            cur.execute(insertString)
        except sqlite3.Error as er:
            print(f"Could not insert {billObj.name} into table BillsAndIncome.  Error received: ",er)
        cur.close()
        con.commit()
        con.close()
        return 

    def mergeBills(billObjs):
        billDates = [bill.dueDate for bill in billObjs]
        existingBillDates = [row[0] for row in QueryBillsAndIncome.byBillTypeIdAndDueDates(billObjs[0].billTypeId,billDates)]
        newBills = []
        for i,dueDate in enumerate(billDates):
            if dueDate in existingBillDates:
                continue
            else:
                newBill = billObjs[i]
                newBills.append((newBill.billTypeId,newBill.name,newBill.amount,newBill.dueDate,newBill.category,newBill.constant))
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute('begin')
        try:
            cur.executemany("INSERT INTO BillsAndIncome (billTypeId, name, amount, dueDate, category, constant) VALUES (?,?,?,?,?,?)",newBills)
        except sqlite3.IntegrityError as err:
            cur.execute('rollback')
        cur.close()
        con.commit()
        con.close()

    def deleteByIds(ids):
        setOfIds = "("+",".join(ids)+")"
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute("DELETE FROM BillsAndIncome WHERE id in "+setOfIds)
        cur.close()
        con.commit()
        con.close()

    def simpleEdit(billObj):
        sqlString=f"UPDATE BillsAndIncome SET name='{billObj.name}',amount={billObj.amount},category={billObj.category},constant={billObj.constant} WHERE id = {billObj.id}"
        con=sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute(sqlString)
        cur.close()
        con.commit()
        con.close()

    def simpleEditByType(billObj):
        sqlString=f"UPDATE BillsAndIncome SET name='{billObj.name}',amount={billObj.amount},category={billObj.category},constant={billObj.constant} WHERE (billTypeId={billObj.billTypeId} AND dueDate>='{billObj.dueDate}')"
        con=sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute(sqlString)
        cur.close()
        con.commit()
        con.close()

## Likely a temporary class which will be replaced when we add better user support
class GetUserInfo():
    def getCurrentBalance():
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute("SELECT value FROM UserInfo WHERE name = 'currentBalance'")
        currBal = float(cur.fetchone()[0])
        return currBal
    
    def setCurrentBalance(newCurrentBalance):
        con = sqlite3.connect("KivyBudget.db")
        cur = con.cursor()
        cur.execute(f"UPDATE UserInfo SET value='{newCurrentBalance}' WHERE name='currentBalance'")
        cur.close()
        con.commit()
        con.close()