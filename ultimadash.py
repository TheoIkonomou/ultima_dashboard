import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

df = pd.read_csv('stocks.csv')
df2 = pd.read_csv('bonds.csv')
pd.set_option("display.max_rows", None, "display.max_columns", None)

# Formating Dashboard
st.set_page_config(page_title="Ultima",
                   page_icon=":chart_with_upward_trend:",
                   layout="wide")

# Formating stock file
df[['Date', 'Price']] = df['Trade Date;Close'].str.split(';', 1, expand=True)
df.drop("Trade Date;Close", axis=1, inplace=True)
df = df.astype({'Price': float})
df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
df['Year'] = pd.to_datetime(df['Date']).dt.year
df['Month'] = pd.to_datetime(df['Date']).dt.month
df.drop('Date', axis=1, inplace=True)

stock_prices = pd.DataFrame(df.groupby(by=["Year", 'Month']).mean().round(2).reset_index())

# Formating Bonds file
df2[['Date', 'Price']] = df2['Trade Date;Close'].str.split(';', 1, expand=True)
df2.drop("Trade Date;Close", axis=1, inplace=True)
df2 = df2.astype({'Price': float})
df2['Date'] = pd.to_datetime(df2['Date'], format="%d/%m/%Y")
df2['Year'] = pd.to_datetime(df2['Date']).dt.year
df2['Month'] = pd.to_datetime(df2['Date']).dt.month
df2.drop('Date', axis=1, inplace=True)

bond_prices = pd.DataFrame(df2.groupby(by=["Year", 'Month']).mean().round(2).reset_index())

# List with months and years
year_months = stock_prices[["Year", "Month"]]
year_months = pd.DataFrame(stock_prices[["Year", "Month"]])
# Time selection list
date_selection = year_months["Month"].astype(str) + "/" + year_months["Year"].astype(str)
date_selection = date_selection.tolist()


# Returns Portfolio Composition
def port_comp(composition):
    stock = composition.split("|")[0]
    bond = composition.split("|")[1]
    return int(stock) / 100, int(bond) / 100


# Composition of Portfolio Slidebar
comp = st.sidebar.select_slider("Κατανομή Επενδύσεων(Μετοχικό|Ομολογιακό):",
                                options=["0|100", "10|90", "20|80", "30|70", "40|60",
                                         "50|50", "60|40", "70|30", "80|20", "90|10", "100|0"])

# Weighted Price
stock_weight, bond_weight = port_comp(comp)
weighted_prices = (stock_prices["Price"] * stock_weight + bond_prices["Price"] * bond_weight).round(2)
weighted_df = pd.concat([year_months['Year'], year_months['Month'], weighted_prices], axis=1,
                        keys=['Year', 'Month', 'Adj Price'])
weighted_df["%Ch"] = 1 + weighted_df["Adj Price"].pct_change().round(4)
weighted_df['%Ch'] = weighted_df['%Ch'].fillna(0)


# Returns list with the months payments occured
def payments(start_date, payment_method):
    starting_point = date_selection.index(start_date)
    payment_list = []
    payment_list = date_selection[starting_point::int(payment_method)]
    for x in range(len(payment_list)):
        payment_list[x] = payment_list[x].split("/")
    payment_list = pd.DataFrame(payment_list, columns=['Month', 'Year'])
    payment_list["Month"] = pd.to_numeric(payment_list["Month"])
    payment_list["Year"] = pd.to_numeric(payment_list["Year"])
    return payment_list


# Insurance Cost per Month
def ins_cost(payment):
    annual = payment * 12
    if annual < 1000:
        cost = 43 / 12
    if annual < 3000 & annual >= 1000:
        cost = 65 / 12
    else:
        cost = 95 / 12
    return round(cost, 2)


# Monthly payment slider
monthly_amount = st.sidebar.slider("Μηνιαίο Ασφάλιστρο:", min_value=60, max_value=1000, step=10)
total_monthly = monthly_amount



# Starting Date and Payment Method sliders
starting_date = st.sidebar.select_slider("Μήνας Έναρξης:", options=date_selection)
payment_method = st.sidebar.select_slider("Τρόπος Πληρωμής:", options=["Μήνα", "Τρίμηνο", "Εξάμηνο", "Ετήσιο"])
if payment_method == "Μήνα":
    payment_method = 1
