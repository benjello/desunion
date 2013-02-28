# /usr/bin/env python-
# -*- coding:utf-8 -*-


import os

from datetime import datetime
from numpy import ones
from pandas import DataFrame, concat, Series, ExcelWriter

from src import SRC_PATH
from src.parametres.paramData import XmlReader, Tree2Object
from desunion import DesunionSimulation

def get_asf(nbenf, year = 2011):
    param_file = os.path.join(SRC_PATH, 'countries', 'france', 'param', 'param.xml')
    date_str = str(year)+ '-01-01'
    datesim = datetime.strptime(date_str ,"%Y-%m-%d").date()
    reader = XmlReader(param_file, datesim)
    rootNode = reader.tree
    P = Tree2Object(rootNode, defaut=True)
    
    return round(nbenf * 12 * P.fam.af.bmaf * P.fam.asf.taux1, 2)


def get_children(e, ea, temps_garde = "classique", pension = None):
    
    children = dict()
    if pension is not None:
        pension_per_child = pension/(e+ea)
    for i in range(1,e+1):
        name = u"enfant " + str(i)    
        children[name] = {'birth' : "2002-01-01", 'temps_garde' : temps_garde, 'non_custodian' : 'chef'}
        if pension is not None:
            children[name].update({'pension' : pension_per_child}) 
            
    for j in range(e+1,e+ea+1):
        name = u"enfant " + str(j)
        children[name] = {'birth' : "1996-01-01", 'temps_garde' : temps_garde, 'non_custodian' : 'chef'}
        if pension is not None:
            children[name].update({'pension' : pension_per_child})
    
    return children


def get_test_case(children, sal_chef_smic, sal_part_smic, uc_parameters = None, pension = None, disabled = None, year = 2011):
    
    desunion = DesunionSimulation()
    desunion.set_config(nmen = 1, year = year)
    desunion.set_param()
    
    sal_chef = sal_chef_smic*1072*12  # TODO: for 2011
    sal_part = sal_part_smic*1072*12
    
    desunion.set_children(children)
        
    desunion.create_couple(sal_chef, sal_part)    
    desunion.set_pension(pension=pension)
    desunion.break_union()
    if uc_parameters is not None:    
        desunion.set_uc_parameters(uc_parameters)

    if disabled is not None:
        desunion.disable_prestations(disabled)   

    return desunion


def get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde = "classique", uc_parameters = None, pension = None, disabled = None):
    children =  get_children(e, ea, temps_garde, pension)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part, uc_parameters=uc_parameters, pension=pension, disabled=disabled)
    df = test_case.diag()
    
     
    s= DataFrame( {'enfant de moins de 14 ans' : e*ones(len(df)),
                   'enfant de plus de 14 ans' : ea*ones(len(df)),
                   'rev_smic_chef' :  rev_smic_chef*ones(len(df)),
                   'rev_smic_part' :  rev_smic_part*ones(len(df)),
                   'temps_garde' :  [temps_garde]*len(df), 
                   'alpha' : test_case.uc_parameters['alpha']*ones(len(df)),
                   'beta' : test_case.uc_parameters['beta']*ones(len(df)),
                   'gamma' : test_case.uc_parameters['gamma']*ones(len(df))
                   })
    df = concat([ s, df], axis = 1) 

    return df
