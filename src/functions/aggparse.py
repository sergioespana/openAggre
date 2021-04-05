import sys 
import pandas as pd
import streamlit as st
import re 
import src.db.database as db
import numpy as np

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]

def interpret(formula,df):
    print("Current formula piece: " + formula)
    if re.match(r'\Asum\([^\(\)]+\)\Z',formula): #Identify popsum operator
        return popsum(interpret(formula[4:-1],df),df)
    elif re.match(r'\Aavg\([^\(\)]+\)\Z',formula): #Identify popsum operator
        return average(interpret(formula[4:-1],df),df)
    elif re.match(r'\Amax\([^\(\)]+\)\Z',formula): #Identify popsum operator
        return maximum(interpret(formula[4:-1],df),df)
    elif re.match(r'\Amin\([^\(\)]+\)\Z',formula): #Identify popsum operator
        return minimum(interpret(formula[4:-1],df),df)
    elif re.match(r'\Ayesno\([^\(\)]+\)\Z',formula): #Identify popsum operator
        return sino(interpret(formula[6:-1],df),df)
    elif re.match(r'\Acount\([^\(\)]+\)\Z',formula): #Identify popsum operator
        return count(interpret(formula[6:-1],df),df)
    elif re.match(r'\A(.*?)\s\Z',formula): #Remove wspace at the back of the string
        return interpret(formula[:-1],df)
    elif re.match(r'\A\s(.*?)\Z',formula): #Remove wspace at the start of the string
        return(interpret(formula[1:],df))
    elif ')' in formula:
        return betweenParantheses(0,0,formula,0,formula,df) 
    elif re.match(r'\A0?.?(\d+)\Z',formula): #Pass numerical value as numerical value for calculation
        return eval(formula)
    elif re.match(r'\Aind(\d+)[a-z]{0,1}\Z',formula): #Identify indicator parameter
        return getParameterid(formula)
    elif re.match(r'\Aq(\d+)[a-z]{0,1}\Z',formula): #Identify question parameter
        return getParameterid(formula)
    else: #Multi component formula that must be recursively split into concrete components
        if '+' in formula or '-' in formula:
            components = re.compile(r'[\+\-]').split(formula)
        else:
            components = re.compile(r'[\*\/]').split(formula)
        pos = len(components[0])
        
        left = formula[:pos]
        right = formula[pos+1:]
        operator = formula[pos]
        if operator == "+":
            return interpret(left,df) + interpret(right,df)
        elif operator == "-":
            return interpret(left,df) - interpret(right,df)
        elif operator == "*":
            return interpret(left,df) * interpret(right,df)
        elif operator == "/":
            denominator = interpret(right,df)
            if denominator == 0 or denominator is np.nan:
                return np.nan
            else:
                return interpret(left,df) / interpret(right,df)  
    return np.nan
        
    
def popsum(indicator,df):
    values = df[df.fk_parameterid == indicator]['value'].values
    result = 0
    leftout = 0
    for value in values:
        try:
            result += int(value)
        except:
            leftout += 1
    return result

def average(indicator,df):
    values = df[df.fk_parameterid == indicator]['value'].values
    sum = 0
    print(values)
    leftout = 0
    for value in values:
        try:
            sum += eval(value)
        except:
            leftout += 1
    result = sum / (len(values) - leftout)
    return result 

def maximum(indicator,df):
    values = df[df.fk_parameterid == indicator]['value'].values.tolist()
    values = [int(i) for i in values]

    result = max(values)
    return result
    
def minimum(indicator,df):
    values = df[df.fk_parameterid == indicator]['value'].values.tolist()
    values = [int(i) for i in values]

    result = min(values)
    return result 

def sino(indicator,df):
    values = df[df.fk_parameterid == indicator]['value'].values
    si = 0
    no = 0
    for value in values:
        if value == "si" or value == "X" or value == 'x':
            si += 1
        elif value == "no" or value == "0":
            no += 1
    result = (si,no)
    return(result)

def count(indicator,df):
    values = df[df.fk_parameterid == indicator]['value'].values
    count = 0
    for value in values:
        if value == "si" or value == "X" or value == 'x':
            count += 1
    return count

def betweenParantheses(amountLeft, amountRight, formulaString, pos,formula, df):
    i = formulaString[0]
    if i == "(":
        amountLeft += 1
        pos += 1
        return betweenParantheses(amountLeft,amountRight,formulaString[1:],pos,formula, df)
    elif i == ")":
        amountRight += 1
        pos += 1
        if amountLeft == amountRight:
            left = formula[:pos]
            right = formula[pos+1:]
            start = left.find('(')
            if start == 0: # If the first char of the string is the opening parenthesis
                left = left[1:-1]
                leftValue = interpret(left,df)
                newFormula = str(leftValue) + right
                return interpret(newFormula,df)
            elif formula[start-3:start] == "max" or formula[start-3:start] == "sum" or formula[start-3:start] == "min" or formula[start-3:start] == "num" or formula[start-3:start] == "avg":
                pos += 1
                return betweenParantheses(amountLeft,amountRight,formulaString[1:],pos,formula,df)
            else:
                betweenValue = interpret(formula[start:pos],df)
                left = left[:start]
                newFormula = left + str(betweenValue) + right
                return interpret(newFormula,df)
        else:
            return betweenParantheses(amountLeft,amountRight,formulaString[1:],pos,formula,df)
    else:
        pos += 1
        return betweenParantheses(amountLeft,amountRight,formulaString[1:],pos,formula,df)

    
def getParameterid(realid):
    # Use db class to get parameterid
    parameterdf = db.selectfromwhere("realid,fk_methodid,parameterid","parameter","realid = ? and fk_methodid = ?",(realid,int(currentMethod),))
    result = parameterdf['parameterid'].iloc[0]
    return result

