from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import datetime as dt

from matplotlib import pyplot as plt
from mydb import *

# Import the necessary Matplotlib components
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


data = Database(db='ExpenseRecord.db')
count = 0
selected_rowid = 0
user_name_var = None  # Initialize to None
budget_var = None  # Initialize to None

def initialize_vars():
    global user_name_var, budget_var
    user_name_var = StringVar()
    budget_var = DoubleVar(value=20000.0)

def saveRecord():
    global data

    # Check if any input field is left empty
    if not user_name_var.get() or not item_name.get() or not amtvar.get() or not dopvar.get() or not budget_var.get():
        messagebox.showwarning('Empty Field', 'Please fill in all the input fields.')
        return

    total_balance_records = data.fetchRecord(query="SELECT SUM(item_price) FROM expense_record")

    if total_balance_records:
        total_balance = total_balance_records[0][0] or 0
    else:
        total_balance = 0

    category_name_value = user_name_var.get()
    item_name_value = item_name.get()
    
    # Check if the Item Price contains only numeric characters
    item_price_str = amtvar.get()
    try:
        item_price_value = float(item_price_str)
    except ValueError:
        messagebox.showwarning('Invalid Item Price', 'Enter a valid numeric Item Price.')
        return
    
    purchase_date_value = dopvar.get()
    budget_value = float(budget_var.get())

    if total_balance + item_price_value > budget_value:
        messagebox.showwarning('Insufficient Balance', 'You do not have sufficient balance to make this purchase.')
        return

    data.insertRecord(category_name_value, item_name_value, item_price_value, purchase_date_value, budget_value)

    clearEntries()
    refreshData()


def setDate():
    date = dt.datetime.now()
    dopvar.set(f'{date:%d %B %Y}')

def clearEntries():
    item_name.delete(0, 'end')
    item_amt.delete(0, 'end')
    transaction_date.delete(0, 'end')

def fetch_records():
    f = data.fetchRecord('select rowid, * from expense_record')
    global count
    for rec in f:
        tv.insert(parent='', index='0', iid=count, values=(rec[0], rec[2], rec[3], rec[4]))
        count += 1
    tv.after(400, refreshData)

def select_record(event):
    global selected_rowid
    selected_item = tv.selection()

    if selected_item:
        selected_rowid = tv.item(selected_item)['values'][0]
        selected_values = tv.item(selected_item)['values']

        try:
            namevar.set(selected_values[1])
            amtvar.set(selected_values[2])
            dopvar.set(str(selected_values[3]))
        except Exception as ep:
            pass

def update_record(budget_value):
    global selected_rowid

    selected = tv.focus()

    total_balance_records = data.fetchRecord(query="SELECT SUM(item_price) FROM expense_record")

    if total_balance_records:
        total_balance = total_balance_records[0][0] or 0
    else:
        total_balance = 0

    category_name_value = user_name_var.get()
    item_name_value = namevar.get()
    item_price_value = amtvar.get()
    purchase_date_value = dopvar.get()

    current_expense_price = data.fetchRecord(query=f"SELECT item_price FROM expense_record WHERE rowid={selected_rowid}")
    if current_expense_price:
        current_expense_price = current_expense_price[0][0]
    else:
        current_expense_price = 0

    if total_balance - current_expense_price + item_price_value > budget_value:
        messagebox.showwarning('Insufficient Balance', 'You do not have sufficient balance for this update.')
        return

    try:
        data.updateRecord(category_name_value, item_name_value, item_price_value, purchase_date_value, budget_value, selected_rowid)
        tv.item(selected, text="", values=(item_name_value, item_price_value, purchase_date_value, selected_rowid))
    except Exception as ep:
        messagebox.showerror('Error', ep)

    clearEntries()
    tv.after(400, refreshData)

def totalBalance():
    total_expenses_records = data.fetchRecord(query="SELECT SUM(item_price) FROM expense_record")

    if total_expenses_records and total_expenses_records[0][0] is not None:
        total_expenses = total_expenses_records[0][0]
        remaining_balance = budget_var.get() - total_expenses
        messagebox.showinfo('Current Balance:', f"Total Expense: {total_expenses}\nRemaining Balance: {remaining_balance}")
    else:
        messagebox.showinfo('Current Balance:', "No expenses recorded yet.")