elif payment_method == "Τρίμηνο":
    payment_method = 3
    monthly_amount *= 3
elif payment_method == "Εξάμηνο":
    payment_method = 6
    monthly_amount *= 6
else:
    payment_method = 12
    monthly_amount *= 12


#Calculation of Portfolio value and Total paid amount
when_payments_occured = payments(starting_date, payment_method)
Portfolio = []
Total_paid = []
for f in range(len(weighted_df)):
    Portfolio.append(0)
    Total_paid.append(0)
previous = 0
security = 0
for i in range(len(weighted_df)):
    if i != 0:
        previous = i - 1
    Total_paid[i] = Total_paid[previous]
    if Portfolio[previous] != 0:
        Portfolio[i] = Portfolio[previous] * (weighted_df["%Ch"][i] - 0.001541) - ins_cost(monthly_amount)
    for x in range(len(when_payments_occured)):
        if when_payments_occured["Year"][x] == weighted_df["Year"][i] and \
                when_payments_occured["Month"][x] == weighted_df["Month"][i]:
            if x < (12 / payment_method):
                Total_paid[i] = monthly_amount * 0.5 + Total_paid[previous]
                Portfolio[i] = monthly_amount * 0.5 + \
                               Portfolio[previous] * (weighted_df["%Ch"][i] - 0.001541) - ins_cost(monthly_amount)
                security += monthly_amount * 0.5
            elif x < (24 / payment_method):
                Total_paid[i] = monthly_amount * 0.75 + Total_paid[previous]
                Portfolio[i] = monthly_amount * 0.75 + \
                               Portfolio[previous] * (weighted_df["%Ch"][i] - 0.001541) - ins_cost(monthly_amount)
                security += monthly_amount * 0.25
            else:
                Total_paid[i] = monthly_amount + Total_paid[previous]
                Portfolio[i] = monthly_amount + \
                               Portfolio[previous] * (weighted_df["%Ch"][i] - 0.001541) - ins_cost(monthly_amount)



# Formating final df for the chart

weighted_df["Portfolio"] = Portfolio
weighted_df["Total Paid"] = Total_paid
weighted_df["Portfolio"] = weighted_df["Portfolio"].round(1)
weighted_df["Total Paid"] = weighted_df["Total Paid"].round(1)

starting_date_index = date_selection.index(str(starting_date))
date_selection = pd.Series(date_selection)
line_df = pd.DataFrame()
line_df["Date"] = date_selection.loc[starting_date_index - 1:]
line_df["Portfolio"] = weighted_df.loc[starting_date_index - 1:, "Portfolio"]
line_df["Total Paid"] = weighted_df.loc[starting_date_index - 1:, "Total Paid"]


#KPI's
total_portfolio = weighted_df["Portfolio"].iloc[-1] + security
total_amount = weighted_df["Total Paid"].iloc[-1] + security
profit = round(((total_portfolio / total_amount) - 1) * 100, 2)
st.title("Ultima")
st.markdown("##")
left_c, midle_c, right_c= st.columns(3)
with left_c:
    st.subheader("Αξία Χαρτοφυλακίου:")
    st.subheader(f"{total_portfolio}€")
with midle_c:
    st.subheader('Συνολικές Καταβολές:')
    st.subheader(f"{total_amount}€")
with right_c:
    st.subheader("Συνολική Απόδοση:")
    st.subheader(f"{profit}%")
st.markdown("---")

#Main Chart
char_portfolio = px.line(line_df, y=[line_df["Total Paid"], line_df["Portfolio"]], x=line_df["Date"],
                         labels={"Total Paid": "Καταβολές",
                                 "Portfolio": "Χαρτοφυλάκιο",
                                 "Date": " ",
                                 "value": " "},
                         width=900,
                         height=500
                         )

char_portfolio.update_layout(plot_bgcolor="rgb(0,0,0,0)",
                             xaxis=(dict(showgrid=False)),
                             yaxis=(dict(showgrid=False)),
                             showlegend=False,
                             )
st.plotly_chart(char_portfolio, use_conteiner_width=False)

hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)
