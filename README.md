This code accompanies the following paper:

**Delos Reyes, R., Capurro, D., & Geard, N. (2026). _Generating synthetic electronic health record data using agent-based models to evaluate machine learning robustness under mass casualty incidents_. To appear in Proceedings of the 7th Annual Conference on Health, Inference, and Learning.**

<img width="10016" height="4350" alt="CHIL_2026_ED_ABM_synthetic_EHR" src="https://github.com/user-attachments/assets/de6f1f46-0aac-4df7-953c-b345eb532502" />

---

**Setting up the environment**
1. Download [anaconda](https://docs.anaconda.com/)
2. Run
    `conda env create --name edabm`
3. Run
    `conda activate edabm`
4. Run
    `pip install -r requirements.txt`

**Getting the required data**
1. Download the following datasets (they require credentialed access which can be requested at the provided websites)
    - [MIMIC-IV v2.2](https://physionet.org/content/mimiciv/2.2/)
    - [MIMIC-IV-ED v2.2](https://physionet.org/content/mimic-iv-ed/2.2/)
2. Store the unzipped datasets inside the data folder
    - data/ed
    - data/hosp
    - data/icu

**Preprocessing the data**

Open the following Jupyter notebooks in the following order and run all cells:
1. `generate_patient_data.ipynb`&nbsp;&nbsp;\# To exclude patient records with invalid values
2. `generate_event_logs.ipynb`&nbsp;&nbsp;\# To convert the records to event logs
3. `generate_model_parameters.ipynb`&nbsp;&nbsp;\# To generate the parameters needed to run the ED simulation model

**Running the experiments**
1. Run
    `chmod u+x ./run.sh`
2. Run
    `./run.sh`

**Analysing the results**

Open the following Jupyter notebooks and run all cells:
   1. `evaluate_edabm.ipynb`
   2. `evaluate_mlmodel.ipynb`
