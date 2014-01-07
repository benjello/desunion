# /usr/bin/env python-
# -*- coding:utf-8 -*-

'''
Created on 17 janv. 2013

@author: PYC MBJ
'''


from scripts.unaf import get_unaf
    

COUNTRY = "france"
DIR = u"C:/Users/Utilisateur/Dropbox/CAS/Désunions/"    
YEAR = 2011
EPS = 1e-3

from pandas import concat
from numpy import arange
from scripts.utils import get_children, get_results_df, get_asf, get_test_case, compute_optimal_pension


def compute_and_save_bareme(disable_api = False):

    csv_file = DIR + 'bareme_new.csv'  

    nb_enf_max = 4
    nb_enf_max_14 = 0
    rev_smic_max = 4 
    rev_smic_step = .5
    temps_garde_range = ['classique', 'alternee_pension_non_decl', 'alternee_pension_decl']

    disabled = None
    if disable_api:
        disabled = ['api'] + ["majo_rsa"]
    else:
        disabled = []

    first = True

    for uc_parameters in [ {'alpha' : 0, 'beta' : .5, 'gamma' : 1}, {'alpha' : 0.4, 'beta' : .7, 'gamma' : 1.4}]:  
        for nb_enf in range(1,nb_enf_max+1):
            for ea in range(0,nb_enf_max_14+1):
                e = nb_enf - ea
                for temps_garde in temps_garde_range:
                    disabled += ['asf']
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
        csv_file = DIR  + 'opt_pension_new.csv'

    nb_enf_max = 4
    nb_enf_max_14 = 0
    rev_smic_max = 4 
    rev_smic_step = .5
    temps_garde_range = ['classique', 'alternee_pension_non_decl', 'alternee_pension_decl']
    first = True    
    disabled = None
    if disable_api:
        disabled = ['api'] + ["majo_rsa"]

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
                                    disabled = disabled + ['asf']
                                else:
                                    disabled = ['asf']
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



def build_all():
    pass

if __name__ == '__main__':
    compute_and_save_bareme(disable_api=True)