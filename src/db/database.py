import sys
import streamlit as st
import awesome_streamlit as ast
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import mariadb 

dbconfig = {
    'host' : "localhost",
    'port' : 3306,
    'user' : "root",
    'password' : "Wft9usbm!",
    'database' : "aggreportproduction"

}


def selectallfrom(parFrom):
    try:
        conn = mariadb.connect(**dbconfig) #dbconfig is defined at the top of this file
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor() 
    query = "SELECT * FROM " + parFrom
    try:
        cur.execute(query)
    except mariadb.Error as e: 
        print(f"Error: {e}")
    row_headers=[x[0] for x in cur.description]
    rv = cur.fetchall()
    data = pd.DataFrame(data = rv, columns = row_headers)
    conn.commit() #
    conn.close()
    return(data)

def subselectfrom(parSelect,parFrom):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "SELECT " + parSelect + " FROM " + parFrom
    try:
        cur.execute(query)
    except mariadb.Error as e: 
        print(f"Error: {e}")
    columns = parSelect.split(',')
    data = pd.DataFrame(columns=columns)
    for columns in cur:
        temp = pd.Series(list(columns),index = data.columns)
        data = data.append(temp, ignore_index = True)
    conn.commit()
    conn.close()
    return(data)


def selectfromwhere(parSelect, parFrom, parWhere, parameters):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "SELECT " + parSelect + " FROM " + parFrom + " WHERE " + parWhere
    try:
        cur.execute(query,(parameters))
    except mariadb.Error as e: 
        print(f"Error: {e}")
    columns = parSelect.split(',')
    data = pd.DataFrame(columns=columns)
    for columns in cur:
        temp = pd.Series(list(columns),index = data.columns)
        data = data.append(temp, ignore_index = True)
    conn.commit()
    conn.close()
    return(data)
    

def insertvaluessingle(parInto, parValues, parameters):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "INSERT INTO " + parInto + " VALUES " + parValues
    try:
        cur.execute(query,(parameters))
    except mariadb.Error as e:
        print(f"Error: {e}")
    conn.commit()
    print(f"last inserted id: {cur.lastrowid}")
    conn.close()
    
def insertorganisations(projectid,df):
    orgids = []
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "INSERT INTO organisation(realorganisationid,region,sector,fk_projectid) VALUES (?,?,?,?)"
    for i in range(len(df)):
        realorgid = df['Organisation'][i]
        region = df['Region'][i]
        sector = df['Sector'][i]
        parameters = (realorgid,region,sector,int(projectid))
        try: 
            cur.execute(query,(parameters))
            orgid = cur.lastrowid
            orgids.append(int(orgid))
        except mariadb.Error as e:
            print(f"Error: {e}")
    conn.commit()
    conn.close()
    return orgids
        
def insertpopulations(projectid,populations,df):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "INSERT INTO population(name,description,fk_projectid) VALUES (?,?,?)"
    for popname in populations:
        parameters = (popname,popname,int(projectid))
        try:
            cur.execute(query,(parameters))
            popid = cur.lastrowid
            query2 = "INSERT INTO populationorganisation_map(fk_populationid,fk_organisationid) VALUES (?,?)"
            for i in range(len(df)):
                orgid = df["organisationid"][i]
                if df[popname][i] == 'x':
                    pars = (int(popid),int(orgid))
                    try:
                        cur.execute(query2, (pars))    
                    except mariadb.Error as e:
                        print(f"Error: {e}")              

        except mariadb.Error as e:
                print(f"Error: {e}")

    conn.commit()
    conn.close()
        


    

def insertquestions(methodid, df):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()

    topics = df["Topic"].unique().tolist()
    topicids = []
    topicquery = "INSERT INTO topic(name,fk_methodid) VALUES (?,?)"
    for topic in topics:
        topicparameters = (topic,int(methodid))
        try:
            cur.execute(topicquery,(topicparameters))
            topicid = cur.lastrowid
            topicids.append(topicid)
        except mariadb.Error as e:
            print(f"Error: {e}")
    
    topicdata = {"topicid":topicids, "topicname":topics}
    topicdf = pd.DataFrame(topicdata)

    query = "INSERT INTO parameter(realid,name,description,nanmethod,fk_methodid,fk_topicid) VALUES (?,?,?,?,?,?)"
    for i in range(len(df)):
        realid = df['QuestionID'][i]
        name = df['Name'][i]
        description = df['Description'][i]
        topicid = topicdf[topicdf["topicname"] == df["Topic"][i]]["topicid"].iloc[0]
        nanmethod = df["Nanmethod"][i]
        parameters = (realid,name,description,int(nanmethod),int(methodid),int(topicid))
        try:
            cur.execute(query,(parameters))
            parid = cur.lastrowid
            q2 = "INSERT INTO question(realid,fk_parameterid) VALUES (?,?)"
            pars = (realid,parid)
            try:
                cur.execute(q2,(pars))
            except mariadb.Error as e:
                print(f"Error: {e}")
        except mariadb.Error as e:
            print(f"Error: {e}")    
    conn.commit()
    print(f"last inserted id: {cur.lastrowid}")
    conn.close()

