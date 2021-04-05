import sys
import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from plotly.subplots import make_subplots
from bokeh.models.widgets import ColorPicker
import plotly.graph_objects as go
import src.db.database as db
import src.functions.valparse as valparse
import src.functions.indparse as indparse
import src.functions.aggparse as aggparse
import streamlit.components.v1 as components
import json

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]


class Template():
    def __init__(self,type,colorway,showlegend,template):
        self.type = type
        self.colorway = colorway
        self.showlegend = showlegend
        self.template = template

        self.layout = getLayout(self,type,colorway,showlegend,template)
    
    def getLayout(self,type,colorway,showlegend,template):
        
        layout = {"colorway":colorway,"showlegend":showlegend,"template":template}
        return layout
        



def getVisTypes():
    types = ["barchart", "table", "categories"]
    return types


def write():
    st.title("Template page")
    options = getVisTypes()
    visTypeSelected = st.selectbox("Select visualisation type", options=options)
    

    projects = db.selectallfrom("project")
    currentProject = projects[projects["currentProject"] == 1]['projectid'].iloc[0]


    templates = db.selectallfrom("template")
    projectTemplates = templates[templates["fk_projectid"] == currentProject]
    
    myTemplateJSON = projectTemplates[projectTemplates['vistype'] == visTypeSelected]['templateDict'].iloc[0]
    myTemplate = json.loads(myTemplateJSON)
    if visTypeSelected == "barchart":

        showLegend = st.checkbox("Show/Hide the legend",value = myTemplate['showlegend'])
        theme = getTheme(myTemplate['template'])
        colorway = getColorway(myTemplate['colorway'])
        data = composeDummyData(visTypeSelected)
        figure = constructFigure(data,visTypeSelected)

        layout = {"colorway": colorway,"showlegend":showLegend,"template":theme}
        
        layoutJSON = json.dumps(layout,indent = 4)
        if st.button("Commit"):
            db.updatevalues("template","templateDict = ?", "fk_projectid = ? AND vistype = ?",(layoutJSON,int(currentProject),"barchart"))
        figure.update_layout(layout)
        st.write(figure)
    elif visTypeSelected == "table":

        data = composeDummyData(visTypeSelected)
        header, cells = constructFigure(data,visTypeSelected)
        colorCols = st.beta_columns((1,1))
        headerFillCol = colorCols[0].text_input("Header fill", value = myTemplate['headerFillCol'])
        headerLineCol = colorCols[1].text_input("Header line", value = myTemplate['headerLineCol'])

        cellsFillCol = colorCols[0].text_input("Cells fill", value = myTemplate['cellsFillCol'])
        cellsLineCol = colorCols[1].text_input("Cells line", value = myTemplate['cellsLineCol'])

        header.update({'fill_color': headerFillCol})
        header.update({'line_color': headerLineCol})

        cells.update({'fill_color': cellsFillCol})
        cells.update({'line_color': cellsLineCol})

        layout = {"headerFillCol":headerFillCol,"headerLineCol":headerLineCol, "cellsFillCol":cellsFillCol,"cellsLineCol":cellsLineCol}
        layoutJSON = json.dumps(layout,indent = 4)

        if st.button("Commit"):
            db.updatevalues("template","templateDict = ?", "fk_projectid = ? AND vistype = ?",(layoutJSON,int(currentProject),"table"))

        figure = go.Figure(data=[go.Table(header=header,cells=cells)])
        
        st.write(figure)
        
    elif visTypeSelected == "categories":
        print("Jup")
        showLegend = st.checkbox("Show/Hide the legend",value = myTemplate['showlegend'])
        theme = getTheme(myTemplate['template'])
        print("Jup2")
        data = composeDummyData(visTypeSelected)
        print("Skrt")
        figure = constructFigure(data,visTypeSelected)
        print("Jup3")
        colorway = getColorway(myTemplate['colorway'])
        layout = {"colorway": colorway,"showlegend":showLegend,"template":theme}
        
        layoutJSON = json.dumps(layout,indent = 4)
        if st.button("Commit"):
            db.updatevalues("template","templateDict = ?", "fk_projectid = ? AND vistype = ?",(layoutJSON,int(currentProject),"categories"))
        print(visTypeSelected)
        figure.update_layout(layout)

        st.write(figure)
        
        




