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
st.set_page_config(page_title="Covid Data", page_icon=":bar_chart:",layout="wide")

# CSV file variables
covid_confirmed_usafacts = 'assignment2Data/covid_confirmed_usafacts.csv'
covid_deaths_usafacts = 'assignment2Data/covid_deaths_usafacts.csv'
covid_county_population_usafacts = 'assignment2Data/covid_county_population_usafacts.csv'

populationsPerCounty = pd.read_csv(covid_county_population_usafacts)

# All start dates for weeks available in data
weekInfo =  pd.period_range(start = '2020-01-26', end =  '2022-02-07', freq = 'W-SAT').map(str)
weekInfo = pd.Series(weekInfo.str.split('/').str[0])

def usaWeeklyNewCases():
    '''
    The function returns average weekly deaths per week in USA.
    '''
    newCases = pd.read_csv(covid_confirmed_usafacts)
    newCases = newCases.drop(columns=['countyFIPS','County Name','State','StateFIPS'])

    newCasesEveryday = pd.DataFrame({'Total Cases': newCases.sum()})
    newCasesEveryday = newCasesEveryday[4:]
    newCasesEveryday = newCasesEveryday.diff()
    newCasesEveryday = newCasesEveryday[newCasesEveryday['Total Cases']>=0]
    newCasesEveryday.reset_index(inplace=True)
    newCasesEveryday.rename(columns={'index':'Date'},inplace=True)

    weeklyDataUSA = round(newCasesEveryday.groupby(newCasesEveryday.index // 7).sum(),2)
    weeklyDataUSA['Date'] = pd.to_datetime(weekInfo, utc=False)
    weeklyDataUSA = weeklyDataUSA[['Date','Total Cases']]

    return weeklyDataUSA

def usaWeeklyDeaths():
    '''
    The function returns average weekly deaths per week in USA.
    '''
    deathCases = pd.read_csv(covid_deaths_usafacts)
    deathCases = deathCases.drop(columns=['countyFIPS','County Name','State','StateFIPS'])
    deathCasesEveryday = pd.DataFrame({'Total Deaths': deathCases.sum()})
    deathCasesEveryday = deathCasesEveryday[deathCasesEveryday['Total Deaths']>=0]
    deathCasesEveryday = deathCasesEveryday[4:]
    deathCasesEveryday = deathCasesEveryday.diff()
    deathCasesEveryday.reset_index(inplace=True)
    deathCasesEveryday.rename(columns={'index':'Date'},inplace=True)

    weekly_data = round(deathCasesEveryday.groupby(deathCasesEveryday.index // 7).sum(),2)
    week_start = [deathCasesEveryday['Date'][i] for i in range(len(deathCasesEveryday)) if i%7==0 ]
    weekly_data['Date'] = pd.to_datetime(week_start,utc=False)
    weekly_data = weekly_data[['Date','Total Deaths']]

    return weekly_data

@st.cache
def newCasesCalculations():
    '''
        The function takes the per county stats of cases and population and returns a dataframe with values of new cases in each county per 100K.
    '''
    dailyCases = pd.read_csv(covid_confirmed_usafacts)
    dailyCases = dailyCases.drop(columns = ['State' ,'StateFIPS','County Name',  '2020-01-22','2020-01-23', '2020-01-24', '2020-01-25'])
    dailyCasesPerCounty = dailyCases.groupby('countyFIPS').sum()
    dailyCasesPerCounty = dailyCasesPerCounty.diff(axis = 1)

    weeklyCasesPerCounty = dailyCasesPerCounty.groupby([[i//7 for i in range(0,len(dailyCasesPerCounty.columns))]], axis = 1).sum().T
    weeklyCasesPerCounty[weeklyCasesPerCounty<0] = 0
    weeklyCasesPerCounty = weeklyCasesPerCounty.T

    populations = populationsPerCounty[['countyFIPS','population']]
    populations = populations.groupby('countyFIPS').sum()

    weeklyCasesPerCounty = pd.merge(weeklyCasesPerCounty,populations,on=['countyFIPS'])
    weeklyCasesPerCounty = weeklyCasesPerCounty.iloc[1:,:]

    weeklyCasesPerCounty.reset_index(inplace=True)

    for j in range(1,108):
       weeklyCasesPerCounty.iloc[:,j] = round((weeklyCasesPerCounty.iloc[:,j]/weeklyCasesPerCounty['population'])*100000,2)

    # sync type with counties as it is used to map choropleth
    weeklyCasesPerCounty['countyFIPS'] = weeklyCasesPerCounty['countyFIPS'].apply(str) 
    weeklyCasesPerCounty['countyFIPS'] = weeklyCasesPerCounty['countyFIPS'].apply(lambda x: x.zfill(5))

    return weeklyCasesPerCounty

@st.cache
def newDeathsCalculations():
    '''
        The function takes the per county stats of deaths and population and returns a dataframe with values of deaths in each county per 100K.
    '''
    dailyDeaths = pd.read_csv(covid_deaths_usafacts)
    dailyDeaths = dailyDeaths.drop(columns = ['State' ,'StateFIPS','County Name', '2020-01-22','2020-01-23', '2020-01-24', '2020-01-25'])
    dailyDeathsTotal = dailyDeaths.groupby('countyFIPS').sum()
    dailyDeathsTotal = dailyDeathsTotal.diff(axis = 1)

    weeklyDeathsPerounty = dailyDeathsTotal.groupby([[i//7 for i in range(0,len(dailyDeathsTotal.columns))]], axis = 1).sum().T
    weeklyDeathsPerounty[weeklyDeathsPerounty<0] = 0
    weeklyDeathsPerounty = weeklyDeathsPerounty.T

    populations = populationsPerCounty[['countyFIPS','population']]
    populations = populations.groupby('countyFIPS').sum()


    weeklyDeathsPerounty = pd.merge(weeklyDeathsPerounty,populations,on=['countyFIPS'])
    weeklyDeathsPerounty = weeklyDeathsPerounty.iloc[1:,:]
    weeklyDeathsPerounty.reset_index(inplace=True)
    
    for j in range(1,108):
       weeklyDeathsPerounty.iloc[:,j] = round((weeklyDeathsPerounty.iloc[:,j]/weeklyDeathsPerounty['population'])*100000,2)

    # sync type with counties as it is used to map choropleth
    weeklyDeathsPerounty['countyFIPS'] = weeklyDeathsPerounty['countyFIPS'].apply(str) 
    weeklyDeathsPerounty['countyFIPS'] = weeklyDeathsPerounty['countyFIPS'].apply(lambda x: x.zfill(5))
    weeklyDeathsPerounty.dropna(inplace=True)

    return weeklyDeathsPerounty


def choroplethGraphForWeek(weeklyData, label,colormap):
    '''
        The function maps the choropleth map with data of a specific week.
    '''
    mapData = pd.DataFrame({'countyFIPS':weeklyData['countyFIPS'],'Cases':weeklyData.iloc[:,1]})
    
    # plotting chrolopleth
    fig = (px.choropleth(mapData, geojson=counties, locations='countyFIPS', color='Cases',
                            color_continuous_scale=colormap,
                            range_color=(mapData.iloc[:,1].min(), mapData.iloc[:,1].max()),
                            scope="usa",
                            labels={'Cases':label}
                            ))
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig


def animate(dataPerWeek, label):

    weeklyDataAll = dataPerWeek.copy(deep=True)
    columns = list(weeklyDataAll.columns[1:107])
    columns = str(columns[i] for i in range(len(columns)))

    weeklyDataAll.columns = weeklyDataAll.columns.astype(str)


    # Melting data in one dataframe to pass to the choropleth function with animation frame as WeekStart.

    meltedWeeklyData = pd.melt(weeklyDataAll[:107], id_vars=['countyFIPS'],var_name="WeekStart", value_name="Cases")
    meltedWeeklyData.drop(meltedWeeklyData.index[meltedWeeklyData['WeekStart'] == 'population'], inplace=True)
    meltedWeeklyData['WeekStart']= meltedWeeklyData['WeekStart'].apply(int)
    meltedWeeklyData.replace([np.inf, -np.inf], np.nan, inplace=True)
    meltedWeeklyData.dropna(inplace=True)
    
    
    # Collecting sample data for each small number of weeks as overall data is crossing the limits of streamlit config.
    slice = meltedWeeklyData.head()
    for i in range(1,30):
        slice = pd.concat([slice, meltedWeeklyData.query("WeekStart=={0}".format(i)).sample(n=5)])
    
    slice['WeekStart'].replace(weekInfo, inplace=True)
    slice.reset_index(drop=True)
    
    
    fig = px.choropleth(slice, geojson=counties, locations='countyFIPS', color='Cases',
                            color_continuous_scale="Viridis",
                            range_color=(slice.iloc[:,2].min(), slice.iloc[:,2].max()),
                            scope="usa",
                            labels={'Cases':label},
                            animation_frame='WeekStart'
                        )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig)



if __name__ == '__main__':

    weeklyDataCases = newCasesCalculations()
    weeklyDataDeaths = newDeathsCalculations()

    st.header("Covid-19 Data Visualization (Jan 2020 - Feb 2022)")
    # Produce a line plot of the weekly new cases of Covid-19 in the USA from the start of the pandemic.
    st.write("Weekly New Cases")
    showWeeklyNewCases = usaWeeklyNewCases()
    chartCases = alt.Chart(showWeeklyNewCases).mark_line().encode(x=alt.X('Date:T', axis=alt.Axis(
        labelAngle=90, labelOverlap="greedy")), y='Total Cases:Q', tooltip=[
        alt.Tooltip("Date", title="Date"),
        alt.Tooltip("Total Cases", title="Total Cases"),])
    st.altair_chart(chartCases, use_container_width=True)  

    # Produce a line plot of the weekly deaths due to Covid-19 in the USA from the start of the pandemic
    st.write("Weekly Deaths")
    showWeeklyDeaths = usaWeeklyDeaths()
    chartDeaths = alt.Chart(showWeeklyDeaths).mark_line().encode(x=alt.X('Date:T', axis=alt.Axis(
        labelAngle=90, labelOverlap="greedy")), y='Total Deaths:Q',tooltip=[
        alt.Tooltip("Date", title="Date"),
        alt.Tooltip("Total Deaths", title="Total Deaths"),])
    st.altair_chart(chartDeaths, use_container_width=True)


    # Have a sider that allows the user to select the week displayed in the two maps.
    #   Moving the one slider should change both maps.
    weekNumber = st.slider('Select a week number?', 0, 106, 0)
    st.write("Week Number: ",weekNumber)
    st.write("Week Start Date: ",weekInfo.iloc[weekNumber])
    
    #  Using Plotly Choropleth map produce a map of the USA displaying for each county the new
    #    cases of covid per 100,000 people in a week
    st.write("New cases per 100K")
    weekData = weeklyDataCases[['countyFIPS',weekNumber]]
    st.plotly_chart(choroplethGraphForWeek(weekData,'New Cases per 100K',"sunset"),use_container_width=True)
    
    # Using Plotly Choropleth map produce a map of the USA displaying for each county the
    #    covid deaths per 100,000 people in a week.
    st.write("Deaths per 100K")
    weekDataDeaths=  weeklyDataDeaths[['countyFIPS',weekNumber]]
    st.plotly_chart(choroplethGraphForWeek(weekDataDeaths,'Deaths per 100K',"portland"),use_container_width=True)

    st.write("Animation")
    if st.button("Start"):
        with st.spinner('Wait for it...'):
            animate(weeklyDataCases,'New Cases per 100K')
            animate(weeklyDataDeaths,'Deaths per 100K')
            time.sleep(1)
        st.success('Done!')
        
        