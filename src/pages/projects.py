import sys
import streamlit as st
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
    st.title("New project")
    
    projectName = st.text_input("Project name:")
    projectYear = st.text_input("Year of survey:")
    aggMethodName = st.text_input("Name of aggregation method:")
    aggMethodDesc = st.text_input("Description of aggregation strategy:")
    
    if(st.button("Add new project")):
        newProject(projectName,projectYear,aggMethodName,aggMethodDesc)


def newProject(projectName, projectYear, aggMethodName, aggMethodDesc):
    methodid = createNewMethod(aggMethodName,aggMethodDesc)
    
    users = db.selectallfrom("user")
    userid = users['userid'].iloc[0]

    db.insertvaluessingle("project(name,fk_userid,fk_methodid,currentPhase,currentYear,currentProject)","(?,?,?,?,?,?)",(projectName,int(userid),int(methodid),int(1),projectYear,0))
    
    projects = db.selectallfrom('project')
    currentProject = projects[projects['name'] == projectName]
    projectid = currentProject['projectid'].iloc[len(currentProject)-1]
    changeCurrentProject(projectid)

    templates = db.selectallfrom("template")

    tempTable = templates[templates['vistype']== "table"]['templateDict'].iloc[0]
    tempCat = templates[templates['vistype']== "categories"]['templateDict'].iloc[0]
    tempBar = templates[templates['vistype']== "barchart"]['templateDict'].iloc[0]

    db.insertvaluessingle("template(vistype,templateDict,fk_projectid)","(?,?,?)",("table",tempTable,int(projectid)))
    db.insertvaluessingle("template(vistype,templateDict,fk_projectid)","(?,?,?)",("categories",tempCat,int(projectid)))
    db.insertvaluessingle("template(vistype,templateDict,fk_projectid)","(?,?,?)",("barchart",tempBar,int(projectid)))

def createNewMethod(name, description):
    db.insertvaluessingle("method(name,description)","(?,?)",(name,description))
    methods = db.selectallfrom('method')
    currentMethod = methods[methods['name'] == name]
    methodid = currentMethod['methodid'].iloc[len(currentMethod)-1]
    return methodid

def changeCurrentProject(newid):
    currentProject = db.selectallfrom("project")
    try:
        currid = currentProject[currentProject['currentProject'] == 1]['projectid'].iloc[0]
        db.updatevalues("project", "currentProject = ?", "projectid = ?", (int(0),int(currid)))
    except:
        print("There is no current project!")
    db.updatevalues("project", "currentProject = ?", "projectid = ?", (int(1),int(newid)))