import re
import sys
import streamlit as st
import pandas as pd
import src.db.database as db
import src.functions.indparse as indparse
import numpy as np

def savePNG(aggregation):
    fig = aggregation.figure
    name = aggregation.name
    fig.write_image("./results/"+ name + ".png")
    