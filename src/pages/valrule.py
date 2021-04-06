import sys
import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import src.db.database as db
import streamlit.components.v1 as components
import os

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]

parent_dir = os.path.dirname(os.path.abspath("openAggre"))
build_dir = os.path.join(parent_dir,"build")
_selectable_data_table = components.declare_component("selectable_data_table",path= build_dir)


def selectable_data_table(data, key=None):
    return _selectable_data_table(data=data, default=[], key=key)


nanMethods = {0:"None selected",1:"Convert to 0",2:"Convert to no",3:"Set empty values to inactive"}



def get_indicators():
    parameters = db.selectallfrom("parameter")
    parameters = parameters[parameters["fk_methodid"] == currentMethod]
    result = []
    for i in range(len(parameters)):
        name = parameters['name'].iloc[i]
        realid = parameters['realid'].iloc[i]
        result.append((realid,name))
    return result



def write():
    st.title("Validation rules")
    st.write("Add validation rule")
    
    options = get_indicators()
    indicator_selected = st.selectbox("Select Indicator", options=options)
    realid = indicator_selected[0]

    currentNaNmethoddf = db.selectfromwhere("realid,nanmethod","parameter", "realid = ?",(realid,))
    currentNaNMethod = currentNaNmethoddf['nanmethod'].iloc[0]

    st.write("Current way to deal with empty values: " + nanMethods[currentNaNMethod])
    #if st.button("Update NaN-method"):
    NaNoptions = ["None selected","Convert to 0", "Convert to no", "Set empty values to inactive"]
    nanMethod = st.selectbox("Update NaN-method",options = NaNoptions)
    if st.button("Update method"):
        if nanMethod == "None selected":
            db.updatevalues("parameter", "nanmethod = ?", "realid = ?",(0,realid))
        elif nanMethod == "Convert to 0":
            db.updatevalues("parameter", "nanmethod = ?", "realid = ?",(1,realid))
        elif nanMethod == "Convert to no":
            db.updatevalues("parameter", "nanmethod = ?", "realid = ?",(2,realid))
        else:
            db.updatevalues("parameter", "nanmethod = ?", "realid = ?",(3,realid))

    indicators = db.selectallfrom("indicator")
    parameters = db.selectallfrom("parameter")
    parameters = parameters[parameters["fk_methodid"] == currentMethod]
    questions = db.selectallfrom("question")
    valrules = db.selectallfrom("validationrule")
    valrules = valrules[valrules["fk_methodid"] == currentMethod]
    

    parid = parameters[parameters["realid"] == realid]['parameterid'].iloc[0]
    #ind = questions[questions['realid'] == realid]
    #parid = questions[questions['fk_parameterid'] == par].iloc[0]
    #print(parid)

    temprules = db.selectfromwhere("fk_parameterid,fk_validationruleid","validationruleparameter_map", "fk_parameterid = ?",(int(parid),))
    valruleids = temprules['fk_validationruleid'].tolist()
    validationrules = valrules[valrules['validationruleid'].isin(valruleids)]
    st.write("Other validation rules: ")
    rows = selectable_data_table(validationrules[['rule','description']])
    if st.button("Delete selected"):
        for i in rows:
            db.deletevalue("validationruleparameter_map","fk_parameterid = ? and fk_validationruleid = ?", (int(parid),int(validationrules['validationruleid'].iloc[i])))
            

    newRule = st.text_input("New rule")
    description = st.text_input("Description")
    if st.button("Save rule"):
        db.insertvaluessingle("validationrule(rule,description,fk_methodid)","(?,?,?)",(newRule,description,int(currentMethod)))
        justAddedrule = db.selectfromwhere("rule,validationruleid","validationrule","rule = ?",(newRule,))
        ruleid = justAddedrule['validationruleid'].iloc[0]
        db.insertvaluessingle("validationruleparameter_map(fk_parameterid,fk_validationruleid)","(?,?)",(int(parid),int(ruleid)))
    
    
    

