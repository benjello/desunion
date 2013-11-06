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



def pension_according_to_bareme(disable_api=False):
    e = 2
    ea = 0
    rev_smic_chef = 1.5
    rev_smic_part = 1.5
    disabled = None
    if disable_api:
        disabled = ['api']
    else:
        disabled = []

    temps_garde = "alternee_pension_non_decl"  #'alternee_pension_decl' # "alternee_pension_non_decl" "classique" 

    uc_parameters = {'alpha' : 0.4, 'beta' : 0.7, 'gamma' : 1.4}
    
    if temps_garde == "alternee_pension_non_decl":
        disabled += ['asf']
         
    df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = None, disabled=disabled)
    print df.to_string()
    
def optimal_pension(criterium, disable_api = False):
    e = 2
    ea = 0
    rev_smic_chef = 3.5
    rev_smic_part = 0
    temps_garde ="alternee_pension_non_decl" # 'classique', 'alternee_pension_decl
    uc_parameters = {'alpha' : 0.4, 'beta' : .7, 'gamma' : 1.4}

    disabled = []
    if disable_api:
        disabled += ['api']
    
    if criterium == "unaf":
        print get_unaf(e,ea)
        opt_pension_nv = compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, 
                                criterium = "nivvie", disabled=disabled)
        print "nivvie : ", opt_pension_nv
          
        opt_pension_unaf = compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, 
                                criterium = "unaf", disabled=disabled)
        print "unaf : ", opt_pension_unaf    
        opt_pension = max(opt_pension_nv, opt_pension_unaf)
    else: 
        opt_pension = compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, 
                                criterium=criterium, disabled=disabled)
        
    asf = get_asf(e+ea, year=YEAR)
    
    print 'opt_pension :', opt_pension  
    print 'asf :', asf  
    if opt_pension >= asf:
        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = opt_pension, disabled = disabled + ['asf'] )
    else:
        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = 0, disabled=disabled)
    
    print df.to_string()
    return df
    

    
def test_unaf():
    e = 2
    ea = 0
    rev_smic_chef = 1.5
    rev_smic_part = 1.5
    temps_garde ="classique" # alternee_pension_non_decl', 'alternee_pension_decl
    uc_parameters = {'alpha' : 0, 'beta' : .5, 'gamma' : 1}
    print get_unaf(e,ea,a=1)
    disabled = None
    
    opt_pension_unaf = compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, 
                            criterium = "unaf2", disabled=disabled)
    print "unaf2 : ", opt_pension_unaf    


def test():
    e = 2
    ea = 0
    rev_smic_chef = 1.5
    rev_smic_part = 1.5
    temps_garde ="classique"
    children =  get_children(e, ea, temps_garde)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part)
    df = test_case.get_results_dataframe()     
    print df.to_string()


    


if __name__ == '__main__':

#    pension_according_to_bareme(disable_api=True)
#    df1 =  optimal_pension("same_total_cost", disable_api=True)
#    df2 = optimal_pension("nivvie", disable_api=True)
#    optimal_pension("share_private_cost_before_part_nivvie_after", disable_api=True)
#    optimal_pension("share_private_cost_before_chef_nivvie_after", disable_api=True)
#    for df in [df0, df1, df2]:
#        print df.to_string()
#    test_unaf()
#    print get_unaf(2,0)
    pension_according_to_bareme(disable_api=True)
#    test()