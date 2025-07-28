__author__ = 'Flo_New'
# file written by Florian Dandl

import re
import Settings as Set
import Vehicle

# for demand estimations
week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
xy_regex = re.compile(".+(\d+)x_(\d+)y.+")

#
def vectorFromTo(p1, p2):
    return (p2[0]-p1[0], p2[1]-p1[1])

# little rectangles classes
class SubArea():
    def __init__(self, xi, yj, corners):
        self.xi = xi  # index for subarea
        self.yj = yj # index for subarea
        self.corners = corners # used to calculate middle of region
        self.relocation_destination = (int((corners[2][0]-corners[0][0])/2.0), int((corners[2][1]-corners[0][1])/2.0))
        #
        self.number_nonzero_forecast_entries = 0 # just to check if in river
        self.demand_forecast = {}       # weekday -> [estimated_number_of_requests_1, estimated_number_of_requests_2, ...]
    #
    def __str__(self):
        return "xi: {0}, yj:{1}\n\tcorners:{2}\n\tforecast:{3}".format(self.xi, self.yj, self.corners, self.demand_forecast)
        #return "xi: {0}, yj:{1}\n\tcorners:{2}\n\trelocation destination:{3}\n\tnumber nonzero-forecast values:{4}".format(self.xi, self.yj, self.corners, self.relocation_destination, self.number_nonzero_forecast_entries)
    #
    def setRelocationDestination(self, point):
        self.relocation_destination = point

    # lc is a row in the demand prediction file
    def setDemandPrediction(self, lc):
        weekday = lc[2]
        self.demand_forecast[weekday] = [float(x) for x in lc[4:]]  # Comment MH: Divide Forecast by 10, because divided demand by 10 /10.0
        for entry in self.demand_forecast[weekday]:
            if entry != 0:
                self.number_nonzero_forecast_entries += 1

    # not that important
    def getDemandEstimation(self, weekday, i):
        # test if weekday exists
        # use weekday-1 if not (only forecast for 1 day avaliable)
        if self.demand_forecast.get(weekday):
            return self.demand_forecast[weekday][i]
        else:
            weekday_index = week.index(weekday)
            day_before_weekday = week[weekday_index-1]  # also works for weekday_index = 0!
            return self.demand_forecast[day_before_weekday][i]

    # not that important
    def isActive(self):
        if self.number_nonzero_forecast_entries != 0:
            return True
        else:
            return False
