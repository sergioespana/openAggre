import sys 
import pandas as pd
import re 
import src.db.database as db
import numpy as np

projects = db.selectallfrom("project")
currentProject = projects[projects['currentProject'] == 1]['projectid'].iloc[0]
currentMethod = projects[projects['currentProject'] == 1]['fk_methodid'].iloc[0]


def interpret(formula,df):
    #print("Current formula piece: " + formula)
    if re.match(r'\Asumswitch\((.*?)\)\Z',formula):
        return computeSumSwitchValue(formula,df)
    elif re.match(r'\Aswitch\((.*?)\)\Z',formula):
        return computeSwitchValue(formula,df)
    elif re.match(r'\A(.*?)\s\Z',formula): #Remove wspace at the back of the string
        return interpret(formula[:-1],df)
    elif re.match(r'\A\s(.*?)\Z',formula): #Remove wspace at the start of the string
        return interpret(formula[1:],df)
    elif ')' in formula:
        return betweenParantheses(0,0,formula,0,formula,df)
    elif re.match(r'\A\((.*?)\)\Z',formula):
        return interpret(formula[1:-1],df)
    elif re.match(r'\A(\d*\.?\d*)\Z',formula): #Pass numerical value as numerical value for calculation
        return eval(formula)
    elif re.match(r'\Aind(\d+)[a-z]{0,1}\Z',formula): #Identify indicator parameter
        return getParameterValue(formula,df)
    elif re.match(r'\Aq(\d+)[a-z]{0,1}\Z',formula): #Identify question parameter
        return getParameterValue(formula,df)  
    elif formula == "no" or formula == "si" or formula == "X":
        return formula 
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
            elif formula[start-3:start] == "max" or formula[start-3:start] == "sum" or formula[start-3:start] == "min" or formula[start-3:start] == "tch" or formula[start-3:start] == "ase":
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


def computeSumSwitchValue(formula,df):
    cases = re.findall(r'case\((.*?)\)\;',formula)
    result = 0
    for case in cases:
        left, right = case.split(',')
        value = interpret(left,df)
        if value == "X" or value == "si":
            result += int(right)

    return result

def computeSwitchValue(formula,df):
    cases = re.findall(r'case\((.*?)\)\;',formula)
    for case in cases:
        left, right = case.split(',')
        if left == "else":
            return right
        value = interpret(left,df)
        if value == "X" or value == "si":
            return right
    return np.nan
    



def computeValue(formula,df):
    result = interpret(formula,df)
    return result

def getParameterValue(realid,df):

    ### Cache this, otherwise every calculation needs to update parameters
    parameterdf = db.selectallfrom('parameter')
    parameterdf = parameterdf[parameterdf["fk_methodid"] == currentMethod]
    parid = parameterdf[parameterdf['realid'] == realid]['parameterid'].iloc[0]
    #print("My parameterid is this: " + str(parid))
    result = df[df['fk_parameterid'] == parid]['value'].iloc[0]
    if result == "nan":
        return np.nan
    return interpret(result,df)


def findParameters(formula):
    return