def refreshData():
    if tv.winfo_exists():  # Check if the widget exists
        for item in tv.get_children():
            tv.delete(item)
        fetch_records()
    else:
        print("Tkinter widget does not exist.")


def deleteRow():
    global selected_rowid
    data.removeRecord(selected_rowid)
    refreshData()

def fetch_records_for_report():
    return data.fetchRecord("SELECT category_name, SUM(item_price), strftime('%Y-%m', COALESCE(purchase_date, '1900-01-01')) AS purchase_month FROM expense_record GROUP BY category_name, purchase_month")


def generate_report():
    # Fetch records from the database for the report
    records_for_report = fetch_records_for_report()

    if not records_for_report:
        messagebox.showinfo('No Records', 'There are no records in the database to generate a report.')
        return

    # Create a new Tkinter window for the report
    report_window = Toplevel(ws)
    report_window.title("Expense Report")

    # Create a Matplotlib figure for the bar graph
    fig, ax = plt.subplots(figsize=(7, 4))

    # Extract data for plotting
    data_dict = {}

    # Iterate over each record fetched for the report
    for record in records_for_report:
        category = record[0]
        month = record[2]
        expense = record[1]

        if category is not None and month != '1900-01' and expense is not None:
            if category not in data_dict:
                data_dict[category] = {'months': [], 'expenses': []}

            data_dict[category]['months'].append(month)
            data_dict[category]['expenses'].append(expense)

    # Convert months to strings
    for category_data in data_dict.values():
        category_data['months'] = [str(month) for month in category_data['months']]

    # Calculate total expense for setting y-axis limit
    total_expense = sum(expense for category_data in data_dict.values() for expense in category_data['expenses'])
    max_category_expense = max(expense for category_data in data_dict.values() for expense in category_data['expenses'])

    # Plotting the bar graph
    bar_width = 0.1
    num_categories = len(data_dict)

    for i, (category, category_data) in enumerate(data_dict.items()):
        x_positions = [j + i * bar_width for j in range(len(category_data['months']))]
        ax.bar(x_positions, category_data['expenses'], width=bar_width, label=category)
        
        # Display total expense on top of each bar
        for x, y in zip(x_positions, category_data['expenses']):
            ax.text(x + bar_width / 9, y + 0.01 * max_category_expense, f'{y:.2f}', ha='center', va='bottom', rotation=0, color='black')

    # Display total expenses at the top right
    total_expenses_str = f"Total Expenses: {total_expense}"
    ax.text(0.95, 0.95, total_expenses_str, transform=ax.transAxes, ha='right', va='top', bbox=dict(facecolor='white', alpha=0.5))

    ax.set_xlabel("Expenses")
    ax.set_ylabel("Total Expense")
    ax.set_title("Expense Report")
    ax.set_xticks([j + (num_categories - 1) * bar_width / 2 for j in range(len(category_data['months']))])
    ax.set_xticklabels(category_data['months'])
    ax.set_ylim(0, max_category_expense)
    ax.legend()
    ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

    # Embed Matplotlib figure into Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=report_window)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # Close the Matplotlib window when the Tkinter window is closed
    def on_closing():
        plt.close()
        report_window.destroy()

    report_window.protocol("WM_DELETE_WINDOW", on_closing)

    # Run the Tkinter event loop for the report window
    report_window.mainloop()


if __name__ == "__main__":
    # Ensure the script is run as the main module
    ws = Tk()
    ws.title('Daily Expenses')
    initialize_vars()

    f = ('Times new roman', 14)
    namevar = StringVar()
    amtvar = IntVar()
    dopvar = StringVar()

    f2 = Frame(ws)
    f2.pack()

    f1 = Frame(
        ws,
        padx=10,
        pady=10,
    )
    f1.pack(expand=True, fill=BOTH)

