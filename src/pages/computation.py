import sys
import streamlit as st
import awesome_streamlit as ast
import pandas as pd
import re
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import mariadb 
import src.db.database as db
import src.functions.parser as parser

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]

def write():
    st.write("Welcome to the indicator computation page")
    st.write("The indicators you have added: ")
    parameters = db.selectallfrom("parameter")
    parameters = parameters[parameters["fk_methodid"] == currentMethod]
    parameterlist = parameters["parameterid"].values
    indicators = db.selectallfrom("indicator")
    indicators = indicators[indicators["fk_parameterid"].isin(parameterlist)]

    st.write(indicators[['indicatorid','formula','realid']])
    if st.button("Compute indicators!"):
        parser.computeInds(indicators)
    

