"""
DispatchLens Business Equipment & Fleet Classification Module

IMPORTANT:
These equipment and fleet size categories ("Broker / Dispatch", "Power Only",
"Hotshot", "Box Truck", "Big Equipment", "Tractor-Trailer", "General Carrier",
"Single Unit", "Multi Trucks", "Zero Units") are DispatchLens business classifications
derived from FMCSA Company Census data and are NOT official FMCSA regulatory classifications.
"""

def _to_int(val):
    if val is None or val == '':
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _is_cargo_active(val):
    if val is None:
        return False
    s = str(val).strip().upper()
    if s in ['', 'N', 'NO', '0', 'FALSE', 'NONE', 'NULL']:
        return False
    return True


def classify_equipment(item):
    """
    Derives DispatchLens Business Equipment Type and Fleet Size from an FMCSA census record.

    Priority Order:
    1. Broker / Dispatch
    2. Hotshot
    3. Power Only
    4. Box Truck
    5. Big Equipment
    6. Tractor-Trailer
    7. General Carrier

    Fleet Size:
    - Zero Units (power_units == 0)
    - Single Unit (power_units == 1)
    - Multi Trucks (power_units >= 2)
    """
    if not isinstance(item, dict):
        item = {}

    legal_name = str(item.get("legal_name") or "").upper()
    dba_name = str(item.get("dba_name") or "").upper()
    name_combined = f"{legal_name} {dba_name}"

    pu = _to_int(item.get("power_units"))

    # Tractor counts (Owned + Term Leased + Trip Leased)
    owntract = _to_int(item.get("owntract"))
    trmtract = _to_int(item.get("trmtract"))
    trptract = _to_int(item.get("trptract"))
    total_tractors = owntract + trmtract + trptract

    # Trailer counts (Owned + Term Leased + Trip Leased)
    owntrail = _to_int(item.get("owntrail"))
    trmtrail = _to_int(item.get("trmtrail"))
    trptrail = _to_int(item.get("trptrail"))
    total_trailers = owntrail + trmtrail + trptrail

    # Straight truck counts (Owned + Term Leased + Trip Leased)
    owntruck = _to_int(item.get("owntruck"))
    trmtruck = _to_int(item.get("trmtruck"))
    trptruck = _to_int(item.get("trptruck"))
    total_straight_trucks = owntruck + trmtruck + trptruck

    if total_straight_trucks == 0 and item.get("truck_units") is not None and total_tractors == 0 and pu > 0:
        total_straight_trucks = _to_int(item.get("truck_units"))

    cargo_desc = str(item.get("crgo_cargoothr_desc") or "").upper()
    carship_str = str(item.get("carship") or "").upper()
    carship_parts = [p.strip() for p in carship_str.split(';')]
    classdef_str = str(item.get("classdef") or "").upper()

    # Determine whether the entity is specifically a Broker or Dispatcher
    # Sourced from official FMCSA carship indicator ('B' = Broker), classdef, and business naming.
    # Do NOT assume zero power units alone proves a company is a broker or dispatcher.
    is_broker = (
        'B' in carship_parts or
        'BROKER' in classdef_str or
        any(term in name_combined for term in ["BROKER", "BROKERAGE", "FREIGHT BROKER", "DISPATCH", "DISPATCHING", "FREIGHT FORWARD", "FORWARDING", "3PL"]) or
        any(term in cargo_desc for term in ["BROKER", "DISPATCH", "FREIGHT FORWARD"])
    )

    # Rule 1: Confirmed Broker / Dispatch
    if is_broker:
        equipment_type = "Broker / Dispatch"

    # Rule 2: Hotshot
    elif ("HOTSHOT" in name_combined or "HOT SHOT" in name_combined) or \
         (total_straight_trucks > 0 and total_trailers > 0 and total_tractors == 0):
        equipment_type = "Hotshot"

    # Rule 3: Power Only
    elif total_tractors > 0 and total_trailers == 0:
        equipment_type = "Power Only"

    # Rule 4: Box Truck
    elif total_straight_trucks > 0 and total_tractors == 0:
        equipment_type = "Box Truck"

    # Rule 5: Big Equipment
    elif _is_cargo_active(item.get("crgo_machlrg")) or \
         _is_cargo_active(item.get("crgo_oilfield")) or \
         _is_cargo_active(item.get("crgo_mobilehome")) or \
         any(term in cargo_desc for term in ["OIL FIELD", "STEEL", "REBAR", "HEAVY", "MACHINERY", "GRAVEL"]):
        equipment_type = "Big Equipment"

    # Rule 6: Tractor-Trailer
    elif total_tractors > 0 and total_trailers > 0:
        equipment_type = "Tractor-Trailer"

    # Rule 7: General Carrier (includes motor carriers with 0 power units on file, NOT assuming they are brokers)
    else:
        equipment_type = "General Carrier"

    # Fleet Size Calculation
    if pu == 0:
        fleet_size = "Zero Units"
    elif pu == 1:
        fleet_size = "Single Unit"
    else:
        fleet_size = "Multi Trucks"

    return {
        "equipment_type": equipment_type,
        "fleet_size": fleet_size,
        "is_broker": is_broker,
        "business_category": "Broker / Dispatch" if is_broker else "Motor Carrier"
    }
