# This module generates demand for Sioux Falls Network
# It reads from a csv file
import pandas as pd
import numpy as np
import Person
import Vehicle
import os
import Parameter as para

# Random Seed
np.random.seed(para.seed)

DemandFileFolder = os.getcwd()
Datapath=DemandFileFolder+'\SiouxFallsODDemand.csv'
pwd=os.getcwd()
Datapath=pwd+'\\SiouxFalls\\SiouxFallsODDemand.csv'
data = pd.read_csv(Datapath, header=None)
dataarray = np.asarray(data)
dataarray = np.reshape(dataarray,(1,166*6))[0]
newlist = list(dataarray)
demandList = []
for i in newlist:
    if i != ' ' and i > -1:
        demandList.append(i)
    # else:
    #     if i > -1:
    #         demandList.append(i)
demandDict = {}
count = 0
for i in range(1, 25, 1):
    for j in range(1, 25, 1):
        demandDict.update({(str(i), str(j)):demandList[count]})
        count += 1
# print(demandDict)
demandTable = np.zeros((24,24))
# for i in range(24):
#     for j in range(24):
#         demandTable[i,j] = demandDict[i+1, j+1]
# dataframe = pd.DataFrame(demandTable)
# dataframe.to_csv('SiouxFallsDemandConverted.csv')
# print(dataframe)


# Time period is the 0,30,60,90,120...
def genDemand(demandDict, SimTime, division, timeperiod):
    PersonList = []
    PersonidCount = 0
    for i,j in demandDict.keys():
        totalTrips = int(np.ceil(demandDict[i, j]/division))
        if totalTrips != 0:
            for t in range(totalTrips):
                requestTime = timeperiod+np.random.random()*SimTime
                NewPerson = Person.Person(PersonidCount, i, j, requestTime, 1)
                PersonidCount += 1
                PersonList.append((NewPerson))

    for p in PersonList:
        o = int(p.pickLoc)
        d = int(p.dropLoc)
        demandTable[ o-1, d-1] += 1

    return demandTable, PersonList


demandTable1,PersonList1 = genDemand(demandDict, 30, 1000, 0)
demandTable2,PersonList2 = genDemand(demandDict, 30, 600, 30)
demandTable3,PersonList3 = genDemand(demandDict, 30, 600, 60)
demandTable4,PersonList4 = genDemand(demandDict, 30, 1000,90)

# for p in PersonList1:
#     print(type(p.dropLoc))
# Combine person lists
PersonList = PersonList1 + PersonList2 + PersonList3 + PersonList4

# print(len(PersonList2))
# print(sum(demandTable))
# print(demandTable)

# Initiate the vehicles
VehicleList = []
for i in range(para.Fleet_size):
    NewVehicle = Vehicle.Vehicle(i, str(np.random.randint(1, 25)), capacity=3)
    VehicleList.append(NewVehicle)
