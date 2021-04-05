import re
import sys
import pandas as pd
import numpy
import src.db.database as db

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]


def iterate(rule,value,df):
    #print("Current rule: " + rule)
    if re.match(r'\A(.*?)\s\Z',rule): #Remove wspace at the back of the string
        return iterate(rule[:-1],value,df)
    elif re.match(r'\A\s(.*?)\Z',rule): #Remove wspace at the start of the string
        return iterate(rule[1:],value,df)
    elif re.match(r'\A\((.*?)\Z',rule): #Remove parentheses around formula
        return betweenParantheses(1,0,rule[1:],0,rule, value, df)
    elif re.match(r'\A(\d+)\Z',rule): #Parse string to numerical value
        return(eval(rule))
    elif re.match(r'\AX\Z',rule): #Replace variable X by numerical value
        return value
    elif re.match(r'\Aq(\d+)[a-z]{0,1}\Z',rule): #Replace question identifier by value
        return getQvalue(rule,df)
    elif re.match(r'\Anum\([^\(\)]+\)\Z',rule): #Check whether value is numerical
        return num(value)
    elif re.match(r'\Asino\([^\(\)]+\)\Z',rule): #Check whether value is binary yes/no value
        return sino(value)
    elif '<' in rule or '>' in rule or '=' in rule: #Conditional operator
        if '<' in rule or '>' in rule:
            components = re.compile(r'[\<\>]').split(rule)
        elif '=='  in rule:
            components = re.compile(r'==').split(rule)
        pos = len(components[0])
        left = rule[:pos]
        secondchar = rule[pos+1]
        if secondchar == "=":
            right = rule[pos+2:]
            operator = rule[pos] + secondchar
        else:
            right = rule[pos+1:]
            operator = rule[pos]
        if operator == "<":
            return eval(str(iterate(left,value,df)) + "<" + str(iterate(right,value,df)))
        elif operator == ">":
            return eval(str(iterate(left,value,df)) + ">" + str(iterate(right,value,df)))
        elif operator == ">=":
            return eval(str(iterate(left,value,df)) + ">=" + str(iterate(right,value,df)))
        elif operator == "<=":
            return eval(str(iterate(left,value,df)) + "<=" + str(iterate(right,value,df)))
        elif operator == "==":
            return eval(str(iterate(left,value,df)) + "==" + str(iterate(right,value,df)))
    else: #Numerical operator
        if '+' in rule or '-' in rule:
            components = re.compile(r'[\+\-]').split(rule)
        else:
            components = re.compile(r'[\*\/]').split(rule)
        pos = len(components[0])
        left = rule[:pos]
        secondchar = rule[pos+1]
        if secondchar == "=":
            right = rule[pos+2:]
            operator = rule[pos] + secondchar
        else:
            right = rule[pos+1:]
            operator = rule[pos]
        if operator == "+":
            return eval(str(iterate(left,value,df)) + "+" + str(iterate(right,value,df)))
        elif operator == "-":
            return eval(str(iterate(left,value,df)) + "-" + str(iterate(right,value,df)))
        elif operator == "*":
            return eval(str(iterate(left,value,df)) + "*" + str(iterate(right,value,df)))
        elif operator == "/":
            denominator = iterate(right,value,df)
            if denominator == 0 or denominator is np.nan:
                return np.nan
            else:
                return iterate(left,value,df) / iterate(right,value,df)  
    return False #Something went wrong
    


def sino(value):
    if value == "si" or value == "no":
        return True
    elif value == "X" or value == "x":
        return True
    else: #This needs to be improved, since in case of Xs the empty field represent "no"
        return False

def betweenParantheses(amountLeft, amountRight, ruleString, pos,rule,value, df):
    i = ruleString[0]
    if i == "(":
        amountLeft += 1
        pos += 1
        return betweenParantheses(amountLeft,amountRight,ruleString[1:],pos,rule, value, df)
    elif i == ")":
        amountRight += 1
        pos += 1
        if amountLeft == amountRight:
            left = rule[1:pos]
            right = rule[pos+1:]
            leftValue = iterate(left,value,df)
            newRule = str(leftValue) + right
            return iterate(newRule,value,df)
        else:
            return betweenParantheses(amountLeft,amountRight,ruleString[1:],pos,rule,value, df)
    else:
        pos += 1
        return betweenParantheses(amountLeft,amountRight,ruleString[1:],pos,rule,value,df)
                
def getQvalue(realid,df):
    pardf = db.selectfromwhere("realid,fk_methodid,parameterid","parameter","realid = ? and fk_methodid = ?",(realid,int(currentMethod),))
    parid= pardf['parameterid'].iloc[0]
    data = df[df['fk_parameterid'] == parid]
    result = data['value'].iloc[0]
    return result
    


def check(rule,value,df):
    if value == "nan":
        return False
    else:
        result = iterate(rule,value,df)
        if result:
            return True
        else:
            return False
    
def num(value):
    try:
        float(value)
        return True
    except:
        return False

def applynanMethod(nanmethod,df):
    if nanmethod == 0:
        return
    elif nanmethod == 1:
        for i in range(len(df)):
            dataid = df['dataid'].iloc[i]
            db.updatevalues("data", "isActive = ?", "dataid  = ?",(int(0),int(dataid)))
            versiondf = db.selectfromwhere("dataid,version","data","dataid = ?",(int(dataid),))
            currentversion = versiondf['version'].iloc[0]
            tempsplit = currentversion.split(".")
            fineversion = int(tempsplit[1]) + 1
            newVersion = tempsplit[0] + "." + str(fineversion)
            newValue = "0"
            year = df['year'].iloc[i]
            parid = df['fk_parameterid'].iloc[i]
            projectid = df['fk_projectid'].iloc[i]
            orgid = df['fk_organisationid'].iloc[i]
            db.insertvaluessingle("data(value,year,version,isActive,fk_parameterid,fk_projectid,fk_organisationid)","(?,?,?,?,?,?,?)",(newValue,year,newVersion,int(1),int(parid),int(projectid),int(orgid)))
    elif nanmethod == 2:
        for i in range(len(df)):
            dataid = df['dataid'].iloc[i]
            db.updatevalues("data", "isActive = ?", "dataid  = ?",(int(0),int(dataid)))
            versiondf = db.selectfromwhere("dataid,version","data","dataid = ?",(int(dataid),))
            currentversion = versiondf['version'].iloc[0]
            tempsplit = currentversion.split(".")
            fineversion = int(tempsplit[1]) + 1
            newVersion = tempsplit[0] + "." + str(fineversion)
            newValue = "no"
            year = df['year'].iloc[i]
            parid = df['fk_parameterid'].iloc[i]
            projectid = df['fk_projectid'].iloc[i]
            orgid = df['fk_organisationid'].iloc[i]
            db.insertvaluessingle("data(value,year,version,isActive,fk_parameterid,fk_projectid,fk_organisationid)","(?,?,?,?,?,?,?)",(newValue,year,newVersion,int(1),int(parid),int(projectid),int(orgid)))
    elif nanmethod == 3:
        for i in range(len(df)):
            dataid = df['dataid'].iloc[i]
            db.updatevalues("data", "isActive = ?", "dataid = ?",(int(0),int(dataid)))
    else:
        return