# imports
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
import get_gacc_data

@st.experimental_memo
def start():
    monthly_trade_df = get_gacc_data.get_monthly_global_trade()
    return monthly_trade_df

df = start()


st.title("Chinese Goods Trade")
st.write("""This dashboard examines Chinese goods trade with the world.
The underlying data is taken from the wesbite of the General Administration of Customs China (GACC),
and uses a combination of both preliminary releases and full monthly bulletins.
GACC's preliminary bulletins include aggregate bilateral data for a limited set of trade partners, 
but include no data on trade by partner by product. 
Monthly bulletins include aggregate bilateral trade data for a fuller set of partners, 
and include trade by partner by product (at HS code 2 digit level) for limited set of partners.
GACC publishes its data according to a set [release schedule](http://english.customs.gov.cn/Statistics/Statistics?ColumnId=4) 
though sometimes its website takes slightly longer to update.
""")
st.write('---')


st.subheader('Chinese goods trade with the world')

st.write('Monthly trade with the world, USD Billions')
st.line_chart(df.div(1000).round(2))

st.write('Monthly trade with the world, % change yoy')
st.line_chart(df.pct_change(12).mul(100))

st.write('Monthly trade with the world, USD Billions change yoy')
st.line_chart(df.diff(12).div(100).round(2))

