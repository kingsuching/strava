import os.path
import sys
import pandas as pd
import numpy as np
from stravalib import Client
import webbrowser
import units
from Pace import Pace
from units import *
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.io as pio
import webbrowser
from functions import *
from tqdm import tqdm
import pickle
import warnings
from units import *
warnings.filterwarnings('ignore')

def setUpClient(client_id, client_secret):
    client = Client()
    if os.path.exists(PKL):
        with open(PKL, 'rb') as f:
            client = pickle.load(f)
            try:
                client.get_athlete()
                print('Client works')
                return client
            except:
                pass

    try:
        authorize_url = client.authorization_url(client_id=client_id,
                                             redirect_uri='http://localhost:1127/authorized',
                                             scope=['read_all', 'profile:read_all', 'activity:read_all'])
    except:
        print('Invalid client credentials.txt')
        return

    webbrowser.open(authorize_url)
    code = input("Code: ")
    tokenStuff = client.exchange_code_for_token(client_id=client_id, client_secret=client_secret, code=code)

    access = tokenStuff['access_token']
    client.access_token = access
    print('Client access token assigned')
    with open(PKL, 'wb') as f:
        pickle.dump(client, f)

    return client


def getActivities(client):
    activities = client.get_activities()
    activity_list = []
    for activity in activities:
        activity_dict = {
            'id': activity.id,
            'name': activity.name,
            'start_date': activity.start_date,
            'distance': activity.distance,  # Convert distance to numeric (meters)
            'moving_time': activity.moving_time,  # Convert to seconds
            'elapsed_time': activity.elapsed_time,  # Convert to seconds
            'total_elevation_gain': activity.total_elevation_gain,
            'type': activity.type,
            'average_speed': activity.average_speed if activity.average_speed else None,  # Convert to numeric
            'max_speed': activity.max_speed if activity.max_speed else None,  # Convert to numeric
            'average_heartrate': activity.average_heartrate,
            'max_heartrate': activity.max_heartrate,
        }
        activity_list.append(activity_dict)
    myActivities = pd.DataFrame(activity_list)
    myActivities = myActivities[myActivities['type'].astype(str).apply(lambda x: 'Run' in x)]
    myActivities = myActivities.reset_index(drop=True)
    myActivities.to_csv('myActivities.csv')
    return myActivities


def get_activity_streams(client, activity_id, resolution='high'):
    """
    Fetch heart rate, pace (velocity), and elevation streams for a given activity ID.
    """
    streams = client.get_activity_streams(
        activity_id,
        types=['heartrate', 'velocity_smooth', 'altitude', 'time', 'distance'],
        resolution=resolution,
    )

    heart_rate = streams['heartrate'].data if 'heartrate' in streams else None
    velocity = streams['velocity_smooth'].data if 'velocity_smooth' in streams else None
    elevation = streams['altitude'].data if 'altitude' in streams else None
    time_index = streams['time'].data if 'time' in streams else None
    distance_index = streams['distance'].data if 'distance' in streams else None
    return heart_rate, velocity, elevation, time_index, distance_index


