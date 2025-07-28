# Vehicle Class, All locations are labelled as Node id (int)
# File Name Vehicle
import Parameter as para


class Vehicle:
    def __init__(self, vid, currentLoc, capacity):
        # Vehicle id
        self.id = vid
        # vehicle Location it now at
        self.currentLoc = currentLoc
        # The node the vehicle is moving TOWARD, labelled as node id, not necessary a pick/drop node
        self.nextNode = self.currentLoc
        # vehicle moving toward location, MUST Be a pickup or dropoff point
        self.nextLoc = None
        # vehicle relocating location
        self.reloc = None
        # Vehicle  estimated arrive time for next NODE
        self.timeNextNode = None
        # Vehicle estimating arrive time for next location
        self.timeNextLoc = None
        # A vehicle could have 4 status,
        # "Idle", "Pick"(enroute to pickup), "Drop", "Relocate"
        self.status = 'I'
        # Capacity of a vehicle
        self.cap = capacity
        # Occupancy is the number of passengers in vehicle, the occupancy cannot be larger than 3
        self.occu = 0
        # Vehicle Future Tasks and sequence, format, a list of [(obj, flag)] e.g. [(Person Obj,'D')]
        self.futureTasks = []
        # Stationary time (Time the vehicle is not moving)
        self.stationary_time = 0
        # Passengers in vehicle, a list of person objects
        self.personIn = []
        # A list of persons served by this vehicle
        self.personServed = []
        # The number of Passenger to be picked up, will not be update
        self.toPick = []
        # toPick and toDrop are both updated after match/routing, so person matched but not
        # physically picked is also included
        # Passenger to be dropoff in sequence, will be person objects
        self.toDrop = []
        # The past trajectory is a list of tuples (Node, time)
        self.trajectory = [(currentLoc, 0)]
        # The future path a list of tuples (Node, time)
        self.path = []
        # The cumulative miles
        self.vmt = 0
        self.vht = 0
        # Idle time refers to the time vehicle status = 'I' (No task at all)
        # Idle time start is the time step when vehicle flag is 'I'
        self.idlTimeStart = 0
        # Idle Time Once, this is the idle time from a 'I' to next time step it receives a task
        self.idlTimeOneCum = 0
        # Idle Time Cumulative
        self.idlTimeCum = 0
        # Idle miles
        self.idlemiles = 0
        # Empty time refers to the time vehicle is empty (could be enroute to pick)
        self.emptyTimeCum = 0
        self.emptyTimeStart = 0
        self.emptyTimeOneCum = 0
        # Share is the flag to show whether a vehicle is shared, default is False
        self.share = False
        # Share start time
        self.shareStartTime = None
        # Share accumulative time
        self.shareTimeTotal = 0

    # Function to find the number of passengers to pick and to drop from futureTasks list
    # Returns topickcount,todropcount
    def findToPickandDropCount(self):
        topPickist = [task for task in self.futureTasks if task[1] == 'P']
        topDroplist = [task for task in self.futureTasks if task[1] == 'D']
        # Return number of passengers to pick and to drop
        return len(topPickist), len(topDroplist)

    # The below function is to update vehicle attributes after a pickup
    # input argument includes new person to drop (object), new Path (list of tuples)
    def updateVehAfterPick(self,current_time):

        # Identify the person to pick/drop
        personServingNow = self.futureTasks[0][0]
        # Update Pickup Person attributes
        personServingNow.updatePersonAfterPick()
        # Create a check point to see which node the vehicle arrives for pick up
        checkPoint = (self.nextLoc, self.timeNextLoc)
        # Find the index of that node in path, and attach the (N, t) before that to trajectory
        # Update newPath to be the path after the checkpoint
        index = self.path.index(checkPoint)
        # Update trajectory
        self.trajectory = self.trajectory + self.path[0:(index + 1)]
        # Update Path
        self.path = self.path[(index + 1):]
        # PersonIn list append picked persons
        self.personIn.append(personServingNow)
        # Update person to pick
        self.futureTasks.remove((personServingNow, 'P'))
        with open(para.output_timestep_log, 'a') as op_file:
            print("Person ",personServingNow.person_id," picked by Veh-",self.id,file=op_file)

        # Update idelTime
        # first update idleTimeOneCum (if occu "was" zero, not updated yet)
        if self.occu == 0:
            self.emptyTimeOneCum = current_time - self.emptyTimeStart
            self.emptyTimeCum += self.emptyTimeOneCum
            self.emptyTimeOneCum =0

        # update status, occupancy, and share time
        self.occu += personServingNow.size
        # Check assignment error
        if self.occu > self.cap: # Check error
            print("Assignment Error: Occupancy more than capacity")
            # When more than 2 passengers in vehicle
        if self.occu >= 2:
            # Flip the flag for share
            self.share = True
            # Share start time was from the pickup point
            self.shareStartTime = self.timeNextLoc
        # Check whether there is another pickup
        if self.futureTasks[0][1] == 'P':
            personToServeNext = self.futureTasks[0][0]
            # if the next task is 'P', vehicle status unchanged
            # Current location is the location the vehicle just arrived
            self.currentLoc = self.trajectory[-1][0]
            # nextNode will be the first node in future path
            if len(self.path) > 0:
                self.nextNode = self.path[0][0]
                self.timeNextNode = self.path[0][1]
            else:
                self.nextNode = None
                self.timeNextLoc = None
            # update next location and time, Note: next Location MUST be a pick/drop point

            self.nextLoc = personToServeNext.pickLoc
            self.timeNextLoc = personToServeNext.pickTime
            # If next person is to be picked from same location
            # Then complete that action in the same time step
            # if abs(self.timeNextLoc - current_time) < 0.1:
            if self.nextLoc == self.currentLoc:
                with open(para.output_timestep_log, 'a') as op_file:
                    print("Veh- ", self.id, " after drop-off next person ", personToServeNext.person_id,
                        " has same pickup loc and time ", file=op_file)
                # Check if the same location at same time task has been reflected in the path
                # In some cases, the (location,time) has not been repeated in the path
                # To reflect events happening at the same location at the same time
                # So in such a case, make changes to the path[0] object
                if self.nextNode != self.currentLoc:
                    # Insert current node,time to the beginning of the path list
                    self.path = [(self.currentLoc, self.timeNextLoc)] + self.path
                self.nextNode = self.path[0][0]
                self.timeNextNode = self.path[0][1]
                self.updateVehAfterPick(current_time)

        else: # else means next task is drop
            personToServeNext = self.futureTasks[0][0]
            # Vehicle status changed to "D"
            self.status = 'D'
            # Current location is the location the vehicle just arrived
            self.currentLoc = self.trajectory[-1][0]
            # nextNode will be the first node in future path
            if len(self.path) > 0:
                self.nextNode = self.path[0][0]
                self.timeNextNode = self.path[0][1]
            else:
                self.nextNode = None
                self.timeNextLoc = None
            # update next location and time, Note: next Location MUST be a pick/drop point
            self.nextLoc = personToServeNext.dropLoc
            self.timeNextLoc = personToServeNext.dropTime
            # If the next person is to be dropped at the same location at current time
            # Then drop off current person as well in the current time step
            # if abs(self.timeNextLoc - current_time) < 0.1:
            if self.nextLoc == self.currentLoc:
                with open(para.output_timestep_log, 'a') as op_file:
                    print("Veh- ", self.id, " after drop-off next person ", personToServeNext.person_id,
                          " has same drop off loc and time ", file=op_file)
                # Check if the same location at same time task has been reflected in the path
                # In some cases, the (location,time) has not been repeated in the path
                # To reflect events happening at the same location at the same time
                # So in such a case, make changes to the path[0] object
                if self.nextNode != self.currentLoc:
                    # Insert current node,time to the beginning of the path list
                    self.path = [(self.currentLoc, self.timeNextLoc)] + self.path
                self.nextNode = self.path[0][0]
                self.timeNextNode = self.path[0][1]
                self.updateVehAfterDrop(current_time)

        return

    # The following function updates vehicle information after some time (not an event)
    # This function must be put after Pick/drop event are checked
    # It may be mainly used for D and relocating vehicles
    def updateVehAfterTime(self, currentime):
        # If vehicle is relocating, keep track of idletime
        # if self.status == 'R':
        #     self.idlTimeOneCum = currentime - self.idlTimeStart
        # Check whether the first node in path has been passed
        # Proposed time <= currentime, means arrived at the first node of path
        debug = 0
        if self.path[0][1] <= currentime:
            # If vehicle has been at the same location as previous time step, update stationary time
            if self.currentLoc == self.nextNode and self.status == 'R':
                self.stationary_time += para.TimeStep
            # Update curentLoc
            self.currentLoc = self.path[0][0]
            # If vehicle is relocating and has reached node '10', which is the current reloc destination
            # Then remain at the current node for the next time step
            if self.status == 'R' and self.currentLoc == self.reloc:
                self.path.append((self.currentLoc,currentime+para.TimeStep))
            # Update nextNode
            self.nextNode =self.path[1][0]
            # Update next node time
            self.timeNextNode = self.path[1][1]
            # Update trajectory to append all nodes travelled
            self.trajectory = self.trajectory + [self.path[0]]
            # Delete nodes travelled from future path
            self.path = self.path[1:]

        return

    def updateVehAfterDrop(self,current_time):

        personServingNow = self.futureTasks[0][0]
        # Create a check point to see which node the vehicle arrived for drop
        # checkPoint = (self.nextLoc, self.timeNextLoc)
        # checkPoint = (personServingNow.dropLoc, personServingNow.dropTime)
        # # Debug: Check if passenger is at the correct location at the right time
        # if personServingNow.dropLoc == self.nextLoc:
        #     print('Yes, right location')
        # else:
        #     print('Wrong Location')
        # Find the index of that node in path, and attach the (N, t) before that to trajectory
        # Update newPath to be the path after the checkpoint
        # index = self.path.index(checkPoint)
        # Update trajectory
        # self.trajectory = self.trajectory + self.path[0:(index + 1)]
        self.trajectory = self.trajectory + [self.path[0]]

        # Update Path
        self.path = self.path[1:]

        # Update served passengers
        self.personServed.append(personServingNow)
        # Update person in-vehicle, insert the person to correct sequence
        self.personIn.remove(personServingNow)
        # Update future task list
        self.futureTasks.remove((personServingNow, 'D'))

        # Update the status of the Person just dropped off now
        personServingNow.updatePersonAfterDrop(self)

        with open(para.output_timestep_log, 'a') as op_file:
            print("Person ",personServingNow.person_id," dropped by Veh-",self.id,file=op_file)

        # Update Occupancy and status
        self.occu -= personServingNow.size

        # Update empty time, start the empty time timer
        if self.occu == 0:
            self.emptyTimeStart = self.timeNextLoc
        # Update share information
        if self.occu == 1:
            # flip share flag, update share information
            self.share = False
            self.shareTimeTotal += (self.timeNextLoc - self.shareStartTime)
            self.shareStartTime = None

        # We have two cases here, one is non-idle after drop, another is idle
        # Case 1: Idle case
        if len(self.futureTasks) == 0:
            # Start the idle status timer
            self.idlTimeStart = self.timeNextLoc
            # Set the attributes to default values
            # Current Loc will be the location the vehicle is at
            self.currentLoc = self.trajectory[-1][0]
            # Next Node will be the same as current loc
            self.nextNode = self.currentLoc
            # time next node will be default
            self.timeNextNode = None
            self.nextLoc = None
            self.timeNextLoc = None
            self.status = 'I'
        # Case 2: Non Idle:
        # 2.1 No Pickup, have drop off
        else: # As drop
            if self.futureTasks[0][1] == 'D':
                self.status = 'D'
                personToServe = self.futureTasks[0][0]
                # Status remains at 'D'
                # Update current location, will be the node just arrived
                self.currentLoc = self.trajectory[-1][0]
                # Update next Node
                if len(self.path) > 0:
                    self.nextNode = self.path[0][0]
                    self.timeNextNode = self.path[0][1]
                else:
                    self.nextNode = None
                    self.timeNextLoc = None
                # update next location and time, Note: next Location MUST be a pick/drop point
                self.nextLoc = personToServe.dropLoc
                self.timeNextLoc = personToServe.dropTime
                # If the next person is to be dropped at the same location at current time
                # Then drop off current person as well in the current time step
                # if abs(self.timeNextLoc - current_time) < 0.1:
                if self.nextLoc == self.currentLoc:
                    with open(para.output_timestep_log,'a') as op_file:
                        print ("Veh- ",self.id," after drop-off next person ",personToServe.person_id," has same drop off loc and time ", file=op_file)
                    # Check if the same location at same time task has been reflected in the path
                    # In some cases, the (location,time) has not been repeated in the path
                    # To reflect events happening at the same location at the same time
                    # So in such a case, make changes to the path[0] object
                    if self.nextNode != self.currentLoc:
                        # Insert current node,time to the beginning of the path list
                        self.path = [(self.currentLoc,self.timeNextLoc)] + self.path
                    self.nextNode = self.path[0][0]
                    self.timeNextNode = self.path[0][1]
                    self.updateVehAfterDrop(current_time)

            # 2.2 No Drop off, pickup only
            elif self.futureTasks[0][1] == 'P': # As Pick
                personToServe = self.futureTasks[0][0]
                # Vehicle status changes to 'P'
                self.status = 'P'
                # Update current location, will be the node just arrived
                self.currentLoc = self.trajectory[-1][0]
                # Update next Node
                if len(self.path) > 0:
                    self.nextNode = self.path[0][0]
                    self.timeNextNode = self.path[0][1]
                else:
                    self.nextNode = None
                    self.timeNextLoc = None
                # update next location and time, Note: next Location MUST be a pick/drop point
                self.nextLoc = personToServe.pickLoc
                self.timeNextLoc = personToServe.pickTime
                # If next person is to be picked from same location
                # Then complete that action in the same time step
                #if abs(self.timeNextLoc - current_time) < 0.1:
                if self.nextLoc == self.currentLoc:
                    with open(para.output_timestep_log,'a') as op_file:
                        print ("Veh- ",self.id," after drop-off next person ",personToServe.person_id," has same pickup loc and time ", file=op_file)
                    # Check if the vehicle path reflects another pickup at same location at same time
                    # If it does not have a repeating (node,time) element, modify the vehicle path to reflect this
                    if self.nextNode != self.currentLoc:
                        # Insert current node,time to the beginning of the path list
                        self.path = [(self.currentLoc,self.timeNextLoc)] + self.path
                    self.nextNode = self.path[0][0]
                    self.timeNextNode = self.path[0][1]
                    self.updateVehAfterPick(current_time)

        return

    # Idle vehicle will stay at the same location over time, util relocate
    def updateVehIdle(self, currentime):
        # Idle Time Once, this is the idle time from a 'I' to next time step it receives a task
        self.idlTimeOneCum = (currentime - self.idlTimeStart)
        # When vehicle is idle, it is stationary as well, until it starts to Relocate, so increment stationary time
        self.stationary_time += para.TimeStep
        dummy = 0
        # Idle Time Cumulative will be updated once the vehicle got a match
        # When Idle time is more than max idle time, the vehicle will relocate
        if self.idlTimeOneCum >= para.maxIdlTime:
            # Change the flag to 'R'
            self.status = 'R'
            # Then will assign new relocating path to it
        return

    def updateVehAfterMatch(self, newPath):
        ### Need to update

        return