#
class Area():
    def __init__(self, region_csv_file, prediction_csv_file, relocation_destination_f, date=None):
        self.region_csv_file = region_csv_file
        self.prediction_csv_file = prediction_csv_file
        self.prediction_date = date
        # check if files are fitting together
        m_region = xy_regex.search(self.region_csv_file)
        m_pred = xy_regex.search(self.prediction_csv_file)
        if not m_region or not m_pred or m_region.groups()!=m_pred.groups():
            print("---------------------------------------------------")
            print("Regions and Predictions seem to be not matching!")
            print("Region file: {0}".format(region_csv_file))
            print("Prediction file: {0}".format(prediction_csv_file))
            print("---------------------------------------------------")
            raise IOError
        #
        self.x0 = None              # x-anchor of first SubArea
        self.y0 = None              # y-anchor of first SubArea
        self.x_unit = None          # length of x-edge of SubAreas
        self.y_unit = None          # length of y-edge of SubAreas
        self.sub_areas = {}         # (xi, yj) -> SubArea object
        self.forecast_int = []      # [start_time_of_interval_1, start_time_of_interval_2, ...] (in minutes)
        # reading area definition

        # Comment MH:
        # Change to prediction_csv_file
        # fhin = open(region_csv_file, 'r')
        fhin = open(prediction_csv_file, 'r')
        for line in fhin:
            if not line.strip() or line.startswith("#"):
                continue
            lc = line.strip().split(",")
            xi = int(lc[0])
            yj = int(lc[1])
            corners = []
            for ck in lc[2:]:
                corners.append([float(x) for x in ck.split(";")])
            self.sub_areas[(xi, yj)] = SubArea(xi, yj, corners)
            if not self.x0:
                (self.x0, self.y0) = corners[0]
                x_unit_edge = vectorFromTo(corners[0], corners[1])
                if x_unit_edge[1] == 0.0:
                    self.x_unit = x_unit_edge[0]
                else:
                    print("The x-axis of the areas in {0} are not aligned with x-axis".format(region_csv_file))
                    raise IOError
                y_unit_edge = vectorFromTo(corners[0], corners[3])
                if y_unit_edge[0] == 0.0:
                    self.y_unit = y_unit_edge[1]
                else:
                    print("The x-axis of the areas in {0} are not aligned with x-axis".format(region_csv_file))
                    raise IOError
        fhin.close()

        # reading demand center points



        fhin = open(relocation_destination_f, 'r')
        for line in fhin:
            if not line.strip() or line.startswith("#"):
                continue
            lc = line.strip().split(",")
            xi = int(lc[0])
            yj = int(lc[1])
            x_rel_dest = int(lc[2])
            y_rel_dest = int(lc[3])
            self.sub_areas[(xi, yj)].setRelocationDestination((x_rel_dest, y_rel_dest))
        fhin.close()

        # Comment MH:
        # Change to region_csv_file
        # fhin = open(relocation_destination_f, 'r')
        # reading demand predictions
        fhin = open(region_csv_file, 'r')
        for line in fhin:
            if not self.forecast_int:
                hc = line.strip().split(",")
                self.forecast_int = [3600*int(x.split(":")[0]) + 60*int(x.split(":")[1]) for x in hc[4:]]
            if not line.strip() or line.startswith("#"):
                continue
            lc = line.strip().split(",")
            if self.prediction_date:
                if self.prediction_date in lc[3]:
                    #print("using prediction of {0} for simulation of day {1}".format(lc[3], self.prediction_date))
                    use_flag = True
                else:
                    use_flag = False
            else:
                use_flag = True
            if use_flag:
                xi = int(lc[0])
                yj = int(lc[1])
                self.sub_areas[(xi, yj)].setDemandPrediction(lc)
        fhin.close()
        #print(self)
    #
    def __str__(self):
        prt_list = []
        prt_list.append("Area file: {0}".format(self.region_csv_file))
        prt_list.append("Prediction file: {0}".format(self.prediction_csv_file))
        prt_list.append("Prediction date: {0}".format(self.prediction_date))
        prt_list.append("-----------------------------")
        prt_list.append("Number of subareas: {0}".format(len(self.sub_areas.keys())))
        prt_list.append("Anchor point: ({0}, {1})".format(self.x0, self.y0))
        prt_list.append("X-unit vector: ({0}, 0)".format(self.x_unit))
        prt_list.append("Y-unit vector: (0, {0})".format(self.y_unit))
        prt_list.append("-----------------------------")
        prt_list.append("Subareas:")
        for sa_key in sorted(self.sub_areas.keys()):
            sa_obj = self.sub_areas[sa_key]
            prt_list.append(str(sa_obj))
        return "\n".join(prt_list)
    #
    def findSubAreaOfPoint(self, point):
        x_val = point[0] - self.x0
        if x_val < 0:
            xi = -1
        else:
            xi = int(x_val/self.x_unit)
        y_val = point[1] - self.y0
        if y_val < 0:
            yj = -1
        else:
            yj = int(y_val/self.y_unit)
#         print("point {0}".format(point))
#         print("x_val {0}".format(x_val))
#         print("xi {0}".format(xi))
#         print("y_val {0}".format(y_val))
#         print("yj {0}".format(yj))
        return self.sub_areas.get((xi, yj))
    #
    def getVehicleAvailabilitiesPerArea(self, av_fleet):
        # input: list of vehicles
        # output: dictionary with subArea key -> list of (veh_id, av_time)
        veh_availabilities = {}       # (xi, yj) -> [(veh_id, av_time)_1, (veh_id, av_time)_2, ...]
        for sa_key in self.sub_areas.keys():
            veh_availabilities[sa_key] = []
        #
        count_veh = -1
        for j_veh in av_fleet:
            count_veh += 1
            (av_x, av_y, av_dist) = Vehicle.get_next_availability(j_veh)
            av_time = av_dist/Set.veh_speed
            sa_obj = self.findSubAreaOfPoint((av_x, av_y))
            if sa_obj:
                xi = sa_obj.xi
                yj = sa_obj.yj
                veh_availabilities[(xi, yj)].append((count_veh, av_time))
            else:
                print("Vehicle location {0} is out of bounds! It will not be counted to any subarea.".format(count_veh))
        return veh_availabilities

    def getNumberOfCurrentlyUnassignedRequestPerArea(self, customers):
        # input: list of customers
        # output: dictionary with subArea key -> number of currently unassigned customers in this subregion
        unassigned_cust_per_region = {}         # (xi, yj) -> number
        for sa_key in self.sub_areas.keys():
            unassigned_cust_per_region[sa_key] = 0
        for request in customers:
            if request.status == "unassigned":
               pick_up_location = (request.pickup_location_x, request.pickup_location_y)
               respective_subArea = self.findSubAreaOfPoint(pick_up_location)
               if respective_subArea:
                   xi = respective_subArea.xi
                   yj = respective_subArea.yj
                   unassigned_cust_per_region[(xi, yj)] += 1
        return unassigned_cust_per_region

    #
    def getDemandPredictionsPerArea(self, weekday, time, relocation_time_horizon):
        # input:
        # - weekday in week
        # - time in seconds
        # - relocation_time_horizon in seconds
        demand_predictions = {}     # (xi, yj) -> count
        for sa_key in self.sub_areas.keys():
            demand_predictions[sa_key] = 0
        #
        ti_weekday = {} # i -> weekday
        # find start interval
        i = 0
        while time >= self.forecast_int[i]:
            i += 1
        i -= 1
        start_time_index = i
        # find end interval
        end_time = time + relocation_time_horizon
        while self.forecast_int[i] < end_time:
            ti_weekday[i] = weekday
            i += 1
            # jump to next weekday
            if i == len(self.forecast_int):
                i = 0
                end_time -= 24*60*60
                weekday_index = week.index(weekday)
                next_weekday_index = weekday_index + 1
                if next_weekday_index == len(week):
                    next_weekday_index = 0
                weekday = week[next_weekday_index]
        last_time_index = i