Label(f1, text='ITEM NAME', font=f).grid(row=0, column=0, sticky=W)
Label(f1, text='ITEM PRICE', font=f).grid(row=1, column=0, sticky=W)
Label(f1, text='PURCHASE DATE', font=f).grid(row=2, column=0, sticky=W)
Label(f1, text='CATEGORY', font=f).grid(row=4, column=0, sticky=W)
category_dropdown = ttk.Combobox(f1, font=f, textvariable=user_name_var)
category_dropdown['values'] = ('PERSONAL','STATIONARY', 'GROCERIES','MEDICATIONS','TRANSPORTATION','CLOTHING','OTHERS')  # Replace with your own categories
category_dropdown.grid(row=4, column=1, sticky=EW, padx=(10, 0))
Label(f1, text='BUDGET', font=f).grid(row=5, column=0, sticky=W)

item_name = Entry(f1, font=f, textvariable=namevar)
item_amt = Entry(f1, font=f, textvariable=amtvar)
transaction_date = Entry(f1, font=f, textvariable=dopvar)
category_name_entry = Entry(f1, font=f, textvariable=user_name_var)
budget_entry = Entry(f1, font=f, textvariable=budget_var)

item_name.grid(row=0, column=1, sticky=EW, padx=(10, 0))
item_amt.grid(row=1, column=1, sticky=EW, padx=(10, 0))
transaction_date.grid(row=2, column=1, sticky=EW, padx=(10, 0))
budget_entry.grid(row=5, column=1, sticky=EW, padx=(10, 0))

cur_date = Button(
    f1, 
    text='Current Date', 
    font=f, 
    bg='#04C4D9', 
    command=setDate,
    width=15
)

submit_btn = Button(
    f1, 
    text='Save Record', 
    font=f, 
    command=saveRecord, 
    bg='#04C4D9', 
)

clr_btn = Button(
    f1, 
    text='Clear Entry', 
    font=f, 
    command=clearEntries, 
    bg='#04C4D9', 
)

quit_btn = Button(
    f1, 
    text='Exit', 
    font=f, 
    command=lambda:ws.destroy(), 
    bg='#04C4D9', 
)

total_bal = Button(
    f1,
    text='Total Balance',
    font=f,
    bg='#04C4D9',
    command=totalBalance
)

update_btn = Button(
    f1, 
    text='Update',
    bg='#04C4D9',
    command=lambda: update_record(budget_var.get()),
    font=f
)

del_btn = Button(
    f1, 
    text='Delete',
    bg='#04C4D9',
    command=deleteRow,
    font=f
)

# Report button
rpt_btn = Button(
        f1, 
        text='Generate Report',
        bg='#04C4D9',
        font=f,
        command=generate_report  # Link the button to the generateReport function
    )

cur_date.grid(row=3, column=1, sticky=EW, padx=(10, 0))
submit_btn.grid(row=0, column=2, sticky=EW, padx=(10, 0))
clr_btn.grid(row=1, column=2, sticky=EW, padx=(10, 0))
quit_btn.grid(row=2, column=2, sticky=EW, padx=(10, 0))
total_bal.grid(row=0, column=3, sticky=EW, padx=(10, 0))
update_btn.grid(row=1, column=3, sticky=EW, padx=(10, 0))
del_btn.grid(row=2, column=3, sticky=EW, padx=(10, 0))
rpt_btn.grid(row=3, column=3, sticky=EW, padx=(10, 0))

tv = ttk.Treeview(f2, columns=(1, 2, 3, 4), show='headings', height=8)
tv.pack(side="left")

tv.column(1, anchor=CENTER, stretch=NO, width=70)
tv.column(2, anchor=CENTER)
tv.column(3, anchor=CENTER)
tv.column(4, anchor=CENTER)

tv.heading(1, text="Serial no")
tv.heading(2, text="Item Name", )
tv.heading(3, text="Item Price")
tv.heading(4, text="Purchase Date")

tv.bind("<<TreeviewSelect>>", select_record)

style = ttk.Style()
style.theme_use("default")
style.map("Treeview")

scrollbar = Scrollbar(f2, orient='vertical')
scrollbar.configure(command=tv.yview)
scrollbar.pack(side="right", fill="y")
tv.config(yscrollcommand=scrollbar.set)

fetch_records()

ws.mainloop()
