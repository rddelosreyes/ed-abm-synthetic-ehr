import datetime
import mesa
import networkx as nx
import numpy as np
import pandas as pd
import random
import string

from agent import PatientAgent

class HospitalResource():

    def __init__(self, identifier, name, capacity=float('inf')):
        self.identifier = identifier
        self.name = name
        self.execution_queue = []
        self.waiting_queue = []
        self.capacity = capacity

    def transfer(self):
        patient_execute = self.waiting_queue.pop(0)
        self.execution_queue.append(patient_execute)
        patient_execute.in_execution_queue = 1

class EDModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, **params):
        super().__init__()
        # Simulation run parameters
        self.simulation_type = params['simulation_type']
        self.increase_arrival = params['increase_arrival']
        self.increase_resource = params['increase_resource']
        self.increase_workflow = params['increase_workflow']

        self.increase_resource_flag = 0

        # ED resource parameters
        self.no_beds = params['no_beds']
        self.no_clinicians = params['no_clinicians']
        self.no_imaging = params['no_imaging']

        self.available_clinicians = params['no_clinicians']
        self.busy_clinicians = 0

        self.new_patient_id = 1
        self.hosp_waiting_1 = []
        self.hosp_waiting_2 = []
        self.hosp_waiting_345 = []
        self.hosp_execution_queue = []

        # Arrival parameters
        self.hourly_arrival_rate = params['hourly_arrival_rate']
        self.new_patient_arrival_time = np.random.poisson(60/self.hourly_arrival_rate[24])

        # Process parameters
        process_model_dict = params['process_model']
        path_cohort_frequency = params['path_cohort_frequency']
        self.categories_acuity = ['1', '2', '3', '4', '5']

        process_model = self._get_process_model_graph(process_model_dict)

        self.process_dict = {}
        self.process_shared = {}
        self.process_unshared = {}
        for process_id in process_model.nodes():
            new_process = HospitalResource(process_id, process_model.nodes[process_id]['name'], process_model.nodes[process_id]['capacity'])
            self.process_dict[process_id] = new_process

            if process_model.nodes[process_id]['share_clinicians']:
                self.process_shared[process_id] = new_process
            else:
                self.process_unshared[process_id] = new_process

        self.df_frequency_subcohort = pd.read_csv(f'{path_cohort_frequency}/frequency_groupname.csv', index_col='acuity').sort_values(['acuity']).reset_index()
        self.df_frequency_subcohort['groupname'] = self.df_frequency_subcohort['acuity'].astype(str) + '-' + self.df_frequency_subcohort['disposition'].astype(str)
        groupname_list = set(self.df_frequency_subcohort['groupname'])

        self.dict_frequency_per_acuity = {}
        for acuity_val, disp_val, per_val in zip(self.df_frequency_subcohort['acuity'], self.df_frequency_subcohort['disposition'], self.df_frequency_subcohort['percent']):
            acuity_val = str(acuity_val)
            if acuity_val not in self.dict_frequency_per_acuity.keys():
                self.dict_frequency_per_acuity[acuity_val] = {}

            grp_val = disp_val
            self.dict_frequency_per_acuity[acuity_val][grp_val] = per_val

        self.df_frequency_acuity = pd.read_csv(f'{path_cohort_frequency}/frequency.csv')

        # Mesa parameters
        self.grid = mesa.space.NetworkGrid(process_model)
        self.schedule = mesa.time.RandomActivation(self)
        self.running = True

        # Output parameters
        self.period_runin = params['period_runin']
        self.output_folder = params['output_folder']

        if 'real' in self.simulation_type:
            self.synthetic_ehrs = {}
            self.time_now = datetime.datetime.now().replace(second=0, microsecond=0)

        self.reference_df_frequency_acuity = self.df_frequency_acuity.copy()
        self.reference_df_frequency_subcohort = self.df_frequency_subcohort.copy()

        path_test_data = params['path_test_data']
        self.df_test = pd.read_pickle(f'{path_test_data}')

        self.df_test['acuity'] = self.df_test['acuity'].astype(str)
        self.df_test['disposition'] = self.df_test['disposition'].astype(str)

    def step(self):
        """Advance the model by one step."""
        # Remove clinicians
        day_now = self._get_time_in_days()
        if self.period_runin + 3 < day_now <= self.period_runin + 7:
            if self.increase_resource_flag < self.increase_resource:
                if self.available_clinicians > 0:
                    self.available_clinicians -= 1
                    self.no_clinicians -= 1
                    self.increase_resource_flag += 1

        # Add new patients based on hourly arrival rate
        while self.new_patient_arrival_time == 0:
            self._create_new_arrival()
            hour_of_day = self._get_hour_of_day()

            day_now = self._get_time_in_days()
            if self.increase_arrival > 0:
                magnitude_increase_val = 0
                if self.period_runin + 3 < day_now <= self.period_runin + 7:
                    magnitude_increase_val = self.increase_arrival

                self.new_patient_arrival_time = np.random.poisson(60/(self.hourly_arrival_rate[hour_of_day] * (1+magnitude_increase_val)))
            else:
                self.new_patient_arrival_time = np.random.poisson(60/self.hourly_arrival_rate[hour_of_day])

        # Move patients from hospital waiting queue to hospital execution queue if bed is available
        if self._get_bed_occupancy() < self.no_beds:
            number_of_patients_to_add = self.no_beds - self._get_bed_occupancy()
            in_waiting_queue = self.hosp_waiting_1 + self.hosp_waiting_2 + self.hosp_waiting_345
            patients_to_add = in_waiting_queue[:number_of_patients_to_add]

            for waiting_patient in patients_to_add:
                if waiting_patient.acuity == '1':
                    self.hosp_waiting_1.remove(waiting_patient)
                elif waiting_patient.acuity == '2':
                    self.hosp_waiting_2.remove(waiting_patient)
                else:
                    self.hosp_waiting_345.remove(waiting_patient)

                self.hosp_execution_queue.append(waiting_patient)

                next_resource = waiting_patient.destination_list.pop(0)
                self.grid.place_agent(waiting_patient, next_resource)
                self.process_dict[next_resource].execution_queue.append(waiting_patient)
                waiting_patient.in_execution_queue = 1

                next_execution = waiting_patient.execution_list.pop(0)
                waiting_patient.execution_ctr = next_execution

        # Move all patients
        for patient in self.schedule.agents:
            patient.step()

        # Transfer patients in bed across hospital resources
        for resource_unit in list(self.process_dict.values())[::-1]:
            for patient_in_bed in list(resource_unit.execution_queue):
                if patient_in_bed.execution_ctr <= 0:
                    resource_unit.execution_queue.remove(patient_in_bed)

                    if len(patient_in_bed.destination_list) > 1:
                        next_resource = patient_in_bed.destination_list.pop(0)
                        self.grid.move_agent(patient_in_bed, next_resource)
                        self.process_dict[next_resource].waiting_queue.append(patient_in_bed)
                        patient_in_bed.in_execution_queue = 0

                        next_execution = patient_in_bed.execution_list.pop(0)

                        if next_resource == 'E':
                            day_now = self._get_time_in_days()
                            if self.period_runin + 3 < day_now <= self.period_runin + 7:
                                if self.increase_workflow > 0:
                                    next_execution += np.random.normal(self.increase_workflow)

                        patient_in_bed.execution_ctr = next_execution
                    else:
                        if self.period_runin + 3 < patient_in_bed.arrival_time_in_days <= self.period_runin + 7:
                            self._record_removed_patient(patient_in_bed)

                        self.hosp_execution_queue.remove(patient_in_bed)
                        self.grid.remove_agent(patient_in_bed)
                        self.schedule.remove(patient_in_bed)

                    if resource_unit.identifier in self.process_shared.keys():
                        self.available_clinicians += 1
                        self.busy_clinicians -= 1

        # Move patients in bed from waiting queue to execution queue per resource unit if space becomes available
        for resource_unit in self.process_unshared.values():
            while len(resource_unit.execution_queue) < resource_unit.capacity:
                if resource_unit.waiting_queue:
                    resource_unit.transfer()
                else:
                    break

        while self.available_clinicians:
            shared_resources_with_in_waiting_queue = [resource_unit for resource_unit in self.process_shared.values() if (len(resource_unit.waiting_queue) > 0) and (len(resource_unit.execution_queue) < resource_unit.capacity)]

            if shared_resources_with_in_waiting_queue:
                random.shuffle(shared_resources_with_in_waiting_queue)

                shared_resources_with_in_waiting_queue[0].transfer()
                self.available_clinicians -= 1
                self.busy_clinicians += 1
            else:
                break

        assert self.busy_clinicians <= self.no_clinicians, 'Number of occupied clinicians should be at most equal to the number of clinicians'

        self.schedule.steps += 1
        self.schedule.time += 1
        self.new_patient_arrival_time -= 1

    def _get_day_of_week(self):
        day_of_week = int(self._get_time_in_days()) % 7
        if day_of_week == 0: day_of_week = 7

        return day_of_week

    def _get_hour_of_day(self):
        hour_of_day = int(self._get_time_in_hours()) % 24
        if hour_of_day == 0: hour_of_day = 24

        return hour_of_day

    def _get_bed_occupancy(self):

        return len(self.hosp_execution_queue)

    def _get_bed_waiting(self):

        return len(self.hosp_waiting_1) + len(self.hosp_waiting_2) + len(self.hosp_waiting_345)

    def _get_time_in_days(self):

        return self.schedule.time / (60*24)

    def _get_time_in_hours(self):

        return self.schedule.time / 60

    def _get_process_model_graph(self, process_model_dict):
        # Assign alphabet IDs to process names (for better handling)
        node_dict = {}
        alphabet_counterpart = string.ascii_uppercase[:len(process_model_dict)]
        for process_id, (process_name, process_attributes) in zip(alphabet_counterpart, process_model_dict.items()):
            node_dict[process_id] = {'name': process_name, 'capacity': float(process_attributes['capacity']), 'share_clinicians': process_attributes['share_clinicians']}

        # Create process model
        process_model = nx.complete_graph(node_dict.keys(), nx.DiGraph())
        nx.set_node_attributes(process_model, node_dict)

        return process_model

    def _get_hospitalisation_probability(self, L, a, x0=0):
        if L <= x0:
            return 1
        else:
            return np.exp(-a * (L - x0))

    def _create_new_arrival(self):
        new_patient = PatientAgent(self.new_patient_id, self)

        new_patient.acuity = str(random.choices(self.df_frequency_acuity.acuity.tolist(), weights=self.df_frequency_acuity.percent.tolist())[0])
        patient_end_weights = list(self.dict_frequency_per_acuity[new_patient.acuity].values())

        patient_end = random.choices(list(self.dict_frequency_per_acuity[new_patient.acuity].keys()), weights=patient_end_weights)[0]
        new_patient.disposition = patient_end.split('-')[0]

        # Sample from df_test
        while True:
            day_now = self._get_time_in_days()

            df_cohort = self.df_test[(self.df_test['acuity'] == str(new_patient.acuity)) & (self.df_test['disposition'] == str(new_patient.disposition))]

            if len(df_cohort):
                sample_test = df_cohort.sample(n=1)
                new_patient.mimic_id = sample_test['stay_id'].iloc[0]
                break

            # Resample attributes
            new_patient.acuity = str(random.choices(self.df_frequency_acuity.acuity.tolist(), weights=self.df_frequency_acuity.percent.tolist())[0])

            patient_end_weights = list(self.dict_frequency_per_acuity[new_patient.acuity].values())
            patient_end = random.choices(list(self.dict_frequency_per_acuity[new_patient.acuity].keys()), weights=patient_end_weights)[0]
            new_patient.disposition = patient_end.split('-')[0]

        destination_list = list(sample_test['activity_name'].iloc[0])
        execution_list = sample_test['time_diffs'].iloc[0]
        execution_list = [max(int(x),1) for x in execution_list]

        new_patient.destination_record = ''.join(destination_list)
        new_patient.destination_list = destination_list
        new_patient.execution_list = execution_list
        new_patient.arrival_time_in_days = self._get_time_in_days()

        # For synthetic data stratification
        new_patient.patient_volume_at_arrival = self._get_bed_occupancy() + self._get_bed_waiting()
        all_patients_list = self.hosp_execution_queue + self.hosp_waiting_1 + self.hosp_waiting_2 + self.hosp_waiting_345
        all_patients_list_los = [pat_idx.ed_los for pat_idx in all_patients_list]
        new_patient.median_los_at_arrival = np.median(all_patients_list_los) if len(all_patients_list_los) else 0

        self.schedule.add(new_patient)
        self.new_patient_id += 1

        if self._get_bed_occupancy() == self.no_beds:
            if new_patient.acuity == '1':
                self.hosp_waiting_1.append(new_patient)
            elif new_patient.acuity == '2':
                self.hosp_waiting_2.append(new_patient)
            else:
                self.hosp_waiting_345.append(new_patient)
        else:
            self.hosp_execution_queue.append(new_patient)

            next_resource = new_patient.destination_list.pop(0)
            self.grid.place_agent(new_patient, next_resource)
            self.process_dict[next_resource].execution_queue.append(new_patient)
            new_patient.in_execution_queue = 1

            next_execution = new_patient.execution_list.pop(0)
            new_patient.execution_ctr = next_execution

    def _record_removed_patient(self, patient):
        patient_record = {key: val for key, val in vars(patient).items() if key not in ['model', 'pos', 'destination_list', 'execution_list', 'execution_ctr', 'in_execution_queue']}
        self.synthetic_ehrs[patient.unique_id] = patient_record
