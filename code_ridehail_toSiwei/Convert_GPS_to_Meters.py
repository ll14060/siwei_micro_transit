__author__ = 'Mike'
# this file is just used to convert GPS coordinates to meters
import csv
import geopy.distance as gd


def convert_gps_to_meter(file_path):
    gps_traveler_file = open(file_path + '/manhattan_travelers_gps.csv', 'r')
    gps_traveler_file_reader = csv.reader(gps_traveler_file, delimiter=',', skipinitialspace=True)

    trip_id = []
    request_times = []
    pickup_lon = []
    pickup_lat = []
    dropoff_lon = []
    dropoff_lat = []
    group_size = []

    count = 0
    for i_row in gps_traveler_file_reader:
        count += 1
        if count > 1:
            trip_id.append(int(i_row[0]))
            request_times.append(int(float(i_row[1])))  # figure out time units
            pickup_lon.append(float(i_row[2]))
            pickup_lat.append(float(i_row[3]))
            dropoff_lon.append(float(i_row[4]))
            dropoff_lat.append(float(i_row[5]))
            group_size.append(float(i_row[6]))

    min_lat = min(min(pickup_lat), min(dropoff_lat))
    min_lon = min(min(pickup_lon), min(dropoff_lon))
    base_pt = (min_lat, min_lon)

    xy_traveler_file = open(file_path + '/manhattan_travelers_xy.csv', 'w')
    xy_traveler_file_writer = csv.writer(xy_traveler_file, lineterminator='\n', delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_NONNUMERIC)
    xy_traveler_file_writer.writerow(["# person_id","Request_Time [min]",
                                  "Pickup x", "Pickup y", "Dropoff x", "Dropoff y", "group_size"])

    for i_trip in range(len(trip_id)):
        pickup_x = int(gd.vincenty(base_pt, (min_lat, pickup_lon[i_trip])).meters)
        pickup_y = int(gd.vincenty(base_pt, (pickup_lat[i_trip], min_lon)).meters)
        dropoff_x = int(gd.vincenty(base_pt, (min_lat, dropoff_lon[i_trip])).meters)
        dropoff_y = int(gd.vincenty(base_pt, (dropoff_lat[i_trip], min_lon)).meters)

        xy_traveler_file_writer.writerow(
                [trip_id[i_trip], request_times[i_trip],
                 pickup_x, pickup_y, dropoff_x, dropoff_y,
                 group_size[i_trip]]
        )

    xy_traveler_file.close()
    return


convert_gps_to_meter(r"C:\Users\Mike\OneDrive\Documents\Academic_Journal_Papers\Working\6_Dandl")