def insertvalrules(methodid,projectid,df):

    colnames = df.columns.tolist()
    questionIndex = colnames.index("questions")
    questions = colnames[questionIndex+1:]

    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    cur = conn.cursor()
    query = "INSERT INTO validationrule(rule,description,fk_methodid) VALUES (?,?,?)"
    for i in range(len(df)):
        valrule = df["valrule"][i]
        description = df["valrule"][i]
        parameters = (valrule,description,int(methodid))
        try:
            cur.execute(query,(parameters))
            ruleid = cur.lastrowid
            query2 = "INSERT INTO validationruleparameter_map(fk_parameterid,fk_validationruleid) VALUES (?,?)"
            for question in questions:
                if df[question][i] == 'x': 
                    allPars = selectallfrom("parameter")
                    methodpars = allPars[allPars['realid']== question]
                    parid = methodpars[methodpars["fk_methodid"] == methodid]["parameterid"].iloc[0]
                    parameters2 = (int(parid),int(ruleid))
                    try:
                        cur.execute(query2,(parameters2))
                    except mariadb.Error as e:
                        print(f"Error: {e}")
        except mariadb.Error as e:
            print(f"Error: {e}")    
    conn.commit()
    conn.close()
    

def insertindicators(methodid, df):

    dfTopics = df["topic"].unique().tolist()
    allTopics = selectallfrom("topic")
    methodTopics = allTopics[allTopics["fk_methodid"] == methodid]
    methodTopicsList = methodTopics["name"].tolist()    

    for topic in dfTopics:
        if topic not in methodTopicsList:
            topicquery = "INSERT INTO topic(name,fk_methodid) VALUES (?,?)"
            topicparameters = (topic,int(methodid))
            try:
                cur.execute(topicquery,(topicparameters))
            except mariadb.Error as e:
                print(f"Error: {e}")

                
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "INSERT INTO parameter(realid,name,description,nanmethod,fk_methodid,fk_topicid) VALUES (?,?,?,?,?,?)"
    for i in range(len(df)):
        realid = df['realid'][i]
        name = df['name'][i]
        description = df['description'][i]
        topicid = methodTopics[methodTopics["name"] == df["topic"][i]]["topicid"].iloc[0]
        formula = df['formula'][i]
        parameters = (realid,name,description,int(0),int(methodid),int(topicid))
        try:
            cur.execute(query,(parameters))
            parid = cur.lastrowid
            q2 = "INSERT INTO indicator(realid,fk_parameterid,formula) VALUES (?,?,?)"
            pars = (realid,parid,formula)
            try:
                cur.execute(q2,(pars))
            except mariadb.Error as e:
                print(f"Error: {e}")
        except mariadb.Error as e:
            print(f"Error: {e}")    
    conn.commit()
    print(f"last inserted id: {cur.lastrowid}")
    conn.close()
    
##### INSERT DATA #####

def insertdata(year,methodid,projectid, df):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    
    cur = conn.cursor()
    organisations = selectallfrom("organisation")
    organisations = organisations[organisations['fk_projectid']==projectid]
    pars = selectallfrom("parameter")
    pars = pars[pars["fk_methodid"]==methodid]

    questions = []
    for rowname,j in df.iterrows():
        questions.append(j[0])  

    for colname,j in df.iteritems():
        if colname != 'organisation':
            for i in range(len(j)):
                
                orgid = organisations[organisations['realorganisationid'] == colname]['organisationid'].iloc[0]
                q = questions[i]

                parid = pars[pars['realid'] == q]['parameterid'].iloc[0]
                value = str(j[i])
                query = "INSERT INTO data(value,year,version,fk_parameterid,fk_projectid,fk_organisationid) VALUES (?,?,?,?,?,?)"
                parameters = (value,year,"1.0",int(parid),int(projectid),int(orgid))
                
                try:
                    cur.execute(query,(parameters))
                except mariadb.Error as e:
                    print(f"Error: {e}")
    conn.commit()
    conn.close()
        
def insertaggregation(methodid,populationid,df):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    cur = conn.cursor()
    query = "INSERT INTO aggindicator(realindicatorid,description,formula,fk_methodid,fk_populationid,fk_periodid) VALUES (?,?,?,?,?,?)"
    for i in range(len(df)):
        realindicatorid = df['AggIndID'][i]
        description = df['Description'][i]
        formula = df['formula'][i]
        periodid = df['period'][i]
        parameters = (realindicatorid,description,formula,int(methodid),int(populationid),int(periodid))
        try:
            cur.execute(query,(parameters))
        except mariadb.Error as e:
            print(f"Error: {e}")
    conn.commit()
    conn.close()


def updatevalues(parUpdate, parSet, parWhere, parameters):
    #Connect to MariaDB Platform
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor()
    query = "UPDATE " + parUpdate + " SET " + parSet + " WHERE " + parWhere
    try:
        cur.execute(query, (parameters))
    except mariadb.Error as e: 
        print(f"Error: {e}")
    conn.commit()
    print("Updated values")
    conn.close()

def deletevalue(parDelFrom,parWhere,parameters):
    try:
        conn = mariadb.connect(**dbconfig)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor()
    query = "DELETE FROM " + parDelFrom + " WHERE " + parWhere
    try:
        cur.execute(query, (parameters))
    except mariadb.Error as e: 
        print(f"Error: {e}")
    conn.commit()
    conn.close()

