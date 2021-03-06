import pandas as pd
import geopandas as gpd
import joblib
import folium
import urllib
import json
import numpy as np
import os
import altair as alt
import streamlit as st
# from coronavirus.preprocessor.preprocessor import load_data
from coronavirus.mapper.mapper import choropleth_map, base_map
from coronavirus.db_utils.db_utils import DataBase
from coronavirus.utilities.utilities import _max_width_

URL = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
# URL = f'https://github.com/datasets/geo-countries/tree/master/data/countries.geojson'
COUNTRY_GEO = f'{URL}/world-countries.json'
STATE_GEO = f'{URL}/us-states.json'


def load_world_map_page():
    # set to wide-mode
    _max_width_()

    # Get the data
    db = DataBase('COVID-19.db')

    data_type = st.sidebar.selectbox(label='Select data', options=['DEATHS', 'CONFIRMED', 'RECOVERED'], index=0)
    if data_type == 'CONFIRMED':
        response = 'confirmed'
        df = db.read_table_to_dataframe('jh_global_confirmed', response)
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
    elif data_type == 'DEATHS':
        response = 'deaths'
        df = db.read_table_to_dataframe('jh_global_deaths', response)
    else:
        response = 'recovered'
        df = db.read_table_to_dataframe('jh_global_recovered', response)

    st.header("World Map")

    # Select Date
    df['date'] = pd.to_datetime(df['date']).apply(lambda x: x.date())
    current_date = df['date'].max()
    date = st.sidebar.date_input("Select Date:", value=current_date)
    df = df.loc[df['date'] == date]

    # Merge ISO2 Codes
    link = "http://country.io/names.json"
    f = urllib.request.urlopen(link)

    country_json = f.read().decode("utf-8")
    country_ISO2 = json.loads(country_json)
    country_ISO2_df = pd.DataFrame(country_ISO2.items(), columns=['ISO2 Code','country/region'])

    df = pd.merge(df, country_ISO2_df, on='country/region', how='inner')

    # Merge ISO3 Codes
    link = "http://country.io/iso3.json"
    f = urllib.request.urlopen(link)

    country_json = f.read().decode("utf-8")
    country_ISO3 = json.loads(country_json)
    country_ISO3_df = pd.DataFrame(country_ISO3.items(), columns=['ISO2 Code','ISO3 Code'])

    df = pd.merge(df, country_ISO3_df, on='ISO2 Code', how='inner')

    # Create map
    with st.spinner('Rendering map...'):
        active_map = choropleth_map(df,
                                    columns=['ISO3 Code', response],
                                    geo_data=COUNTRY_GEO,
                                    color='YlGn',
                                    legend='Cases')
        # active_map = base_map()
        st.write(active_map._repr_html_(), unsafe_allow_html=True)
        active_map.save("map.html")
        st.success("Map rendered.")
  
    