# /usr/bin/env python-
# -*- coding:utf-8 -*-

'''
Created on 17 janv. 2013

@author: PYC MBJ
'''


from scipy.optimize import fixed_point, fsolve

COUNTRY = 'france'
DIR = u"C:/Users/Utilisateur/Dropbox/CAS/Désunions/"    
YEAR = 2011
EPS = 1e-3

from pandas import concat
from numpy import arange

from scripts.utils import get_children, get_results_df, get_asf, get_test_case


def compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = None , criterium = None, disabled = None):

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
        
#        opt_pension = private_cost_after*(revdisp_chef + pension)/(revdisp_chef+revdisp_part) - total_cost_after_chef + public_cost_after_chef

        private_cost_after_chef = df.get_value(u"chef", u"prise en charge privée de l'enfant")        

        if criterium == "revdisp":
            opt_pension = private_cost_after*revdisp_chef/(revdisp_chef+revdisp_part)-private_cost_after_chef
        elif criterium == "nivvie":
            opt_pension = private_cost_after*nivvie_chef_after/(nivvie_chef_after+nivvie_part_after)-private_cost_after_chef
        elif criterium == "revdisp_pyc":
            opt_pension = private_cost_after*(revdisp_chef+pension)/(revdisp_chef+revdisp_part)-private_cost_after_chef    
        elif criterium == "jacquot":
            alpha = uc_parameters['alpha']
            beta = uc_parameters['beta']
            gamma = uc_parameters['gamma']
            A = (.3*e + .5*ea)/(1 + .3*e + .5*ea)
            B = (alpha*gamma*(.3*e + .5*ea))/(1 + alpha*gamma*(.3*e + .5*ea))
            C = 1 + .3*e + .5*ea
            D = 1 + alpha*gamma*(.3*e + .5*ea)
            opt_pension = ((A-B)*revdisp_chef*revdisp_part)/((revdisp_chef/C) + (revdisp_part/D))
        elif criterium == "same_total_cost":
            return total_cost_after_chef+total_cost_after_part-total_cost_before
        
        return opt_pension 
    
    if criterium == "same_total_cost":
        optimal_pension, infodict, ier, mesg = fsolve(func_optimal_pension, 10000, xtol = EPS)
        print optimal_pension, infodict, ier, mesg
    else:
        try :
            optimal_pension = fixed_point(func_optimal_pension, 0, xtol = EPS, maxiter = 10)
        except RuntimeError:
            optimal_pension = 10000
    
    return optimal_pension




def compute_and_save_bareme(disable_api = False):

    csv_file = DIR + 'bareme_new.csv'  

    nb_enf_max = 4
    nb_enf_max_14 = 0
    rev_smic_max = 4 
    rev_smic_step = .5
    temps_garde_range = ['classique', 'alternee_pension_non_decl', 'alternee_pension_decl']

    disabled = None
    if disable_api:
        disabled = ['api']

    first = True

    for uc_parameters in [ {'alpha' : 0, 'beta' : .5, 'gamma' : 1}, {'alpha' : 0.4, 'beta' : .7, 'gamma' : 1.4}]:  
        for nb_enf in range(1,nb_enf_max+1):
            for ea in range(0,nb_enf_max_14+1):            
                e = nb_enf - ea
                for temps_garde in temps_garde_range:
                    for rev_smic_chef in arange(0,rev_smic_max, rev_smic_step):
                        for rev_smic_part in arange(0,rev_smic_max, rev_smic_step):
                            df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, disabled=disabled)
                            print df
                            if first:
                                df_final = df  
                                first = False
                            else:
                                df_final = concat([df_final, df], axis=0)
                            
    df_final.to_csv(csv_file)
    
    
def compute_and_save_opt_pension(criterium, disable_api = False):


    if disable_api:
        csv_file = DIR  + 'opt_pension_no_api.csv'  
    else:
        csv_file = DIR  + 'opt_pension.csv'

    nb_enf_max = 4
    nb_enf_max_14 = 0
    rev_smic_max = 4 
    rev_smic_step = .5
    temps_garde_range = ['classique', 'alternee_pension_non_decl', 'alternee_pension_decl']
    first = True
    disabled = None
    if disable_api:
        disabled = ['api']

    for uc_parameters in [ {'alpha' : 0, 'beta' : .5, 'gamma' : 1}, {'alpha' : 0.4, 'beta' : .7, 'gamma' : 1.4}]:  
        for nb_enf in range(1,nb_enf_max+1):
            for ea in range(0,nb_enf_max_14+1):            
                e = nb_enf - ea
                for temps_garde in temps_garde_range:
                    for rev_smic_chef in arange(0,rev_smic_max, rev_smic_step):
                        for rev_smic_part in arange(0,rev_smic_max, rev_smic_step):                 
                            opt_pension = compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, criterium = criterium, disabled=disabled)
                            asf = get_asf(nb_enf, year=YEAR)
                            if opt_pension >= asf:
                                if disabled is not None:
                                    disabled += ['asf']
                                else:
                                    disabled += ['asf'] 
                                df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = opt_pension, disabled = disabled)
                            else:
                                df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = 0, disabled = disabled)
                            
                            print df
                            if first:
                                df_final = df  
                                first = False
                            else:
                                df_final = concat([df_final, df], axis=0)
                            df_final.to_csv(csv_file)    
    


def pension_according_to_bareme(disable_api=False):
    e = 2
    ea = 0
    rev_smic_chef = 3
    rev_smic_part = 3
    disabled = None
    if disable_api:
        disabled = ['api']

    temps_garde ="alternee_pension_non_decl" # alternee_pension_non_decl', 'alternee_pension_decl

    uc_parameters = {'alpha' : 0, 'beta' : .5, 'gamma' : 1}
    df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = None, disabled=disabled)
    print df.to_string()
    
def optimal_pension(criterium, disable_api = False):
    e = 4
    ea = 0
    rev_smic_chef = 0.5
    rev_smic_part = 0
    temps_garde ="classique" # alternee_pension_non_decl', 'alternee_pension_decl
    uc_parameters = {'alpha' : 0, 'beta' : .5, 'gamma' : 1}

    disabled = []
    if disable_api:
        disabled += ['api']
    
    opt_pension = compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, 
                            criterium = criterium, disabled=disabled)
 
    asf = get_asf(e+ea, year=YEAR)
    print 'opt_pension :', opt_pension  
    print 'asf :', asf  
    if opt_pension >= asf:
        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = opt_pension, disabled = disabled + ['asf'] )
    else:
        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = 0, disabled=disabled)
    
    print df.to_string()
    
    
    # 3,3
    # bareme : 8863
    # revdisp : pension = 4863
    # nivvie : pension = 6243 (égalisation des niveaux de vie)
    # revdisp_pyc : pension = 5803
    # jacquot : 6243
   
    # 3,0
    # nivvie : pension = - 1324 ! (le parent non gardien paie une pension)
    
    # 3,1
    # jacquot pensio, 3387 alpha' : 0.3, 'beta' : .5, 'gamma' : 1.3}
    

def test():
    e = 2
    ea = 0
    rev_smic_chef = 2
    rev_smic_part = 2
    temps_garde ="classique"
    children =  get_children(e, ea, temps_garde)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part)
    
    df = test_case.get_results_dataframe()
     
    print df.to_string()
       
 



if __name__ == '__main__':
#   compute_and_save_bareme()
    optimal_pension("nivvie", disable_api=True)
