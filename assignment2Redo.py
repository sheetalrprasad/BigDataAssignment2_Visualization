import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import plotly.express as px
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
weeklyUsaDeathsEachCounty.set_index(weekInfo,inplace=True)


def per100K(data):
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
    
    return weeklyCasesPerCounty


def choroplethGraphForWeek(weeklyData, label,colormap):
    '''
        The function maps the choropleth map with data of a specific week.
    '''

    mapData = pd.DataFrame({'countyFIPS':weeklyData.index,'Cases':weeklyData})

    # plotting chrolopleth
    fig = (px.choropleth(mapData, geojson=counties, locations='countyFIPS', color='Cases',
                            color_continuous_scale=colormap,
                            range_color=(mapData.iloc[:,1].min(), mapData.iloc[:,1].max()),
                            scope="usa",
                            labels={'Cases':label}
                            ))
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig


if __name__ == '__main__':

    st.header("Covid-19 Data Visualization (Jan 2020 - Feb 2022)")
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


    weekNumber = st.slider('Select a week number?', 0, 106, 0)
    st.write("Week Number: ",weekNumber)
    st.write("Week Start Date: ",weekInfo.iloc[weekNumber])
    
    #  Using Plotly Choropleth map produce a map of the USA displaying for each county the new
    #    cases of covid per 100,000 people in a week
    st.write("New cases per 100K")
    weekData = per100K(weeklyUsaCasesEachCounty).iloc[:,weekNumber]
    st.plotly_chart(choroplethGraphForWeek(weekData,'New Cases per 100K',"sunset"),use_container_width=True)
    
    # Using Plotly Choropleth map produce a map of the USA displaying for each county the
    #    covid deaths per 100,000 people in a week.
    st.write("Deaths per 100K")
    weekDataDeaths=  per100K(weeklyUsaDeathsEachCounty).iloc[:,weekNumber]
    st.plotly_chart(choroplethGraphForWeek(weekDataDeaths,'Deaths per 100K',"portland"),use_container_width=True)

