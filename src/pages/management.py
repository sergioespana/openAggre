import sys
import streamlit as st
import awesome_streamlit as ast
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import src.db.database as db
import src.functions.valparse as valparse
import src.functions.indparse as indparse
import src.functions.aggparse as aggparse
import streamlit.components.v1 as components


def write():
    projects = db.selectallfrom("project")
    currentPhase = projects[projects['currentProject'] == 1]['currentPhase'].iloc[0]
    methodid = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]
    projectid = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
    projectYear = projects[projects['currentProject'] == 1]['currentYear'].iloc[0]

    st.title("Project management")
    st.write("Data import progress: ")
    progressTable(currentPhase)

    st.write("Current data import: ")
    stepSwitcher(currentPhase, methodid, projectid,projectYear)


def stepSwitcher(currentPhase, methodid, projectid, year):
    if(currentPhase == 1):
        organisationupload(projectid)
    elif(currentPhase == 2):
        questionupload(methodid,projectid)
    elif(currentPhase == 3):
        valrulesupload(methodid,projectid)
    elif(currentPhase == 4):
        indicatorupload(methodid,projectid)
    elif(currentPhase == 5):
        dataupload(year,methodid,projectid)
    else:
        st.write("You do not to input any more data!")

def organisationupload(projectid):
    st.write("Upload your organisation import-file")
    datafile = st.file_uploader(type = "xlsx", label = "Organisations")
    try:
        df = pd.read_excel(datafile)
        st.write(df)
    except:
        st.write("Please upload your organisation data")
    if st.button("Commit"):
        colnames = df.columns.tolist()
        popIndex = colnames.index("Population")
        populations = colnames[popIndex+1:]

        orgidlist = db.insertorganisations(projectid,df)
        df["organisationid"] = orgidlist

        db.insertpopulations(projectid,populations,df)
        db.updatevalues("project","currentPhase = ?","projectid = ?",(int(2),int(projectid)))
        st.button("Next import")


def questionupload(methodid,projectid):
    st.write("Upload your questions")
    datafile = st.file_uploader(type = "xlsx", label = "Questions")
    try:
        df = pd.read_excel(datafile)
        st.write(df)
    except:
        st.write("Please upload your question data")
    if st.button("Commit"):
        db.insertquestions(methodid,df)
        db.updatevalues("project","currentPhase = ?","projectid = ?",(int(3),int(projectid)))
        st.button("Next import")


def valrulesupload(methodid,projectid):
    st.write("Upload your validation rules")
    datafile = st.file_uploader(type = "xlsx", label = "Validation rules")
    try:
        df = pd.read_excel(datafile)
        st.write(df)
    except:
        st.write("Please upload your validation rules")
    if st.button("Commit"):
        db.insertvalrules(methodid,projectid,df)
        db.updatevalues("project","currentPhase = ?","projectid = ?",(int(4),int(projectid)))
        st.button("Next import")

def indicatorupload(methodid,projectid):
    st.write("Upload your indicators")
    datafile = st.file_uploader(type = "xlsx", label = "Indicators")
    try:
        df = pd.read_excel(datafile)
        st.write(df)
    except:
        st.write("Please upload your indicator data")
    if st.button("Commit"):
        db.insertindicators(methodid,df)
        db.updatevalues("project","currentPhase = ?","projectid = ?",(int(5),int(projectid)))
        st.button("Next import")


def dataupload(year,methodid,projectid):
    st.write("Upload your data")
    datafile = st.file_uploader(type = "xlsx", label = "Data")
    try:
        df = pd.read_excel(datafile)
        st.write(df)
    except:
        st.write("Please upload your data")
    if st.button("Commit"):
        db.insertdata(year,methodid,projectid,df)
        db.updatevalues("project","currentPhase = ?","projectid = ?",(int(6),int(projectid)))
        st.button("Next import")



def progressTable(currentPhase):
    done = ["DONE"]
    todo = ["TODO"]
    if(currentPhase == 1):
        data = {"Organisations":todo,"Questions":todo,"Validation rules":todo,"Indicators":todo,"Data":todo}
    elif(currentPhase == 2):
        data = {"Organisations":done,"Questions":todo,"Validation rules":todo,"Indicators":todo,"Data":todo}
    elif(currentPhase == 3):
        data = {"Organisations":done,"Questions":done,"Validation rules":todo,"Indicators":todo,"Data":todo}
    elif(currentPhase == 4):
        data = {"Organisations":done,"Questions":done,"Validation rules":done,"Indicators":todo,"Data":todo}
    elif(currentPhase == 5):
        data = {"Organisations":done,"Questions":done,"Validation rules":done,"Indicators":done,"Data":todo}
    elif(currentPhase == 6):
        data = {"Organisations":done,"Questions":done,"Validation rules":done,"Indicators":done,"Data":done}
    else:
        st.write("You do not to input any more data!")
    df = pd.DataFrame(data)
    df.index = [""] * len(df)
    st.table(df)
