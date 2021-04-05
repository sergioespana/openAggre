import sys
import streamlit as st
import awesome_streamlit as ast
import pandas as pd
import altair as alt
import gspread
import src.db.database as db
from oauth2client.service_account import ServiceAccountCredentials

ast.core.services.other.set_logging_format()

import src.pages.projects
import src.pages.computation
import src.pages.valrule
import src.pages.validation
import src.pages.specification
import src.pages.management
import src.pages.template


PAGES = {
    "New project" : src.pages.projects,
    "Data import" : src.pages.management,
    "Template" : src.pages.template,
    "Computation": src.pages.computation,
    "Validation" : src.pages.validation,
    "Validation rules" : src.pages.valrule,
    "Specification" : src.pages.specification 

}

def get_projects():
    projects = db.selectallfrom("project")
    result = []
    for i in range(len(projects)):
        name = projects['name'][i]
        id = projects['projectid'][i]
        result.append((id,name))
    return result

def changeCurrentProject(newid):
    currentProject = db.selectallfrom("project")
    try:
        currid = currentProject[currentProject['currentProject'] == 1]['projectid'].iloc[0]
        db.updatevalues("project", "currentProject = ?", "projectid = ?", (int(0),int(currid)))
    except:
        print("There is no current project!")
    db.updatevalues("project", "currentProject = ?", "projectid = ?", (int(1),int(newid)))

def main():
    options = get_projects()
    try:
        currentProject = db.selectallfrom("project")
        currProjectName = currentProject[currentProject['currentProject'] == 1]['name'].iloc[0]
        currProjectYear = currentProject[currentProject['currentProject'] == 1]['currentYear'].iloc[0]
    except:
        currProjectName = "No current project selected..."
        currProjectYear = "No current project selected..."
    
    st.sidebar.title("Current project:")
    st.sidebar.write("Project name: " + currProjectName)
    st.sidebar.write("Project year: " + currProjectYear)
    project_selected = st.sidebar.selectbox("Change project", options=options)
    projectid = project_selected[0]
    if st.sidebar.button("Change current project"):
        changeCurrentProject(projectid)


    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    page = PAGES[selection]
    with st.spinner(f"Loading {selection} ..."):
        ast.shared.components.write_page(page)
    

if __name__ == "__main__":
    main()





