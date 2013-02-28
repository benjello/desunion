# -*- coding:utf-8 -*-
# Created on 25 janv. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from __future__ import division 
from src.lib.simulation import ScenarioSimulation
from scipy.optimize import fixed_point


def get_loyer(scenario):
    yr = scenario.year    
    simu = ScenarioSimulation()
    simu.set_config(scenario= scenario, nmen = 1, year = yr, country = 'france')
    simu.set_param()


    def func(loyer):
        simu.scenario.menage[0].update({'loyer': loyer})                 
        data, data_default = simu.compute()
        revdisp = data['revdisp'].vals
        logt = data['logt'].vals 
        return float(((revdisp - logt)/3 + logt )/12) 
    
    return fixed_point(func, 0)


if __name__ == '__main__':
    
    pass
    


    
