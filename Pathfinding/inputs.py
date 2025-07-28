import Parameter as para
if para.network_name == 'Anaheim':
    import Anaheim_OD_Demand as OD_Demand
else:
    import OD_Demand
import numpy as np

# Initialize the supply and demand
PersonList = []
VehicleList = []
PersonMaster = []
PersonU = []
# A list of persons that requested a vehicle but not matched yet
PersonRequest = []
# A list of persons who are matched but not yet picked
PersonMatch = []
# A list of persons who are picked but not dropped
PersonPicked = []
# A list of persons who are served
PersonServed = []
# A list of persons who are not served, i.e., Time exceeds maxpickuptime
PersonReject=[]
# A list of vehicles which are idle (no match), includes both "I" and "R"
VehEmpty = []
# A list of vehicles which are enroute to pick up
VehPick = []
# A list of vehicles which are enroute to drop off
VehDrop = []
# An additional list for eligible vehicles for pickup at each time step
VehAvbl = []
# Total number of requests made
total_demand = 0

def init_demand_supply():
    np.random.seed(para.seed)
    global PersonList,VehicleList
    PersonList,VehicleList = OD_Demand.genRequestsandFleet()
    # Reduce number of vehicles for now
    VehicleList=VehicleList[0:para.Fleet_size]

    # Set up a series of lists to store vehicles and persons and they will change dynamically

    # A list of all Persons objects with status as 'U'
    global PersonMaster,PersonU
    PersonMaster = [p for p in PersonList if p.requesttime < para.SimTime]
    # Slice demand randomly from PersonMaster
    PersonU=[]

    if len(PersonMaster) > para.Demand_size:
        PersonU=np.random.choice(PersonMaster,size=para.Demand_size,replace=False)
        PersonU = PersonU.tolist()
    else:
        PersonU=PersonMaster
    global total_demand
    total_demand = len(PersonU) # Total number of requests in the simulation period
    # A list of persons that requested a vehicle but not matched yet
    global PersonReject,PersonRequest,PersonMatch,PersonPicked,PersonServed
    PersonRequest = []
    # A list of persons who are matched but not yet picked
    PersonMatch = []
    # A list of persons who are picked but not dropped
    PersonPicked = []
    # A list of persons who are served
    PersonServed = []
    # A list of persons who are not served, i.e., Time exceeds maxpickuptime
    PersonReject=[]
    # A list of vehicles which are idle (no match), includes both "I" and "R"
    global VehEmpty,VehPick,VehDrop,VehAvbl
    VehEmpty = [veh for veh in VehicleList]
    # A list of vehicles which are enroute to pick up
    VehPick = []
    # A list of vehicles which are enroute to drop off
    VehDrop = []
    # An additional list for eligible vehicles for pickup at each time step
    VehAvbl = []
