import sqlite3
from DBManagement import db_setup, load_test_data,QueryBillType,QueryBillsAndIncome
from models import IncType,BillType,Bill

db_setup()
load_test_data()