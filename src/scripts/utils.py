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
    """
    Build a simplified DesunionSimulation() object from a list of parameters 
    """
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
    s  = DataFrame( {'enfant de moins de 14 ans' : e*ones(len(df)),
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



def compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters=None, criterium=None, disabled=None):
    """
    Return optimal pension according to different criteria
    
    Parameters
    ----------
    e : number of kids 
    ea : number of teenagers
    rev_smic_chef : revenue of the non custodian parent (in SMIC)
    rev_smic_part : revenue of the custodian parent (in SMIC)
    temps_garde : type of custody
    uc_parameters : parameters to compute the household consumption units
    criterium : the normative criteria used to compute the optimal pension
    disabled : the disabled presattions of the socio-fiscal model
    
    Returns
    -------
    optimal_pension : the optimal pension  
    """
    EPS = 1e-3
    
    from scipy.optimize import fixed_point, fsolve
    from scripts.unaf import get_unaf
    dep_decent_unaf = get_unaf(e, ea)
    dep_decent_unaf2 = get_unaf(e, ea, a=1)

    # Define a useful function
    def func_optimal_pension(pension):
         
        if disabled is None:
            dis =  ["asf"]
        elif "asf" not in disabled:
            dis = disabled + ['asf']
            
        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters=uc_parameters, pension=pension, disabled=dis)
        print df.to_string()
        df = df.set_index([u"ménage"])
        private_cost_after = ( df.get_value(u"chef", u"prise en charge privée de l'enfant") +
                             df.get_value(u"part", u"prise en charge privée de l'enfant") )
        revdisp_chef = df.get_value(u"chef", u"revdisp")
        revdisp_part = df.get_value(u"part", u"revdisp")
        
        total_cost_after_chef = df.get_value(u"chef", u"dépense totale pour enfants")
        total_cost_after_part = df.get_value(u"part", u"dépense totale pour enfants")
        total_cost_before = df.get_value(u"couple", u"dépense totale pour enfants")
        public_cost_after_chef = df.get_value(u"chef", u"prise en charge publique de l'enfant")
        public_cost_after_part = df.get_value(u"part", u"prise en charge publique de l'enfant")

        nivvie_chef_after = df.get_value(u"chef", u"nivvie")
        nivvie_part_after = df.get_value(u"part", u"nivvie")
        nivvie_chef_before = df.get_value(u"chef", u"nivvie")/df.get_value(u"chef", u"nivvie_loss")
        nivvie_part_before = df.get_value(u"part", u"nivvie")/df.get_value(u"part", u"nivvie_loss")
        
#        opt_pension = private_cost_after*(revdisp_chef + pension)/(revdisp_chef+revdisp_part) - total_cost_after_chef + public_cost_after_chef

        private_cost_after_chef = df.get_value(u"chef", u"prise en charge privée de l'enfant")        
        private_cost_after_part = df.get_value(u"part", u"prise en charge privée de l'enfant")
        private_cost_before = df.get_value(u"couple", u"prise en charge privée de l'enfant")
        

        if criterium == "revdisp":
            opt_pension = private_cost_after*revdisp_chef/(revdisp_chef+revdisp_part)-private_cost_after_chef
        elif criterium == "nivvie":
            opt_pension = private_cost_after*nivvie_chef_after/(nivvie_chef_after+nivvie_part_after)-private_cost_after_chef
        elif criterium == "revdisp_pyc":
            opt_pension = private_cost_after*(revdisp_chef+pension)/(revdisp_chef+revdisp_part)-private_cost_after_chef    
        elif criterium == "jacquot":
            alpha = uc_parameters['alpha']
            beta  = uc_parameters['beta']
            gamma = uc_parameters['gamma']
            A = (.3*e + .5*ea)/(1 + .3*e + .5*ea)
            B = (alpha*gamma*(.3*e + .5*ea))/(1 + alpha*gamma*(.3*e + .5*ea))
            C = 1 + .3*e + .5*ea
            D = 1 + alpha*gamma*(.3*e + .5*ea)
            opt_pension = ((A-B)*revdisp_chef*revdisp_part)/((revdisp_chef/C) + (revdisp_part/D))
        elif criterium == "share_private_cost_before_chef":
            opt_pension = - private_cost_after_chef  + private_cost_before*nivvie_chef_before/(nivvie_chef_before+nivvie_part_before)
        
        elif criterium == "share_private_cost_before_part":
            opt_pension = private_cost_after_part  - private_cost_before*nivvie_part_before/(nivvie_chef_before+nivvie_part_before)
        
        elif criterium == "share_private_cost_before_chef_nivvie_after":
            opt_pension = - private_cost_after_chef  + private_cost_before*nivvie_chef_after/(nivvie_chef_after+nivvie_part_after)
        
        elif criterium == "share_private_cost_before_chef_nivvie_after_coef":
            opt_pension = - private_cost_after_chef  + 1.4*private_cost_before*nivvie_chef_after/(nivvie_chef_after+nivvie_part_after)
        
        elif criterium == "share_private_cost_before_part_nivvie_after":
            opt_pension = private_cost_after_part  - private_cost_before*nivvie_part_after/(nivvie_chef_after+nivvie_part_after)
        
        elif criterium == "same_total_cost":
            return total_cost_after_chef+total_cost_after_part-total_cost_before
        
        elif criterium == "unaf":
            return total_cost_after_part - dep_decent_unaf
        
        elif criterium == "unaf2":
            return revdisp_part - dep_decent_unaf2
        return opt_pension 
    
    if criterium == "same_total_cost" or criterium in ["unaf", "unaf2"]:
        res = fsolve(func_optimal_pension, 10000, xtol = EPS)
        print res
        optimal_pension = res[0]
    else:
        try :
            optimal_pension = fixed_point(func_optimal_pension, 0, xtol = EPS, maxiter = 10)
        except RuntimeError:
            optimal_pension = 10000
    
    return optimal_pension

