import re
import sys
import streamlit as st
import pandas as pd
import src.db.database as db
import src.functions.indparse as indparse
import numpy as np

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]

def getData():
    rawData = db.selectallfrom('data')
    rawData = rawData[rawData["fk_projectid"]== currentProject]
    data = rawData[rawData['isActive'] == 1]
    return data

def computeInds(indicators):
    organisations = db.selectallfrom("organisation")
    organisations = organisations[organisations['fk_projectid'] == currentProject]
    errorList = [(0,0)]
    
    for i in range(len(organisations)):
        orgid = organisations['organisationid'].iloc[i]
        print("Current organisation: " + str(orgid) + " - " + str(i) + " of " + str(len(organisations)))
        for j in range(len(indicators)):
            realid = indicators['realid'].iloc[j]
            formula = indicators['formula'].iloc[j]
            parameterid = indicators['fk_parameterid'].iloc[j]
            try:
                value = calculateIndicator(orgid,formula)
            except:
                value = "nan"
                errorList.append((orgid,parameterid))

            if str(value) == "nan":

                db.insertvaluessingle("data(value,year,version,isActive,fk_parameterid,fk_projectid,fk_organisationid)","(?,?,?,?,?,?,?)",(value,2019,"1.0",0,int(parameterid),int(currentProject),int(orgid)))
            else:
                db.insertvaluessingle("data(value,year,version,isActive,fk_parameterid,fk_projectid,fk_organisationid)","(?,?,?,?,?,?,?)",(value,2019,"1.0",1,int(parameterid),int(currentProject),int(orgid)))
    
def calculateIndicator(orgid,formula):
    data = getData()
    df = data[data['fk_organisationid'] == orgid]
    result = indparse.computeValue(formula,df)

    return result