#         print("Start time index: {0} | End time index: {1}".format(start_time_index, last_time_index))
        # sum of all intervals that are touched
        for i in range(start_time_index, last_time_index):
            for sa_key, sa_obj in self.sub_areas.items():
                demand_predictions[sa_key] += sa_obj.getDemandEstimation(ti_weekday[i], i)
#                 if sa_key == (0,1):
#                     print(demand_predictions[sa_key])
        # remove part for time > self.forecast_int[start_time_index]
        ratio_time_in_time_interval = 1.0 * (time - self.forecast_int[start_time_index])/(self.forecast_int[start_time_index+1] - self.forecast_int[start_time_index])
        for sa_key, sa_obj in self.sub_areas.items():
            demand_predictions[sa_key] -= (ratio_time_in_time_interval * sa_obj.getDemandEstimation(ti_weekday[start_time_index], start_time_index))
#             if sa_key == (0,1):
#                 print(time, self.forecast_int[start_time_index], self.forecast_int[start_time_index+1])
#                 print(ratio_time_in_time_interval, sa_obj.getDemandEstimation(ti_weekday[start_time_index], start_time_index), demand_predictions[sa_key])
        # remove part for time+relocation_time_horizon < self.forecast_int[last_time_index]
        ratio_time_in_time_interval = 1.0 * (self.forecast_int[last_time_index] - end_time)/(self.forecast_int[last_time_index] - self.forecast_int[last_time_index-1])
        for sa_key, sa_obj in self.sub_areas.items():
            demand_predictions[sa_key] -= (ratio_time_in_time_interval * sa_obj.getDemandEstimation(ti_weekday[last_time_index-1], last_time_index-1))
#             if sa_key == (0,1):
#                 print(end_time, self.forecast_int[last_time_index-1], self.forecast_int[last_time_index])
#                 print(ratio_time_in_time_interval, sa_obj.getDemandEstimation(ti_weekday[last_time_index-1], last_time_index-1), demand_predictions[sa_key])
        #
        return demand_predictions

# # --------------------------------------------------------------------------- #
# # test of code
# if __name__ == '__main__':
#     # example: reading input
#     prediction_csv_file = r"manhattan_trip_patterns_2x_6y_15min_only_predictions.csv"
#     region_csv_file = r"prediction_areas_2x_6y_for_testing.csv"
#     relocation_destination_csv_file = r"demand_center_points_2x_6y_for_testing.csv"
#     #region_csv_file = r"prediction_areas_2x_8y.csv"
#     area_instance = Area(region_csv_file, prediction_csv_file, relocation_destination_csv_file)
#     print(area_instance)
#     #
#     print("-----------------------------")
#     # example vehicle availabilities
#     # lower left corner: -1290.0;1509.0
#     # upper right corner: 1541.0;22682.0
#     list_vehicle_availabilities = []
#     list_vehicle_availabilities.append((0,1800))
#     list_vehicle_availabilities.append((1800,1800))
#     list_vehicle_availabilities.append((1800,7800))
#     list_vehicle_availabilities.append((0,10000))
#     list_vehicle_availabilities.append((-2000,0))   # point not in area
#     veh_av_dict = area_instance.getVehicleAvailabilitiesPerArea(list_vehicle_availabilities)
#     print(veh_av_dict)
#     #
#     print("-----------------------------")
#     # example demand predictions
#     weekday = "Tuesday"
#     #time = 10*60*60
#     time = 10*60*60-7.5*60
#     relocation_time_horizon = 30*60
#     demand_forecast = area_instance.getDemandPredictionsPerArea(weekday, time, relocation_time_horizon)
#     print("Forecast for {0} at time {1} with time horizon {2}:".format(weekday, time, relocation_time_horizon))
#     print(demand_forecast)