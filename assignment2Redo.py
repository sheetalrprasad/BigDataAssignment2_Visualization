import pandas as pd
import numpy as np
from pyparsing import col
import streamlit as st
import altair as alt
import plotly.express as px

from plotly.subplots import make_subplots
import plotly.graph_objects as go

import time
from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)


# Page setup
st.set_page_config(page_title="Covid Data Redo", page_icon=":bar_chart:",layout="wide")

# CSV file variables
covidConfirmedUsaFacts = 'assignment2Data/covid_confirmed_usafacts.csv'
covidDeathsUsaFacts = 'assignment2Data/covid_deaths_usafacts.csv'
covidCountyPopulationUsaFacts = 'assignment2Data/covid_county_population_usafacts.csv'

# New Test Data  
# covidConfirmedUsaFacts = 'testData/covid_confirmed_usafacts.csv'
# covidDeathsUsaFacts = 'testData/covid_deaths_usafacts.csv'
# covidCountyPopulationUsaFacts = 'testData/covid_county_population_usafacts.csv'


# Population per county
populationsPerCounty = pd.read_csv(covidCountyPopulationUsaFacts)

# Confirmed cases dataframe
dailyCases = pd.read_csv(covidConfirmedUsaFacts)
dailyCases.drop(columns = ['State','County Name','StateFIPS'], inplace=True)

dailyCasesEachCounty = dailyCases.groupby('countyFIPS').sum()

dailyCasesEachCounty =  dailyCasesEachCounty.diff(axis=1) # The data is cumulative

dailyCasesEachCounty.columns = pd.to_datetime(dailyCasesEachCounty.columns)

# To Find Proper Week set
startDate = 0
for i in range(len(dailyCasesEachCounty.columns)):
    # to find first sunday 
    if dailyCasesEachCounty.columns[i].weekday() == 6:
        startDate= i
        break;

reverseCountyColumns = dailyCasesEachCounty.columns[::-1]

endDate = len(dailyCasesEachCounty.columns)
for i in range(len(dailyCasesEachCounty.columns)):
    # to find last saturday 
    if reverseCountyColumns[i].weekday() == 5:
        endDate -= i
        break;


weekInfo =  pd.period_range(start = dailyCasesEachCounty.columns[startDate], end =  dailyCasesEachCounty.columns[endDate-1], freq = 'W-SAT').map(str)
weekInfo = pd.Series(weekInfo.str.split('/').str[0])

# Data with full weeks 
dailyCasesEachCounty = dailyCasesEachCounty.iloc[:,startDate:endDate]
dailyCasesEachCounty = dailyCasesEachCounty.transpose()
dailyCasesEachCounty.reset_index(inplace=True)
dailyCasesEachCounty.rename(columns={'index':'Date'},inplace=True)

