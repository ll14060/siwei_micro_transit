import os

def determine_dolders(study_area, dt_sd_full_trnst_ntwk, zonal_partition, TRPartA, BayesianOptimization):
    base = os.path.expanduser("~/Downloads/Siwei_Micro_Transit/Siwei_Micro_Transit")

    if TRPartA:
        if BayesianOptimization:
            # demand folder
            demand_folder = os.path.join(base, "Bayesian_Optimization", "demand_data", str(study_area))

            if study_area == "downtown_sd":
                fleetpy_demand_folder = os.path.join(base, "FleetPy_SanDiego", "data", "demand", "example_demand", "matched", "example_network")
                if zonal_partition:
                    initial_network_folder = os.path.join(base, "Bayesian_Optimization", str(study_area), "initial_network_folder", "initial_full_transit_network_4_zones")
                else:
                    initial_network_folder = os.path.join(base, "Bayesian_Optimization", str(study_area), "initial_network_folder", "initial_full_transit_network")

            if study_area == "lemon_grove":
                fleetpy_demand_folder = os.path.join(base, "FleetPy_SanDiego", "data", "demand", "lemon_grove_example_demand", "matched", "lemon_grove_example_network")
                if zonal_partition:
                    initial_network_folder = os.path.join(base, "Bayesian_Optimization", str(study_area), "initial_network_folder", "initial_network_4_zones")
                else:
                    initial_network_folder = os.path.join(base, "Bayesian_Optimization", str(study_area), "initial_network_folder", "initial_network")

            final_network_folder = os.path.join(base, "Bayesian_Optimization", str(study_area), "final_network_folder")
            output_folder = os.path.join(base, "Bayesian_Optimization", str(study_area), "output_folder")

        else:
            demand_folder = os.path.join(base, "TR_PartA", "Data", "demand_data", str(study_area))

            if study_area == "downtown_sd":
                fleetpy_demand_folder = os.path.join(base, "FleetPy_SanDiego", "data", "demand", "example_demand", "matched", "example_network")
                if zonal_partition:
                    initial_network_folder = os.path.join(base, "TR_PartA", "Data", str(study_area), "initial_network_folder", "initial_full_transit_network_4_zones")
                else:
                    initial_network_folder = os.path.join(base, "TR_PartA", "Data", str(study_area), "initial_network_folder", "initial_full_transit_network")

            if study_area == "lemon_grove":
                fleetpy_demand_folder = os.path.join(base, "FleetPy_SanDiego", "data", "demand", "lemon_grove_example_demand", "matched", "lemon_grove_example_network")
                if zonal_partition:
                    initial_network_folder = os.path.join(base, "TR_PartA", "Data", str(study_area), "initial_network_folder", "initial_network_4_zones")
                else:
                    initial_network_folder = os.path.join(base, "TR_PartA", "Data", str(study_area), "initial_network_folder", "initial_network")

            final_network_folder = os.path.join(base, "TR_PartA", "Data", str(study_area), "final_network_folder")
            output_folder = os.path.join(base, "TR_PartA", "Data", str(study_area), "output_folder")

    else:
        if study_area == "downtown_sd":
            demand_folder = os.path.join(base, "Data", "0719_input", "demand_folder")
            if dt_sd_full_trnst_ntwk:
                if zonal_partition:
                    initial_network_folder = os.path.join(base, "Data", "0719_input", "initial_full_transit_network_4_zones")
                else:
                    initial_network_folder = os.path.join(base, "Data", "0719_input", "initial_full_transit_network")
            else:
                initial_network_folder = os.path.join(base, "Data", "0719_input", "initial_network")

            final_network_folder = os.path.join(base, "Data", "0719_input", "final_network")
            fleetpy_demand_folder = os.path.join(base, "FleetPy_SanDiego", "data", "demand", "example_demand", "matched", "example_network")
            output_folder = os.path.join(base, "Data", "0719_input", "output_folder")

        if study_area == "lemon_grove":
            demand_folder = os.path.join(base, "Data", "0719_input", "lemon_grove", "demand_folder")
            if zonal_partition:
                initial_network_folder = os.path.join(base, "Data", "0719_input", "lemon_grove", "initial_network_4_zones")
            else:
                initial_network_folder = os.path.join(base, "Data", "0719_input", "lemon_grove", "initial_network")

            final_network_folder = os.path.join(base, "Data", "0719_input", "lemon_grove", "final_network")
            fleetpy_demand_folder = os.path.join(base, "FleetPy_SanDiego", "data", "demand", "lemon_grove_example_demand", "matched", "lemon_grove_example_network")
            output_folder = os.path.join(base, "Data", "0719_input", "lemon_grove", "output_folder")

    return demand_folder, initial_network_folder, final_network_folder, fleetpy_demand_folder, output_folder
