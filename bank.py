import mysql.connector
from getpass import getpass
import sys
import bcrypt
from termcolor import cprint


class MysqlDatabaseManager:
    def __init__(self,hostname,username,password,database):
        self.hostname= hostname
        self.username= username
        self.password= password
        self.database= database
        self.connection = None
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host = self.hostname,
                user = self.username,
                password= self.password,
                database = self.database
            
            )
            if self.connection.is_connected():
                print('Connected to mysql database')
        except mysql.connector.Error as err:
            print(f'The Error is {err}')

    def excute_query(self,query,data=None):
        try:
            cursor = self.connection.cursor()
            if data:
                cursor.execute(query,data)
            else:
                cursor.execute(query)
            self.connection.commit()
            cprint('Query success!',color='green',on_color=None)
        except mysql.connector.Error as err:
            cprint(f'Error {err}',color='red',on_color=None)
            return cursor
        
    def close(self):
        if self.connection:
            self.connection.close()
            print('Connection Closed!')

class Bank:
    def __init__(self):
        self.user_info = {}
        self.db = MysqlDatabaseManager(
            hostname='localhost',
            username='root',
            password='YOUR PASSWORD',
            database='YOUR DATABASE'
        )
        self.db.connect()

    def create_account(self):
        full_name = input('Your full name? ')
        email= input('Your Email Account? ')
        username= input('Username? ')
        passwd = getpass('type  Password? ')
        passwd1 = getpass('Type the password one more time? ')
        hashed_passwd= bcrypt.hashpw(passwd.encode('utf-8'),bcrypt.gensalt())
        if passwd == passwd1:
            cprint('Account Created!',color='green',on_color=None)
            self.user_info = {'Full name':full_name,'Email':email,'Username':username,'Password':hashed_passwd}
            
            q1= '''INSERT INTO user (name,email,username,password,balance) VALUES (%s,%s,%s,%s,%s)
                '''
            data= (
                self.user_info['Full name'],
                self.user_info['Email'],
                self.user_info['Username'],
                self.user_info['Password'],
                0
            )
            try:
                query= self.db.excute_query(q1,data)
                self.db.close()
            except mysql.connector.Error as err:
                cprint(f'Erorr:{err}',color='red',on_color=None)

        else:
            cprint("Passwords did'nt match!!",color='white',on_color='on_red')

    def login(self):
        username= input('Enter Your Username? ')
        passwd = getpass('Enter your password? ')
        
        q= ' SELECT password FROM user WHERE username = %s'
        user = (username,)
        query = self.db.excute_query(q,user)
        result = query.fetchone()
        if result:
            hashed_passwd = result[0]
            if bcrypt.checkpw(passwd.encode('utf-8'),hashed_passwd.encode('utf-8')):
                cprint('User Found!','green','on_green')
                self.username = username
                self.password = hashed_passwd
                self.choose_operation()
            else:
                cprint('Password is not Correct!',on_color='on_red')
        else:
            cprint('Username is not correct!',on_color='on_red')
        self.db.close()
    
    def choose_operation(self):
        print('OPerations:\n1-Deposit\n2-withdraw\n3-Show balance\n4-Transaction History\n5-Exit')
        operation= int(input())
        if operation == 1:
            self.deposit()
        elif operation == 2:
            self.withdraw()
        elif operation == 3:
            self.show_balance()
        elif operation == 4:
            self.show_history()
        elif operation == 5:
            sys.exit()
        else:
            print('Unknown OPeration!')

    def deposit(self):
        mount = int(input('Enter the mount you want to deposit: '))
        # Retrieve the current user's balance 
        q1 = 'SELECT balance FROM user WHERE username=%s AND password=%s'
        if hasattr(self,'username') and hasattr(self,'password'):
            username=self.username
            password =self.password
            user = (username,password)
            query = self.db.excute_query(q1,user)
            result = query.fetchone()
            if result:
                balance = result[0]
                # Update The user's balance after adding the deposit money 
                q2 ='UPDATE user SET balance=%s WHERE username=%s AND password=%s'  
                updated_balance = mount + balance
                data = (updated_balance,username,password)
                self.db.excute_query(q2,data)
                query = self.db.excute_query(q1,user)
                result = query.fetchone()
                balance = result[0]
                cprint(f'the money Deposited successfully! Your balance now is {balance}',color='green',on_color=None)
                # Retrieving the user's id to store it in transaction table..
                q3 = 'SELECT id FROM user WHERE username=%s AND password=%s'
                query= self.db.excute_query(q3,user)
                result = query.fetchone()
                result = result[0]
                # Add deposit mount in transations table 
                q4 = 'INSERT INTO transactions (deposit,user_id) VALUES (%s,%s) '
                trans_data = (mount,result)
                self.db.excute_query(q4,trans_data)
            else:
                print('Faild to retrieve the balance..')
            

    def withdraw(self):
        mount = int(input('Enter the mount you want to withdraw: '))
        ## Retrieve the current user's balance 
        q1 = 'SELECT balance FROM user WHERE username=%s AND password=%s '
        if hasattr(self,'username') and hasattr(self,'password'):
            username=self.username
            password =self.password
            user=(username,password)
            query = self.db.excute_query(q1,user)
            result = query.fetchone()
            if result:
                balance = result[0]
            else:
                cprint('Faild to retrieve the balance..',color='red')
            # Update the User's balance after withdraw transaction
            q2 = 'UPDATE user SET balance=%s WHERE username=%s AND password=%s'
            updated_balance = balance-mount
            if updated_balance < 0:
                print('No enough balance..')
            else:
                data = (updated_balance,username,password)
                self.db.excute_query(q2,data)
                # Updating the balance after withdraw..
                query = self.db.excute_query(q1,user)
                result = query.fetchone()
                balance = result[0]
                cprint(f'the transaction finished successfully, your balance now  {balance}.',color='green')
                # Pick the user's id to store the withdraw in transactions table 
                q3 = 'SELECT id FROM user WHERE username=%s AND password=%s'
                id_q = self.db.excute_query(q3,user)
                id_result = id_q.fetchone()
                id_result = id_result[0]
                # Store the withdraw in transation table
                q4 = 'INSERT INTO transactions (withdraw, user_id) VALUES (%s,%s)'
                trans_data = (mount,id_result)
                self.db.excute_query(q4,trans_data)
             

    def show_balance(self):    
        balance_q = 'SELECT balance FROM user WHERE username= %s AND password= %s'
        if hasattr(self,'username') and hasattr(self,'password'):
            username = self.username
            password = self.password
            user = (username,password)
            query =  self.db.excute_query(balance_q, user)
            result= query.fetchone()
            if result:
                balance = result[0]
                cprint(f"Your Balance {balance}",color='green',on_color=None) 

            else:  
                cprint('Faild to retrieve Your balance',color='red',on_color=None)    
        else:
            print('You Should login First!!')

    def show_history(self):
        print('Transaction History')
        # Select user's Id from user Table 
        q1 = 'SELECT id FROM user WHERE username=%s AND password=%s'
        if hasattr(self,'username') and hasattr(self,'password'):
            username = self.username
            password = self.password
            user = (username,password)
            id_q = self.db.excute_query(q1,user)
            result = id_q.fetchone()
            result =result[0]
            q2= 'SELECT deposit,withdraw FROM transactions WHERE user_id=%s'
            user_id = (result,)
            extracted_data= self.db.excute_query(q2,user_id)
            for d , w in extracted_data:
                if w == None:
                    print(f'Deposit +{d}')
                elif d == None:
                    print(f'Withdraw -{w}')
             
        else:
            cprint('Faild to retrieve the data..',color='red')
        

def main():

    bank = Bank()
    print("Welcome to The Fake Bank ")
    inp = int(input('Choose number of operation\n1-Register new user\n2-Login\n'))
    if inp == 1:
        bank.create_account()
    elif inp == 2:
        print('Login')
        bank.login()




# Creating the tables..
    q1 = '''
        CREATE TABLE IF NOT EXISTS user(
            id INT AUTO_INCREMENT PRIMARY KEY ,
            name VARCHAR(155),
            email VARCHAR(155) NOT NULL,
            username VARCHAR(55) NOT NULL,
            password VARCHAR(155) NOT NULL,
            balance INT 
        );
    '''
    q2= '''
        CREATE TABLE IF NOT EXISTS transactions(
            trans_id INT AUTO_INCREMENT PRIMARY KEY,
            deposit INT,
            withdraw INT,
            user_id INT,
            FOREIGN KEY (user_id) REFERENCES  user(id)
        );

    '''
    q3= '''ALTER TABLE user ALTER balance SET DEFAULT 0;'''
    # db.excute_query(q3)
    # bank.excute_query(q2)
    #----------------------------

if __name__ == '__main__':
   main()