def makePlots(client, rowId):
    myActivities = getActivities(client)
    things = myActivities.iloc[rowId]
    activityId = things['id']
    name = things['name']
    print(f'Looking at ', name)
    hr, pace, elevation, timeIdx, distanceIdx = get_activity_streams(client, activityId, resolution='high')

    # Convert to imperial system
    elevation = [int(round(metersToFeet(elev), 0)) for elev in elevation]
    timeIdx = [i / 60 for i in timeIdx]
    distanceIdx = [round(metersToMiles(i), 2) for i in distanceIdx]

    pace = [Pace.from_mps(v) for v in pace if v > 0]

    """Pace Plots"""
    # Time
    diff = len(timeIdx) - len(pace)
    average = sum(pace) / len(pace)
    x = pace + [average] * diff

    stuff = numericPlot('Pace', x, timeIdx, distanceIdx)
    myPaces = stuff['Pace']
    index = stuff['Time']

    y_values = [pace.time/60 for pace in myPaces]
    labels = [str(pace) for pace in myPaces]

    # Create the plot
    fig = go.Figure(data=go.Scatter(
        x=index,
        y=y_values,
        mode='markers+lines',
        text=[f"{str(pace)}, {hr[i]} BPM" for i, pace in enumerate(myPaces)],
        marker=dict(color=hr, colorscale='solar', colorbar=dict(title='Heart Rate'))
    ))

    fig.update_layout(
        title='Pace Plot',
        xaxis_title='Time',
        yaxis_title='Pace (min/mi)'
    )
    requiredFolders = os.path.join(units.PLOT_FOLDER, name)
    if not os.path.exists(requiredFolders):
        os.makedirs(requiredFolders)

    pio.write_html(fig, os.path.join(requiredFolders, f'{name}_pace_time{units.EXTENSION}'))

    # Distance
    index = stuff['Distance']
    y_values = [pace.time / 60 for pace in myPaces]
    labels = [str(pace) for pace in myPaces]
    fig = go.Figure(data=go.Scatter(
        x=index,
        y=y_values,
        mode='markers+lines',
        text=labels
    ))
    fig.update_layout(
        title='Pace Plot',
        xaxis_title='Distance (mi)',
        yaxis_title='Pace (min/mi)'
    )

    pio.write_html(fig, os.path.join(requiredFolders, f'{name}_pace_distance{units.EXTENSION}'))

    """ HR """
    # Time

    zones = client.get_athlete_zones().dict()
    values = zones['heart_rate']['zones'][:-1]
    base = 'HR'
    data = numericPlot(base, hr, timeIdx, distanceIdx)
    try:
        data['Zone']
    except:
        data['Zone'] = data[base].apply(lambda x: getZone(values, x))

    fig = go.Figure()
    zone_colors = {
        'Zone 1': 'green',
        'Zone 2': 'yellow',
        'Zone 3': 'orange',
        'Zone 4': 'red'
    }

    # Create the figure
    fig = go.Figure()

    # Add traces for each zone
    for zone in data['Zone'].unique():
        zone_data = data[data['Zone'] == zone]
        fig.add_trace(go.Scatter(
            x=zone_data['Time'],
            y=zone_data['HR'],
            mode='lines',
            name=zone,
            line=dict(color=zone_colors[zone], width=1)  # Assign color based on zone
        ))

    fig.update_layout(
        title=f'{base}: {name}',
        xaxis_title='Time',
        yaxis_title=base,
        autosize=False,
        width=800,
        height=600
    )

    pio.write_html(fig, os.path.join(requiredFolders, f'{name}_hr_time{units.EXTENSION}'))

    # Distance
    fig = go.Figure()

    # Add traces for each zone using Distance as the x-axis
    for zone in data['Zone'].unique():
        zone_data = data[data['Zone'] == zone]
        fig.add_trace(go.Scatter(
            x=zone_data['Distance'],
            y=zone_data['HR'],
            mode='lines',
            name=zone,
            line=dict(color=zone_colors[zone], width=1)  # Assign color based on zone
        ))

    fig.update_layout(
        title=f'{base}: {name}',
        xaxis_title='Distance',
        yaxis_title=base,
        autosize=False,
        width=800,
        height=600
    )

    pio.write_html(fig, os.path.join(requiredFolders, f'{name}_hr_distance{units.EXTENSION}'))

    if not os.path.exists('analysis'):
        os.makedirs('analysis')

    requiredAnalysisFolders = os.path.join(units.ANALYSIS_FOLDER, name)
    if not os.path.exists(requiredAnalysisFolders):
        os.makedirs(requiredAnalysisFolders)
    analysisFile = os.path.join(requiredAnalysisFolders, f'{name}_analysis.txt')

    open(analysisFile, 'w').close()
    with open(analysisFile, 'w') as f:
        data['Pace'] = x

        grouped = data.groupby('Zone').mean()
        minimums = data.groupby('Zone').min()
        maximums = data.groupby('Zone').max()
        minimums['Pace'] = minimums['Pace'].apply(lambda x: x.time).apply(lambda j: Pace.fromSeconds(j))
        maximums['Pace'] = maximums['Pace'].apply(lambda x: x.time).apply(lambda j: Pace.fromSeconds(j))
        for z in grouped.index:
            item = f'{z} Average Pace: {Pace.fromSeconds(grouped.loc[z, "Pace"])}'
            f.write(item + '\n')
        f.write('\n\n')
        for z in minimums.index:
            item = f'{z} Range: {minimums.loc[z, "Pace"]} to {maximums.loc[z, "Pace"]}'
            f.write(item + '\n')

    """ Pace-HR Boxplot"""

    data['PaceTime'] = data['Pace'].apply(lambda x: x.time/60)
    data['PaceStr'] = data['Pace'].astype(str)

    # Apply the outlier exclusion function to each zone
    filtered_data = pd.concat([
        exclude_outliers(data[data['Zone'] == zone], 'PaceTime')
        for zone in data['Zone'].unique()
    ])

    # Create the boxplot
    fig = go.Figure()
    for zone in filtered_data['Zone'].unique():
        zone_data = filtered_data[filtered_data['Zone'] == zone]
        fig.add_trace(go.Box(
            y=zone_data['PaceTime'],  # Numeric pace values for the boxplot
            x=[zone] * len(zone_data),  # Use the zone as the x-axis category
            name=zone,  # Name of the trace (zone)
            text=zone_data['PaceStr'],  # Tooltip labels (string representation of pace)
            hovertemplate='Zone: %{x}<br>Pace: %{text}<extra></extra>',  # Custom tooltip format
            boxmean=True  # Show mean as a dashed line
        ))

    fig.update_layout(
        title='Pace Distribution by Heart Rate Zone (Outliers Excluded)',
        xaxis_title='Heart Rate Zone',
        yaxis_title='Pace (min/mi)',
        autosize=False,
        width=800,
        height=600
    )

    pio.write_html(fig, os.path.join(requiredFolders, f'{name}_pace_hr_boxplot{units.EXTENSION}'))

    x = data[['HR', 'PaceTime']]
    correlation = x.corr()['HR']['PaceTime']
    with open(analysisFile, 'a') as a:
        a.write(f'\n\nCorrelation: {float(correlation)}')

