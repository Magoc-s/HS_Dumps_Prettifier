"""
Source: 42's original cpp mapping tool
        42 Scientist

map<string,float> initmat() //List of things I'm looking out for
{
    map<string,float> res;
    res["HitPoints"]=-42; //Initialize to -42, to know I want it, and I'll change the value
    res["Mass"]=-42;
    res["MaxLinkLength"]=-42;
    res["MaxCompression"]=-42;
    res["MaxLength"]=-42;
    res["EnergyRunCost"]=-42;
    res["EnergyReclaim"]=-42;
    res["EnergyBuildCost"]=-42;
    res["BuildTime"]=-42;
    res["MaxExpansion"]=-42;
    res["MinLength"]=-42;
    res["MetalRepairCost"]=-42;
    res["Stiffness"]=-42;
    res["MetalReclaim"]=-42;
    res["ScrapTime"]=-42;
    res["MetalBuildCost"]=-42;
    return res;
}

map<string,float> initproj() //List of things I'm looking out for
{
    map<string,float> res;
    res["MaxAge"]=-42; //Initialize to -42, to know I want it, and I'll change the value
    res["ProjectileDamage"]=-42;
    res["WeaponDamageBonus"]=-42;
    res["Impact"]=-42;
    res["ProjectileSplashDamage"]=-42;
    res["ProjectileSplashDamageMaxRadius"]=-42;
    res["IncendiaryRadius"]=-42;
    res["RayDamage"]=-42;
    res["RayLength"]=-42;
    res["RayDamageLimit"]=-42;
    res["AntiAirHitpoints"]=-42;
    res["AntiAirDamage"]=-42;
    return res;
}

map<string,float> initdev() //List of things I'm looking out for
{
    map<string,float> res;
    res[    "BuildTimeComplete",]=-42; //Initialize to -42, to know I want it, and I'll change the value
    res[    "MetalRepairCost",]=-42;
    res[    "MetalCost",]=-42;
    res[    "EnergyCost",]=-42;
    res[    "ScrapPeriod",]=-42;
    res[    "SelectionWidth",]=-42;
    res[    "SelectionHeight",]=-42;
    res[    "Mass",]=-42;
    res[    "WeaponMass",]=-42;
    res[    "HitPoints",]=-42;
    res[    "Scale",]=-42;
    res[    "RoundsEachBurst",]=-42;
    res[    "ReloadTime",]=-42;
    res[    "FireStdDev",]=-42;
    res[    "FireStdDevAuto",]=-42;
    res[    "Recoil",]=-42;
    res[    "EnergyFireCost",]=-42;
    res[    "MetalFireCost",]=-42;
    res[    "EnergyProductionRate",]=-42;
    res[    "MetalProductionRate",]=-42;
    res[    "EnergyStorageCapacity",]=-42;
    res[    "MetalStorageCapacity",]=-42;
    res[    "DeviceSplashDamage",]=-42;
    res[    "DeviceSplashDamageMaxRadius",]=-42;
    res[    "StructureSplashDamage",]=-42;
    res[    "StructureSplashDamageMaxRadius",]=-42;
    res[    "IncendiaryRadius",]=-42;
    return res;
}
"""

RELEVANT_MATERIALS_VARS = [
    "HitPoints",
    "Mass",
    "MaxLinkLength",
    "MaxCompression",
    "MaxLength",
    "EnergyRunCost",
    "EnergyReclaim",
    "EnergyBuildCost",
    "BuildTime",
    "MaxExpansion",
    "MinLength",
    "MetalRepairCost",
    "Stiffness",
    "MetalReclaim",
    "ScrapTime",
    "MetalBuildCost"
]

RELEVANT_PROJECTILES_VARS = [
    "MaxAge",
    "ProjectileDamage",
    "WeaponDamageBonus",
    "Impact",
    "ProjectileSplashDamage",
    "ProjectileSplashDamageMaxRadius",
    "IncendiaryRadius",
    "RayDamage",
    "RayLength",
    "RayDamageLimit",
    "AntiAirHitpoints",
    "AntiAirDamage"
]

RELEVANT_DEVICES_VARS = [
    "BuildTimeComplete",
    "MetalRepairCost",
    "MetalCost",
    "EnergyCost",
    "ScrapPeriod",
    "SelectionWidth",
    "SelectionHeight",
    "Mass",
    "WeaponMass",
    "HitPoints",
    "Scale",
    "RoundsEachBurst",
    "ReloadTime",
    "FireStdDev",
    "FireStdDevAuto",
    "Recoil",
    "EnergyFireCost",
    "MetalFireCost",
    "EnergyProductionRate",
    "MetalProductionRate",
    "EnergyStorageCapacity",
    "MetalStorageCapacity",
    "DeviceSplashDamage",
    "DeviceSplashDamageMaxRadius",
    "StructureSplashDamage",
    "StructureSplashDamageMaxRadius",
    "IncendiaryRadius"
]


"""
This is the mapping table that gets used for writing up the intermediate dict into yaml files

If you wish to modify what variables it copies into the output files, feel free to pick a different
list for the key-value pair, or define a new one
"""
SEARCH_MAPPING: dict[str, list[str]] = {
    "MATERIALS": RELEVANT_MATERIALS_VARS,
    "PROJECTILES": RELEVANT_PROJECTILES_VARS,
    "DEVICES": RELEVANT_DEVICES_VARS,
    "WEAPONS": RELEVANT_DEVICES_VARS,
    "SCRIPTED": RELEVANT_DEVICES_VARS
}