def getTheme(theme):
    defaultTheme = st.selectbox("Default theme", options = ["Regular", "White","Dark"])

    if defaultTheme == "Regular":
        theme = "plotly"
    elif defaultTheme == "White":
        theme = "plotly_white"
    elif defaultTheme == "Dark":
        theme = "plotly_dark"
    else:
        theme = "plotly"
    return theme

def getColorway(colorway):
    st.title("Color scheme")
    colorCols = st.beta_columns((1,1,1,1,1))

    firstColor = colorCols[0].text_input("First Color",value = colorway[0])
    secondColor = colorCols[1].text_input("Second Color",value = colorway[1])
    thirdColor = colorCols[2].text_input("Third Color",value = colorway[2])
    fourthColor = colorCols[3].text_input("Fourth Color",value = colorway[3])
    fifthColor = colorCols[4].text_input("Fifth Color",value =colorway[4])
    sixColor = colorCols[0].text_input("Sixth Color",value = colorway[5])
    sevenColor = colorCols[1].text_input("Seventh Color",value = colorway[6])
    eightColor = colorCols[2].text_input("Eighth Color",value = colorway[7])
    ninceColor = colorCols[3].text_input("Ninth Color",value = colorway[8])
    tenColor = colorCols[4].text_input("Tenth Color",value = colorway[9])
    colorway = [firstColor,secondColor,thirdColor,fourthColor,fifthColor,sixColor,sevenColor,eightColor,ninceColor,tenColor]
    return colorway

def getLayout(colorway, showlegend,template):
    colorway = colorway
    showlegend = showlegend
    template = template
    layout = {"colorway":colorway}
    return layout

def constructFigure(df,type):
    title = "Test graph to edit template"

    if type == "barchart":
        fig = go.Figure()
        variables = ["Var1", "Var2", "Var3", "Var4","Var5"]

        for var in variables:
            tempdf = df.query(f"Variable =='{var}'")
            fig.add_trace(
                go.Bar(
                    x = [tempdf['Year'],tempdf['Population']], y = tempdf['Value'], name = var
                )
            )
        return fig
    elif type == "categories":
        fig = go.Figure()
        variables = ["Var1","Var2","Var3"]

        for var in variables:
            tempdf = df.query(f"Variable =='{var}'")
            fig.add_trace(
                go.Bar(
                    x = tempdf['Value'] , y = [tempdf['Year'],tempdf['Population']], name = var,orientation = 'h',
                    text = tempdf['Value'],
                    textposition = 'auto',
                    width = 0.5

                )
            )
        templates = db.selectallfrom("template")
        fig.update_layout(title = title, barmode = "stack")


        return fig
    elif type == "table":
        labels = ["Number of employees","Number of projects","Number of vacancies","Number of customers"]
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
        return header, cells
        
    else:
        return
    

def composeDummyData(type):
    if type == "barchart":
        years = ["2018","2018","2018","2018","2018","2019","2019","2019","2019","2019"]
        populations = ["Region 1","Region 1","Region 1","Region 1","Region 1","Region 1","Region 1","Region 1","Region 1","Region 1",]
        variables = ["Var1", "Var2", "Var3", "Var4","Var5","Var1", "Var2", "Var3", "Var4","Var5"]
        values = [500,400,300,600,800,200,800,500,340,600]

        data = {'Year' : years,'Variable':variables,'Population':populations,'Value':values}
        df = pd.DataFrame(data)
    elif type == "categories":
        years = ["2018", "2018", "2018", "2019", "2019", "2019"]
        populations = ["ALL","ALL","ALL","ALL","ALL","ALL"]
        variables = ["Var1", "Var2", "Var3","Var1", "Var2", "Var3"]
        values = [428,75,27,368,102,40]
        data = {'Year':years,'Variable':variables,'Population':populations,'Value':values}
        df = pd.DataFrame(data)
    elif type == "table":
        years = ["2019","2019","2019","2019","2019","2019","2019","2019","2019","2019","2019","2019"]
        populations = ["Utrecht", "Utrecht", "Utrecht", "Utrecht", "Valencia","Valencia", "Valencia","Valencia","Madrid","Madrid","Madrid","Madrid"]
        variables = ["Var1", "Var2", "Var3", "Var4","Var1", "Var2", "Var3", "Var4","Var1", "Var2", "Var3", "Var4"]
        values = [972,543,429,124,856,283,92,201,482,381,37,201]

        data = {'Year': years, 'Variable': variables,'Population': populations,'Value': values}
        df = pd.DataFrame(data)

    return(df)

    
    