def getZone(values, hr):
    n = len(values)
    assert hr >= 0, 'HR must be non-negative'
    for i in range(n):
        bucket = values[i]
        if bucket['min'] <= hr <= bucket['max']:
            return f'Zone {i+1}'
    raise ValueError(f'HR {hr} is out of range')

def numericPlot(base, items, timeIdx, distanceIdx):
    data = pd.DataFrame({
        base: items,
        'Time': timeIdx,
        'Distance': distanceIdx
    })
    return data

def exclude_outliers(df, column):
    q1 = df[column].quantile(0.25)  # First quartile (25th percentile)
    q3 = df[column].quantile(0.75)  # Third quartile (75th percentile)
    iqr = q3-q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    return df[(df[column] >= lower_fence) & (df[column] <= upper_fence)]  # Filter data within fences


if __name__ == '__main__':
    if len(sys.argv) > 1:
        rowId = int(sys.argv[1])-1
    else:
        rowId = 0

    with open('credentials.txt', 'r') as credentials:
        lines = credentials.readlines()
        missingCount = 0
        try:
            CLIENT_ID = lines[0].split(' = ')[1]
        except:
            print('Missing Client ID')
            missingCount += 1

        try:
            CLIENT_SECRET = lines[1].split(' = ')[1]
        except:
            print('Missing Client Secret')
            missingCount += 1

        assert missingCount == 0, 'Improper credentials'

    my_client = setUpClient(CLIENT_ID, CLIENT_SECRET)
    makePlots(my_client, rowId)
