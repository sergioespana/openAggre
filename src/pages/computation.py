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
    

# def compute(indicators):
#     organisations = db.selectallfrom("organisation")
#     for i in range(len(organisations)):
#         orgid = organisations['organisationid'][i]
#         for j in range(len(indicators)):
#             realid = indicators['realid'][j]
#             formula = indicators['formula'][j]
#             parameterid = indicators['fk_parameterid'][j]
#             value = calculateIndicator(orgid,formula)
            
#             db.insertvaluessingle("data(value,year,version,fk_parameterid,fk_projectid,fk_organisationid)","(?,?,?,?,?,?)",(value,2019,1,int(parameterid),1,int(orgid)))

# def calculateIndicator(orgid,formula):
#     parameters = re.findall(r"\{(.*?)\}",formula)
#     for i in range(len(parameters)):
#         #The parameterid from the db table parameters
#         parameterid = db.selectfromwhere("realid,parameterid","parameter","realid = ?",(parameters[i],))
#         parid = parameterid['parameterid'][0]
#         valuedf = db.selectfromwhere("fk_parameterid,fk_organisationid,value", "data", "fk_parameterid = ? AND fk_organisationid =?",(int(parid),int(orgid),))
#         value = valuedf['value'][0]
#         if value == "nan":
#             value = 0
#         parameterstring = "{" + parameters[i] + "}"
#         formula = formula.replace(parameterstring,str(value))
#         ### parser.interpretformula(formula) ###
#         try:
#             result = eval(formula)
#         except:
#             result = "nan"
#     return(result)
    
