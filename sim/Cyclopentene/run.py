# %%
from pathlib import Path

import cantera
import polars
from cantera.ck2yaml import Parser

from cantera_helper.reactors import jsr

# >> Configure these parameters as needed: <<
# Required files:
concentrations_file = "concentrations.csv"  # Concentrations spreadsheet
species_file = "species.csv"
chemkin_file = "chem.inp"  # Chemkin mechanism
thermo_file = "thermo.dat"
# Generated files:
cantera_file = Path(chemkin_file).with_suffix(".yaml")  # Cantera mechanism
results_file = "results.csv"  # Results will be written to this file
# Conditions / other parameters:
T = 825  # Temperature (K)
P = 1.1  # Pressure (atm)
residence_time = 2  # Residence time (s)
volume = 1  # Volume (cm^3)
# run_every = 15  # Run every nth concentration for testing
run_every = 1  # (Set this to 1 for the actual simulation)

# %%
# Read in concentrations
print(f"Reading in concentrations from {concentrations_file}")
concs_df = polars.read_csv(concentrations_file)
concs_df = concs_df.gather_every(run_every)
conc_dcts = concs_df.select("fuel", "O2", "N2").to_dicts()

# %%
# Read in species
print(f"Reading in species from {species_file}")
species_df = polars.read_csv(species_file)
species_dct = {k: v for k, v in species_df.select(["species", "name"]).iter_rows()}

# %%
conc_dcts = [{species_dct[k]: v for k, v in c.items()} for c in conc_dcts]
species_dct = {k: v for k, v in species_dct.items() if k not in ["fuel", "O2", "N2"]}

# %%
# Determine N2, O2, fuel names
print("Simulations will be run at the following conditions...")
for conc_dct in conc_dcts:
    for name, conc_dct in conc_dct.items():
        print(f"  {name}: {conc_dct:10.6f}", end="")
    print()

# %%
# Print other species names
print("Data will be collected for the following species...")
for species, name in species_dct.items():
    print(f"  {species}: {name}")

# %%
# Read in ChemKin mechanism and convert to Cantera
print("\nConverting ChemKin mechanism to Cantera YAML...")
Parser.convert_mech(chemkin_file, thermo_file=thermo_file, out_name=cantera_file)

# %%
# Load mechanism and set initial conditions
print("\nDefining model and conditions...")
model = cantera.Solution(cantera_file)

# %%
# Run simulations for each point and store the results in an array
print("\nRunning simulations...")


def simulate(conc_dct: dict[str, float]) -> cantera.ReactorNet:  # pyright: ignore[reportAttributeAccessIssue]
    """Run simulation."""
    print(f"Starting simulation for {conc_dct}")
    return jsr(
        model=model,
        T=T,
        P=P,
        residence_time=residence_time,
        volume=volume,
        concentrations=conc_dct,
    )


solutions = cantera.SolutionArray(model)
for conc_dct in conc_dcts:
    reactor = simulate(conc_dct)
    solutions.append(reactor.thermo.state)

# %%
# Extract results
print("\nExtracting results...")
results_df = concs_df.with_columns(
    polars.Series(species, solutions(name).X.flatten() * 10**6)
    for species, name in species_dct.items()
)
print(results_df)
results_df.write_csv(results_file)