# Calculating Weekly numbers in data
weeklyUsaCasesEachCounty = round(dailyCasesEachCounty.groupby(dailyCasesEachCounty.index // 7).sum(),2)
weeklyUsaCasesEachCounty.set_index(weekInfo, inplace=True)



# Death Dataframe 
dailyDeaths = pd.read_csv(covidDeathsUsaFacts)
dailyDeaths.drop(columns = ['State','County Name','StateFIPS'], inplace=True)

# # sync type with counties as it is used to map choropleth
# dailyDeaths['countyFIPS'] = dailyDeaths['countyFIPS'].apply(str) 
# dailyDeaths['countyFIPS'] = dailyDeaths['countyFIPS'].apply(lambda x: x.zfill(5))

dailyDeathsEachCounty = dailyDeaths.groupby('countyFIPS').sum()
dailyDeathsEachCounty = dailyDeathsEachCounty.diff(axis=1) # The data is cumulative

dailyDeathsEachCounty.columns = pd.to_datetime(dailyDeathsEachCounty.columns)

# To Find Proper Week set
startDate = 0
for i in range(len(dailyDeathsEachCounty.columns)):
    # to find first sunday 
    if dailyDeathsEachCounty.columns[i].weekday() == 6:
        startDate= i
        break;

reverseCountyColumns = dailyDeathsEachCounty.columns[::-1]

endDate = len(dailyDeathsEachCounty.columns)
for i in range(len(dailyDeathsEachCounty.columns)):
    # to find last saturday 
    if reverseCountyColumns[i].weekday() == 5:
        endDate -= i
        break;

weekInfoDeaths =  pd.period_range(start = dailyDeathsEachCounty.columns[startDate], end =  dailyDeathsEachCounty.columns[endDate-1], freq = 'W-SAT').map(str)
weekInfoDeaths = pd.Series(weekInfoDeaths.str.split('/').str[0])

# Data with full weeks 
dailyDeathsEachCounty = dailyDeathsEachCounty.iloc[:,startDate:endDate]
dailyDeathsEachCounty = dailyDeathsEachCounty.transpose()
dailyDeathsEachCounty.reset_index(inplace=True)
dailyDeathsEachCounty.rename(columns={'index':'Date'},inplace=True)

# Calculating Weekly numbers in data
weeklyUsaDeathsEachCounty = round(dailyDeathsEachCounty.groupby(dailyDeathsEachCounty.index // 7).sum(),2)
weeklyUsaDeathsEachCounty.set_index(weekInfoDeaths,inplace=True)


def per100K(data):
    '''
        The function takes input of weekly number and calculates weekly number per 100K of populations
    '''
    populations = populationsPerCounty[['countyFIPS','population']]
    populations = populations.groupby('countyFIPS').sum()

    data = data.transpose()
    data.reset_index(inplace=True)
    data.rename(columns={'index':'countyFIPS'},inplace=True)

    weeklyCasesPerCounty = pd.merge(data,populations,on=['countyFIPS'])
    weeklyCasesPerCounty = weeklyCasesPerCounty.iloc[1:,:]

    for j in range(1,108):
       weeklyCasesPerCounty.iloc[:,j] = round((weeklyCasesPerCounty.iloc[:,j]/weeklyCasesPerCounty['population'])*100000,2)
    
    # sync type with counties as it is used to map choropleth
    weeklyCasesPerCounty['countyFIPS'] = weeklyCasesPerCounty['countyFIPS'].apply(str) 
    weeklyCasesPerCounty['countyFIPS'] = weeklyCasesPerCounty['countyFIPS'].apply(lambda x: x.zfill(5))

    weeklyCasesPerCounty.set_index('countyFIPS',inplace=True)
    weeklyCasesPerCounty.drop(columns=['population'],inplace=True)
    
    return weeklyCasesPerCounty


def choroplethGraphForWeek(weeklyData, label,colormap):
    '''
        The function maps the choropleth map with data of a specific week.
    '''

    mapData = pd.DataFrame({'countyFIPS':weeklyData.index,'Cases':weeklyData})

    # plotting chrolopleth
    fig = px.choropleth(mapData, geojson=counties, locations='countyFIPS', color='Cases',
                            color_continuous_scale=colormap,
                            range_color=(mapData.iloc[:,1].min(), mapData.iloc[:,1].max()),
                            scope="usa",
                            labels={'Cases':label}
                            )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig,use_container_width=True)


def startAnimation():
    '''
        The function maps the choropleth map with data of a specific week.
    '''

    for week in weekInfo:
        
        with casesPlotPosition:
            fig = px.choropleth(weeklyCasesPer100KPopulation, locations=weeklyCasesPer100KPopulation.index, geojson= counties,
            color= week, color_continuous_scale='sunset', range_color=(0,weeklyCasesPer100KPopulation[week].max()))
            
            fig.update_layout( title_text = 'New weekly cases per 100K on {0}'.format(week),geo_scope='usa',)
            
            st.plotly_chart(fig,use_container_width=True)
            
        
        with deathPlotPosition:
            fig1 = px.choropleth(weeklyDeathsPer100KPopulation, locations=weeklyDeathsPer100KPopulation.index, geojson= counties,
                        color= week, color_continuous_scale='viridis', range_color=(weeklyDeathsPer100KPopulation[week].min(),weeklyDeathsPer100KPopulation[week].max()),)
            
            fig1.update_layout( title_text = 'Weekly deaths per 100K on {0}'.format(week), geo_scope='usa',)

            st.plotly_chart(fig1,use_container_width=True)
        
        time.sleep(1)
        




if __name__ == '__main__':

    startDateOfData = pd.to_datetime(weeklyUsaCasesEachCounty.index[0])
    endDateOfData = pd.to_datetime(weeklyUsaCasesEachCounty.index[-1])
    startMonth = startDateOfData.month_name()
    startYear = startDateOfData.year
    endMonth = endDateOfData.month_name()
    endYear = endDateOfData.year
    heading = 'Covid-19 Data Visualization ({0} {1} - {2} {3})'.format(startMonth,startYear,endMonth,endYear)
    st.header(heading)
    

    st.subheader('Problem 1')
    # Produce a line plot of the weekly new cases of Covid-19 in the USA from the start of the pandemic.
    st.write("Weekly New Cases")

    data = weeklyUsaCasesEachCounty.sum(axis=1)
    showWeeklyNewCases = pd.DataFrame({'Date':data.index, 'Total Cases':data})
    showWeeklyNewCases.reset_index(inplace=True)
    showWeeklyNewCases.drop(columns='index',inplace=True)
    
    chartCases = alt.Chart(showWeeklyNewCases).mark_line().encode(x=alt.X('Date:T', axis=alt.Axis(
        labelAngle=90, labelOverlap="greedy")), y='Total Cases:Q', tooltip=[
        alt.Tooltip("Date", title="Date"),
        alt.Tooltip("Total Cases", title="Total Cases"),])
    st.altair_chart(chartCases, use_container_width=True)  


    st.subheader('Problem 2')
    # Produce a line plot of the weekly deaths due to Covid-19 in the USA from the start of the pandemic
    st.write("Weekly Deaths")

    data = weeklyUsaDeathsEachCounty.sum(axis=1)
    showWeeklyDeaths = pd.DataFrame({'Date':data.index, 'Total Deaths':data})
    showWeeklyDeaths.reset_index(inplace=True)
    showWeeklyDeaths.drop(columns='index',inplace=True)

    chartDeaths = alt.Chart(showWeeklyDeaths).mark_line().encode(x=alt.X('Date:T', axis=alt.Axis(
        labelAngle=90, labelOverlap="greedy")), y='Total Deaths:Q',tooltip=[
        alt.Tooltip("Date", title="Date"),
        alt.Tooltip("Total Deaths", title="Total Deaths"),])
    st.altair_chart(chartDeaths, use_container_width=True)


    st.subheader('Problem 3,4, and 5')

    weekNumber = st.slider('Select a week number?', 0, len(weekInfo), 0)
    st.write("Week Number: ",weekNumber)
    st.write("Week Start Date: ",weekInfo.iloc[weekNumber])
    
    weeklyCasesPer100KPopulation = per100K(weeklyUsaCasesEachCounty)
    weeklyDeathsPer100KPopulation = per100K(weeklyUsaDeathsEachCounty)


    #  Using Plotly Choropleth map produce a map of the USA displaying for each county the new
    #    cases of covid per 100,000 people in a week
    st.write("New weekly cases per 100K")
    choroplethGraphForWeek(weeklyCasesPer100KPopulation.iloc[:,weekNumber],'New Weekly Cases per 100K',"sunset")
    
    # Using Plotly Choropleth map produce a map of the USA displaying for each county the
    #    covid deaths per 100,000 people in a week.
    st.write("Weekly Deaths per 100K")
    choroplethGraphForWeek(weeklyDeathsPer100KPopulation.iloc[:,weekNumber],'Weekly Deaths per 100K',"viridis")

    st.subheader('Problem 6')

    button = st.empty()
    casesPlotPosition = st.empty()
    deathPlotPosition = st.empty()

    with button:
        st.button(label='Start Video', on_click= startAnimation)

