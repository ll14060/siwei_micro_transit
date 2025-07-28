# This module generates demand for Sioux Falls Network
# It reads from a csv file
import pandas as pd
import numpy as np
import Person
import Vehicle
import math
import Parameter as para
from read_network import odtable_time,no_of_time_periods,SPSkims,number_of_nodes,origins,odtable
# Random Seed







# Time period is 0,1,2,3,4... where each time period is a 30 minute time window
def genDemand(timeperiod):
    np.random.seed(para.seed)
    PersonList = []
    # Iterate over odtable rows for the required time period
    for o,col in odtable_time[timeperiod].iterrows():
        for d in odtable_time[timeperiod].columns:
            if o == d:
                continue
            # Avoid trips that are shorter than 5 minutes

            if SPSkims[(str(o),str(d))][0] <= 5:
                continue
            totalTrips = col[d]
            # Round up all trip values >= 0.3
            if totalTrips >= 0.3:
                for t in range(math.ceil(totalTrips)):
                    try:
                        genDemand.personidCount += 1
                    except AttributeError:
                        genDemand.personidCount = 1
                    if para.SimTime == 180:
                        requestTime = round(30 * (timeperiod + np.random.random()), 1)
                    # 24 hour simulation
                    else:
                        # AM period: 4 hours (0600 - 1000)
                        if timeperiod == 0:
                            requestTime = round(240 * np.random.random(), 1)
                        # MID Day (1000 - 1500)
                        elif timeperiod == 1:
                            requestTime = round(240 + 300 * np.random.random(), 1)
                        # PM (1500 - 1900)
                        elif timeperiod == 2:
                            requestTime = round(540 + 240 * np.random.random(), 1)
                        # NIGHT (1900 - 0300)
                        elif timeperiod == 3:
                            requestTime = round(780 + 480 * np.random.random(), 1)
                        # EARLY (0300 - 0600)
                        elif timeperiod == 4:
                            requestTime = round(1260 + 180 * np.random.random(), 1)

                    NewPerson = Person.Person(genDemand.personidCount, str(o), str(d), requestTime, 1)
                    PersonList.append((NewPerson))




    print ("NO of requests generated in time period ",timeperiod, " is ",len(PersonList))
    # no_of_hours = [4,5,4,8,3]
    # print("Req generation rate (req/hr): ",len(PersonList)/no_of_hours[timeperiod])

    return PersonList
# Static function id variable
# For unique ids





# Function that returns request and vehicle object lists
def genRequestsandFleet():
    np.random.seed(para.seed)
    PersonList = []
    [PersonList.extend(genDemand(t)) for t in range(no_of_time_periods)]
    print("No of shared ride requests generated ", len(PersonList))
    # Initiate the vehicles
    VehicleList = []
    for i in range(para.Fleet_size):
        # Vehicles randomly distributed among all nodes in the network
        # Could change to include more zones
        # Choose a random vehicle initial location
        veh_loc = np.random.choice(origins, size=1)
        NewVehicle = Vehicle.Vehicle(i, str(veh_loc[0]), capacity=3)
        VehicleList.append(NewVehicle)

    return PersonList,VehicleList




# Test Demand Gen


if __name__ == '__main__':
    genRequestsandFleet()






