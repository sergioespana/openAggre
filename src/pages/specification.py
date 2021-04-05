import sys
import streamlit as st
import awesome_streamlit as ast
import pandas as pd
import re
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import mariadb 
import json

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import src.db.database as db
import src.functions.parser as parser
import src.functions.aggparse as aggparse
import src.functions.writeimages as writeimages


projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]


class Aggregation():
    

    def __init__(self, name, type, formula, label, population, period, title, style):
        self.name = name
        self.type = type
        self.formula = formula
        self.label = label
        self.population = population
        self.period = period
        self.title = title
        self.style = style
        self.data = self.constructDf(type,formula,label,population,period)
        self.figure = self.constructFigure(self.data,self.type,self.title)

        
    def constructFigure(self,df,type,title):
        if type == "barchart":
            fig = go.Figure()
            labels = df.Label.unique()

            for label in labels:
                tempdf = df.query(f"Label =='{label}'")
                fig.add_trace(
                    go.Bar(
                        x = [tempdf['Year'],tempdf['Population']], y = tempdf['Value'], name = label,
                        text = round(tempdf['Value']),
                        textposition = 'auto'
                    )
                )
            templates = db.selectallfrom("template")
            layoutJSON = templates[templates['fk_projectid']== currentProject]
            layoutJSON = layoutJSON[layoutJSON['vistype'] == type]['templateDict'].iloc[0]
            layout = json.loads(layoutJSON)    
            fig.update_layout(layout)
            fig.update_layout(barmode = "group",title = title)
        elif type == "categories":
            fig = go.Figure()
            labels = df.Label.unique()

            for label in labels:
                tempdf = df.query(f"Label =='{label}'")
                fig.add_trace(
                    go.Bar(
                        x = tempdf['Value'] , y = [tempdf['Year'],tempdf['Population']], name = label,orientation = 'h',
                        text = round(tempdf['Value']),
                        textposition = 'auto',
                        width = 0.5

                    )
                )
            templates = db.selectallfrom("template")
            layoutJSON = templates[templates['fk_projectid']== currentProject]
            layoutJSON = layoutJSON[layoutJSON['vistype'] == type]['templateDict'].iloc[0]
            layout = json.loads(layoutJSON)    
            fig.update_layout(layout)
            fig.update_layout(title = title, barmode = "stack")
        
        elif type == "table":
            labels = df.Label.unique()
            pops = df.Population.unique()

            
            hVals = [""]
            for pop in pops:
                hVals.append(pop)

            header = dict(values = hVals )

            cVals = []  
            cVals.append(labels)
            for i in range(len(pops)):
                tempResult = []
                for j in range(len(labels)):
                    tempVal = df[df['Population'] == pops[i]]['Value'].iloc[j]
                    tempResult.append(tempVal)
                cVals.append(tempResult)

            cells = dict(values = cVals)

            templates = db.selectallfrom("template")
            layoutJSON = templates[templates['fk_projectid']== currentProject]
            layoutJSON = layoutJSON[layoutJSON['vistype'] == type]['templateDict'].iloc[0]


            layout = json.loads(layoutJSON)  
            header.update({'fill_color': layout['headerFillCol']})
            header.update({'line_color': layout['headerLineCol']})

            cells.update({'fill_color': layout['cellsFillCol']})
            cells.update({'line_color': layout['cellsLineCol']})


            fig = go.Figure(data=[go.Table(header=header,cells=cells)])
            fig.update_layout(title = title)

        else:
            return
        return fig

    def constructDf(self,type,formula,label,population,period):
        rawData = db.selectallfrom("data")
        rawData = rawData[rawData["fk_projectid"] == currentProject]
        rawData = rawData[rawData['isActive'] == 1]
        if type == "barchart":
            dims = self.calculateDimensions(formula,population,period)
            years = self.parsePeriod(period)
            labels = self.parseVariable(label)
            pops = self.parseVariable(population)
            vars = self.parseVariable(formula)
            labelVardf = pd.DataFrame(data = {'label' :labels,'var': vars})

            colPeriod = []
            colVariable = []
            colLabel = []
            colPopulation = []
            colValue = []
            for year in years:
                for pop in pops:
                    print(pop)
                    for var in vars:
                        colPeriod.append(year)
                        colPopulation.append(pop)
                        colVariable.append(var)
                        colLabel.append(labelVardf[labelVardf['var'] == var]['label'].iloc[0])

                        popiddf = db.selectfromwhere("name,fk_projectid,populationid","population","name = ? and fk_projectid = ?",(pop,int(currentProject),))
                        popid = popiddf['populationid'].iloc[0]

                        poporgmapdf = db.selectfromwhere("fk_populationid,fk_organisationid","populationorganisation_map","fk_populationid = ?",(int(popid),))
                        popOrgList = []
                        for i in range(len(poporgmapdf)):
                            tempOrg = poporgmapdf["fk_organisationid"].iloc[i]
                            popOrgList.append(tempOrg)
                        tempDF = rawData[rawData['year'] == str(year)]
                        tempDF = tempDF[tempDF['fk_organisationid'].isin(popOrgList)]
                        

                        #### Calculate the value based on year, pop and var(formula)
                    
                        result = aggparse.interpret(var,tempDF)
                        colValue.append(result)

            data = {'Year' : colPeriod,'Variable':colVariable,'Label':colLabel,'Population':colPopulation,'Value':colValue}

            resultdf = pd.DataFrame(data = data)
            st.write(resultdf)
        elif type == "categories":
            dims = self.calculateDimensions(formula,population,period)
            years = self.parsePeriod(period)
            labels = self.parseVariable(label)
            pops = self.parseVariable(population)
            vars = self.parseVariable(formula)
            labelVardf = pd.DataFrame(data = {'label' :labels,'var': vars})

            colPeriod = []
            colVariable = []
            colLabel = []
            colPopulation = []
            colValue = []
            for year in years:
                for pop in pops:
                    for var in vars:
                        colPeriod.append(year)
                        colPopulation.append(pop)
                        colVariable.append(var)
                        colLabel.append(labelVardf[labelVardf['var'] == var]['label'].iloc[0])

                        popiddf = db.selectfromwhere("name,fk_projectid,populationid","population","name = ? and fk_projectid = ?",(pop,int(currentProject),))
                        popid = popiddf['populationid'].iloc[0]

                        poporgmapdf = db.selectfromwhere("fk_populationid,fk_organisationid","populationorganisation_map","fk_populationid = ?",(int(popid),))
                        popOrgList = []
                        for i in range(len(poporgmapdf)):
                            tempOrg = poporgmapdf["fk_organisationid"].iloc[i]
                            popOrgList.append(tempOrg)
                        tempDF = rawData[rawData['year'] == str(year)]
                        tempDF = tempDF[tempDF['fk_organisationid'].isin(popOrgList)]
                        

                        #### Calculate the value based on year, pop and var(formula)
                        result = aggparse.interpret(var,tempDF)
                        colValue.append(result)

            data = {'Year' : colPeriod,'Variable':colVariable,'Label':colLabel,'Population':colPopulation,'Value':colValue}

            resultdf = pd.DataFrame(data = data)
            st.write(resultdf)

        elif type == "table":
            dims = self.calculateDimensions(formula,population,period)
            years = self.parsePeriod(period)
            labels = self.parseVariable(label)
            pops = self.parseVariable(population)
            vars = self.parseVariable(formula)
            labelVardf = pd.DataFrame(data = {'label' :labels,'var': vars})

            colPeriod = []
            colVariable = []
            colLabel = []
            colPopulation = []
            colValue = []
            for year in years:
                for pop in pops:
                    for var in vars:
                        colPeriod.append(year)
                        colPopulation.append(pop)
                        colVariable.append(var)
                        colLabel.append(labelVardf[labelVardf['var'] == var]['label'].iloc[0])
                        
                        popiddf = db.selectfromwhere("name,fk_projectid,populationid","population","name = ? and fk_projectid = ?",(pop,int(currentProject),))
                        popid = popiddf['populationid'].iloc[0]

                        poporgmapdf = db.selectfromwhere("fk_populationid,fk_organisationid","populationorganisation_map","fk_populationid = ?",(int(popid),))
                        popOrgList = []
                        for i in range(len(poporgmapdf)):
                            tempOrg = poporgmapdf["fk_organisationid"].iloc[i]
                            popOrgList.append(tempOrg)
                        tempDF = rawData[rawData['year'] == str(year)]
                        tempDF = tempDF[tempDF['fk_organisationid'].isin(popOrgList)]
                        

                        #### Calculate the value based on year, pop and var(formula)
                        result = aggparse.interpret(var,tempDF)
                        colValue.append(result)

            data = {'Year' : colPeriod,'Variable':colVariable,'Label':colLabel,'Population':colPopulation,'Value':colValue}

            resultdf = pd.DataFrame(data = data)
            st.write(resultdf)

        else:
            return
        return resultdf
    
    def calculateDimensions(self,formula,population,period):
        formulaSize = 0
        popSize = 0
        periodSize = 0

        if '{' in formula:
            formSplit = formula.split(',')
            formulaSize = len(formSplit)
        else:
            formulaSize = 1

        if '{' in population:
            popSplit = population.split(',')
            popSize = len(popSplit)
        else:
            popSize = 1

        if '{' in period:
            periodSplit = period.split(',')
            periodSize = len(periodSplit)
        else:
            periodSize = 1
        fullDims = formulaSize * popSize * periodSize
        result = {'variables':formulaSize,'population': popSize,'period':periodSize,'dims':fullDims}
        return result

    def parseVariable(self,variable):
        result = []
        if '{' in variable:
            variable = variable[1:-1]
            tempSplit = variable.split(",")
            for i in range(len(tempSplit)):
                tempString = tempSplit[i]
                result.append(tempString)
        else:
            result.append(variable)
        return result        

    def parsePeriod(self,variable):
        currentyeardf = db.selectfromwhere("projectid,currentYear","project","projectid = ?",(7,))
        currentyear = currentyeardf['currentYear'].iloc[0]
        result = []
        if '{' in variable:
            variable = variable[1:-1]
            tempSplit = variable.split(",")
            for i in range(len(tempSplit)):
                tempString = tempSplit[i]
                if "currentyear" in tempString:
                    tempString = tempString.replace("currentyear", currentyear)
                    result.append(eval(tempString))
        else:
            if "currentyear" in variable:
                tempString = variable.replace("currentyear", currentyear)
                result.append(eval(tempString))
            else:
                result.append(variable)
        return result


def write():
    st.title("Aggregation specification")
    datafile = st.file_uploader(type = "xlsx", label = "Specification")
    aggregations = []
    try:
        df = pd.read_excel(datafile)
        st.write(df)
    except:
        st.write("Please upload your aggregation specification")
    if st.button("Make graphs"):
        
        for i in range(len(df)):
            tempName = df['name'].iloc[i]
            tempType = df['type'].iloc[i]
            tempFormula = df['formula'].iloc[i]
            tempLabel = df['label'].iloc[i]
            tempPop = df['population'].iloc[i]
            tempPeriod = df['period'].iloc[i]
            tempTitle = df['title'].iloc[i]
            tempStyle = df['style'].iloc[i]
            tempAggregation = Aggregation(tempName,tempType,tempFormula,tempLabel,tempPop,tempPeriod,tempTitle,tempStyle)
            aggregations.append(tempAggregation)

            st.write(tempAggregation.figure)
            writeimages.savePNG(tempAggregation)

    

    
        
        
        