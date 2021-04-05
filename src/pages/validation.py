import sys
import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import src.db.database as db
import src.functions.valparse as valparse
import streamlit.components.v1 as components

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]

_selectable_data_table = components.declare_component(
    "selectable_data_table", url="http://localhost:3001",
    )

def selectable_data_table(data, key=None):
    return _selectable_data_table(data=data, default=[], key=key)


def get_indicators():
    parameters = db.selectallfrom("parameter")
    parameters = parameters[parameters['fk_methodid']==currentMethod]
    result = []
    for i in range(len(parameters)):
        name = parameters['name'].iloc[i]
        realid = parameters['realid'].iloc[i]
        result.append((realid,name))
    return result


def write():
    st.title("Validation")
    columns = ["dataid","rule","value","parameterid"]
    # Get all the alterations that are going to be done
    alterations = pd.DataFrame(columns = columns)
    data = db.selectallfrom("data")
    
    parameters = get_indicators()
    if st.button("Validate!"):
        for i in range(len(parameters)):
            realid = parameters[i][0]
            parameteriddf = db.selectfromwhere("realid,fk_methodid,parameterid","parameter","realid = ? and fk_methodid = ?",(realid,int(currentMethod),))
            parameterid = parameteriddf['parameterid'].iloc[0]
            
            datadf = data[data['fk_parameterid'] == parameterid]
            datadf = datadf[datadf['isActive'] == 1]
            
            nanmethoddf = db.selectfromwhere("parameterid,nanmethod","parameter","parameterid = ?",(int(parameterid),))
            nanmethod = nanmethoddf['nanmethod'].iloc[0]
            nandf = datadf[datadf['value'] == "nan"]
            print("Nandf: " + str(len(nandf)))
            if len(nandf) > 0:
                if nanmethod == 0:
                    st.write("There are several NaN values in the data for this indicator, but there has not been a method selected yet how to handle these. Please do so under the validation rules section and come back to this page!")
                valparse.applynanMethod(nanmethod,nandf) 

            alterations = validateparameter(parameterid,alterations,columns)

        if len(alterations) > 0:
            for j in range(len(alterations)):
                val = alterations['value'].iloc[j]
                dataid = alterations['dataid'].iloc[j]
                parid = alterations['parameterid'].iloc[j]
                rule = alterations['rule'].iloc[j]
                description = "Rule: " + rule
                db.insertvaluessingle("alteration(old_val,new_val,description,fk_dataid,fk_projectid)","(?,?,?,?,?)", (val,"?",description,int(dataid),int(currentProject)))

        else:
            st.write("All good! According to the validation rules, there are no wrong values.")
    alts = db.selectallfrom("alteration")
    alts = alts[alts['fk_projectid'] == currentProject]
    if len(alts) > 0:
        interactivetable(alts)
    else:
        st.write("Currently no flagged alterations!")

def validateparameter(parameterid,alterations,columns):
    data = db.selectallfrom("data")
    datadf = data[data['isActive'] == 1]
    pardf = datadf[datadf['fk_parameterid'] == parameterid]
    
    
    valrules = db.selectallfrom("validationrule")
    temprules = db.selectfromwhere("fk_parameterid,fk_validationruleid","validationruleparameter_map", "fk_parameterid = ?",(int(parameterid),))
    valruleids = temprules['fk_validationruleid'].tolist()
    validationrules = valrules[valrules['validationruleid'].isin(valruleids)]
    

    for i in range(len(validationrules)):
        temprule = validationrules['rule'].iloc[i]
        for j in range(len(pardf)):
            tempRow = pardf.iloc[j]
            value = tempRow['value']
            dataid = tempRow['dataid']
            orgid = tempRow['fk_organisationid']
            tempdf = datadf[datadf['fk_organisationid'] == orgid]
            result = valparse.check(temprule,value,tempdf)
            if result == False:
                row = pd.DataFrame([[int(dataid),temprule,value,parameterid]],columns = columns)
                alterations = alterations.append(row)
    return alterations
    

def interactivetable(alterations):
    rows = selectable_data_table(alterations[['description','old_val','fk_dataid']])
    newValue = st.text_input("New value")
    if st.button("Change selected"):
        for i in rows:
            row = alterations.iloc[i]
            dataid = row['fk_dataid']
            alterationid = row['alterationid']
            #Check whether newValue adheres to all the valrules
            updateValue(dataid,newValue,alterationid)
    if st.button("Make inactive"):
        for i in rows:
            row = alterations.iloc[i]
            dataid = row['fk_dataid']
            alterationid = row['alterationid']
            makeInactive(dataid,newValue,alterationid)


def updateValue(dataid,newValue,alterationid):
    data = db.selectallfrom("data")
    datadf = data[data['isActive'] == True]
    row = datadf[datadf['dataid'] == dataid]
    db.updatevalues("data","isActive = ?","dataid = ?",(int(0),int(dataid)))
    
    currentversion = row['version'].iloc[0]
    tempsplit = currentversion.split(".")
    fineversion = int(tempsplit[1]) + 1
    newVersion = tempsplit[0] + "." + str(fineversion)
    
    year = row['year'].iloc[0]
    parid = row['fk_parameterid'].iloc[0]
    projectid = row['fk_projectid'].iloc[0]
    orgid = row['fk_organisationid'].iloc[0]
    try:    
        db.insertvaluessingle("data(value,year,version,isActive,fk_parameterid,fk_projectid,fk_organisationid)","(?,?,?,?,?,?,?)",(newValue,year,newVersion,int(1),int(parid),int(projectid),int(orgid)))
        db.deletevalue('alteration','alterationid = ? and fk_projectid = ?',(int(alterationid),int(currentProject)))
    except:
        print("Nope this didn't work !")


def makeInactive(dataid,newValue,alterationid):
    data = db.selectallfrom("data")
    datadf = data[data['isActive'] == True]
    row = datadf[datadf['dataid'] == dataid]
    db.updatevalues("data","isActive = ?","dataid = ?",(int(0),int(dataid)))
    
    currentversion = row['version'].iloc[0]
    tempsplit = currentversion.split(".")
    fineversion = int(tempsplit[1]) + 1
    newVersion = tempsplit[0] + "." + str(fineversion)
    
    year = row['year'].iloc[0]
    parid = row['fk_parameterid'].iloc[0]
    projectid = row['fk_projectid'].iloc[0]
    orgid = row['fk_organisationid'].iloc[0]
    try:    
        db.deletevalue('alteration','alterationid = ? and fk_projectid = ?',(int(alterationid),int(currentProject)))
    except:
        print("Nope this didn't work !")

    
    

    
