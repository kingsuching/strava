import os
import pickle
import webbrowser
import pandas as pd
from stravalib import Client
from units import PKL


def metersToFeet(meters):
    return meters * 3.28084

def metersToMiles(meters):
    return meters / 1609.34

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
    code = code.strip()
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