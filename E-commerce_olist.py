import pandas as pd
import matplotlib.pyplot as plt, seaborn as sns
import plotly.express as px

path = '...path'
a = path + 'olist_orders_dataset.csv'
b = path + 'olist_order_items_dataset.csv'
c = path + 'olist_customers_dataset.csv'
d = path + 'olist_products_dataset.csv'


orders = pd.read_csv(a)
orders_items = pd.read_csv(b)
customers = pd.read_csv(c)
products = pd.read_csv(d)

""" EDA """

df_total = pd.merge(orders, orders_items, how='inner', on='order_id')
print(df_total.head())
print(df_total.info())

df_total['order_purchase_timestamp'] = pd.to_datetime(df_total['order_purchase_timestamp'])

df_2018 = df_total[(df_total['order_purchase_timestamp'].dt.year == 2018)
                   & (df_total['order_status'] == 'delivered')].copy()

df_customer = pd.merge(customers[['customer_id', 'customer_state']], df_2018, on='customer_id', how='inner')

df_customer = df_customer.groupby('order_id').agg({
    'price': 'sum',
    'freight_value': 'sum',
    'customer_state': 'first',
    'order_purchase_timestamp': 'first',
    'order_delivered_customer_date': 'first',
    'order_status': 'first',
    'order_estimated_delivery_date': 'first'
}).reset_index()

df_customer['GMV'] = df_customer['price'] + df_customer['freight_value']

# Total GMV, sales and ticket info
total_GMV = df_customer['GMV'].sum()
total_sales = df_2018['order_id'].nunique()
print(f'GMV: R${total_GMV:.2f}'
      f'\nTotal Sales: {total_sales}'
      f'\nMedium Ticket: R${(total_GMV / total_sales):.2f}')

# GMV by state (lambda is used to transform all values in %)
per_state = df_customer.groupby('customer_state')['GMV'].sum().apply(lambda x: (x / total_GMV) * 100)
    # Grouping the states with less than 0% contribution
per_state.index = [state if val > 1 else 'Others' for state, val in per_state.items()]
    # Putting 'Others' in the end of the list
per_state = per_state.groupby(level=0).sum().sort_values(ascending=False)
if 'Others' in per_state.index:
    value_others = per_state.pop('Others')
per_state['Others'] = value_others
print(per_state)

# São Paulo (SP) is the dominant state, with almost 40% of the total 2018 GMV coming from there.

# Checking freight prices against GMV contribution
    # recreating perstate but maintaining all the states this time to calculate freight
per_state2 = df_customer.groupby('customer_state')['GMV'].sum().apply(lambda x: (x / total_GMV) * 100)

total_freight = df_customer['freight_value'].sum()
freight_value = (df_customer.groupby('customer_state')['freight_value']
                 .sum().apply(lambda x: (x / total_freight) * 100))

df_freight = pd.merge(
    per_state2, freight_value, how='inner', on='customer_state')

    # in this case I used GMV and not price to calculate ratio, this way you can see cost concentration per state
df_freight['freight_cost_index'] = df_freight['freight_value'] / df_freight['GMV']
# Ratio > 1.0 means shipping cost exceeds it's GMV share
print(df_freight.sort_values(ascending=False, by='freight_cost_index'))

""" DATA VIZ """

sns.set_style('whitegrid')

plt.figure(figsize=(10, 5))
sns.histplot(df_customer['GMV'], alpha=0.7, bins='auto')
plt.axvline(x=df_customer['GMV'].mean(), color='r', linestyle='--', label=f'Mean GMV: R${df_customer['GMV'].mean():.2f}')
plt.axvline(x=df_customer['GMV'].median(), color='y', linestyle='--', label=f'Median GMV: R${df_customer['GMV'].median():.2f}')
plt.title('GMV Distribution - 2018', fontsize=14, weight='bold')
plt.xlabel('Price')
plt.ylabel('Count')
plt.legend()
plt.xlim(0, 1200)
plt.tight_layout()
plt.show()

fig = px.bar(per_state, x=per_state.index, y=per_state.values,
             color='GMV', color_discrete_sequence='blue', opacity=0.7,
             title='GMV Per State (SP holds 39.37% of total GMV)', labels={'GMV': 'GMV%'}, template='ggplot2')
fig.update_xaxes(title_text='States')
fig.update_yaxes(title_text='GMV%')

#fig.show()

# Plot Freight_ratio x GMV
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(10, 6))
sns.set_theme(style="whitegrid")

# Box 1: GMV
sns.boxplot(data=df_freight, y='GMV', ax=axes[0], color='b', width=0.4)
axes[0].set_title('Distribution GMV % - 2018', weight='bold', fontsize=13)
axes[0].set_ylabel('GMV %')
axes[0].annotate('SP', xy=(0, 39.37), xytext=(0.3, 39.37), arrowprops=dict(arrowstyle='->', color='black'))

# Box 2: Ratio
sns.boxplot(data=df_freight, y='freight_cost_index', ax=axes[1], color='g', width=0.4)
axes[1].axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Breakeven')
axes[1].set_title('Freight-To-Revenue-Index', weight='bold', fontsize=13)
axes[1].set_ylabel('Index')
axes[1].annotate('SP', xy=(0, 0.84), xytext=(0.3, 0.84), arrowprops=dict(arrowstyle='->', color='black'))

plt.tight_layout()
plt.show()

"""
KEY INSIGHTS: (2018) 
- Operation is profitable only due to SP
- SP: GMV 39.3%, Ratio 0.84 -> Only profitable State 
"""




