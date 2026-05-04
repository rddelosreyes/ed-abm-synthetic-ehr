#!/bin/bash

RUNS=1000

echo "Running normal scenarios"
NORMAL=(
    config/real_normal/real_normal.yaml
)

for config in "${NORMAL[@]}"
do
    for ((i=1; i<=RUNS; i++))
    do
        python main.py -f "$config"
    done
done

echo "Running MCI scenarios with increases in arrivals"
MCI_ARRIVAL=(
    config/real_mci_arrival/real_mci_a.yaml
    config/real_mci_arrival/real_mci_b.yaml
    config/real_mci_arrival/real_mci_c.yaml
    config/real_mci_arrival/real_mci_d.yaml
)

for config in "${MCI_ARRIVAL[@]}"
do
    for ((i=1; i<=RUNS; i++))
    do
        python main.py -f "$config"
    done
done

echo "Running MCI scenarios with resource constraints"
MCI_RESOURCE=(
    config/real_mci_resource/real_mci_a.yaml
    config/real_mci_resource/real_mci_b.yaml
    config/real_mci_resource/real_mci_c.yaml
    config/real_mci_resource/real_mci_d.yaml
)

for config in "${MCI_RESOURCE[@]}"
do
    for ((i=1; i<=RUNS; i++))
    do
        python main.py -f "$config"
    done
done

echo "Running MCI scenarios with workflow disruptions"
MCI_WORKFLOW=(
    config/real_mci_workflow/real_mci_a.yaml
    config/real_mci_workflow/real_mci_b.yaml
    config/real_mci_workflow/real_mci_c.yaml
    config/real_mci_workflow/real_mci_d.yaml
)

for config in "${MCI_WORKFLOW[@]}"
do
    for ((i=1; i<=RUNS; i++))
    do
        python main.py -f "$config"
    done
done