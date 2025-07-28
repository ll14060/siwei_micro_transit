# Person Class. All locations are labelled as Node id (int)
import Parameter



class Person:

    # A Person will be initiated with id, pickupLoc, droploc, and request_time
    def __init__(self, person_id, pickLoc, dropLoc, request_time, groupSize):
        # Person id
        self.person_id = person_id
        # Pickup Location
        self.pickLoc = pickLoc
        # Dropoff Location
        self.dropLoc = dropLoc
        # Request time, request time also works as a pop-time
        self.requesttime = request_time
        # Time the person estimated to be picked up
        self.pickTime = None
        # Time the person estimated to be dropped off
        self.dropTime = None
        # We will also set a latest pickup time and a latest dropoff time as time windows
        # Now the latest pickup time is 10 minutes after request time as set in Parameters
        self.pickTimeLatest = self.requesttime + Parameter.maxPickUpWaitTime
        # Now the latest dropoff time is infinity
        self.dropTimeLatest = 99999999
        # Waiting time after request and in-vehicle time could be calculated
        # Size of the group
        self.size = groupSize
        # A Person could have 5 status, "Request",'Matched','Picked', and "Served","REject" the default setting is 'U'
        self.status = 'U'
        # The vehicle to serve the person (a vehicle obj, could be a vehicle id if needed)
        self.vehicle = None
        # A trajectory for person to record all nodes the person travelled (node, time)
        # Trajectory is always empty until the person is dropped
        self.trajectory = []
        # Sequence of dropoff when stay in a vehicle, need to update after new pickup happens
        # It is also the index the Person Obj will stay in Vehicle.person
        self.dropSeq = 0
        # Whether his/her trip is shared
        if self.size > 1:
            self.tripShare = True
        else:
            self.tripShare = False

    # This part may not needed
    # # A function to update Person attributes after pickup, it will be updated after updating vehicle
    def updatePersonAfterPick(self):
        self.status = 'P'
        from inputs import PersonPicked,PersonMatch
        PersonPicked.append(self)
        PersonMatch.remove(self)
        # # Pick up time will not change once decided after routing module
        # # Drop off Location will be update when somebody shares the vehicle after routing module
        # # Update Status:
        # self.status = 'P'
        # self.vehicle = vehicle
        # # Person path will be updated at once at drop-off
        # self.dropSeq = vehicle.personIn.index(self)

        return

    # A function to update Person attributes after drop, it will be updated after updating vehicle
    def updatePersonAfterDrop(self, vehicle):
        # Pick up time will not change once decided after routing module
        # Drop off Location will be update when somebody shares the vehicle after routing module
        # Update Status:
        self.status = 'S'
        # Add person to PersonServed
        from inputs import PersonPicked, PersonServed
        PersonServed.append(self)
        # Remove from Person Picked list
        PersonPicked.remove(self)


        # The trajectory is the vehicle trajectory in between (pickLoc, pickTime), (dropLoc, dropTime)
        checkPoint1 = (self.pickLoc, round(self.pickTime,1))
        checkPoint2 = (self.dropLoc, round(self.dropTime,1))
        # Debug, vehicle trajectory time precision
        vehicle.trajectory = [(p,round(t,1)) for p,t in vehicle.trajectory]
        # Find the index of pickup and drop off tuple in vehicle trajectory
        index1 = vehicle.trajectory.index(checkPoint1)
        index2 = vehicle.trajectory.index(checkPoint2)
        # Trajectory is the trajectory in between from vehicle trajectory
        self.trajectory = vehicle.trajectory[index1:(index2 + 1)]

        return


# A function to update Person after giving a match and route
# The routing module will update vehicle fist, person will rely on vehicle for updating
def updatePersonAfterMatch(costObject):
    # The vehicle to serve is vehTemp
    vehTemp = costObject.vehicle

    # Create a list of person to update
    for (p, stat, timetemp) in costObject.taskTime:
        # If the person has not been picked
        if stat == 'P':
            # Update pickup time
            p.pickTime = timetemp
            # update status
            p.status = 'M'
            # Update service vehicle
            p.vehicle = vehTemp
        # Regardless of pick
        elif stat == 'D':
            p.dropTime = timetemp

    return


def updatePersonTripShare(vehicle):
    for p in vehicle.personIn:
        p.shareTrip = True

    return
