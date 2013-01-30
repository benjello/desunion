# /usr/bin/env python
# -*- coding:utf-8 -*-

'''
Created on 17 janv. 2013

@author: PYC MBJ
'''


COUNTRY = 'france'
DIR = u"C:/Users/Utilisateur/"#Dropbox/CAS/Désunions/"    
YEAR = 2009


from pandas import DataFrame, concat, Series, ExcelWriter
from desunion import DesunionSimulation

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


def get_test_case(children, sal_chef_smic, sal_part_smic, uc_parameters = None, pension = None):
    
    desunion = DesunionSimulation()
    desunion.set_config(nmen = 1, year = YEAR)
    desunion.set_param()
    
    sal_chef    = sal_chef_smic*1072*12  # 2011 !! 
    sal_part = sal_part_smic*1072*12
    
    desunion.set_children(children)
        
    desunion.create_couple(sal_chef, sal_part)    
    desunion.set_pension(pension=pension)
    desunion.break_union()
    if uc_parameters is not None:    
        desunion.set_uc_parameters(uc_parameters)
    
    return desunion




def get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde = "classique", uc_parameters = None, pension = None):
    children =  get_children(e, ea, temps_garde, pension)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part, uc_parameters=uc_parameters, pension=pension )
    df = test_case.diag()

    from numpy import ones
     
    s= DataFrame( {'enfant de moins de 14 ans' : e*ones(len(df)),
                   'enfant de plus de 14 ans' : ea*ones(len(df)),
                   'rev_smic_chef' :  rev_smic_chef*ones(len(df)),
                   'rev_smic_part' :  rev_smic_part*ones(len(df)),
                   'temps_garde' :  [temps_garde]*len(df) 
                   })
    #print s
    df = concat([ s, df], axis = 1) 

    return df



    
    

def compute_and_save():

    file = DIR = u"C:/Users/Utilisateur/Dropbox/CAS/Désunions/"  + 'test.xls'  
    excel_writer = ExcelWriter(file)
    
    first = True
    
    for nb_enf in range(1,3+1):
        for ea in range(0,nb_enf+1):            
            e = nb_enf - ea
            for temps_garde in ['classique', 'alternee_pension_non_decl', 'alternee_pension_decl', 'reduite']:
                for rev_smic_chef in range(4):
                    for rev_smic_part in range(4):
                        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde)
                        if first:
                            df_final = df   
                            first = False
                        else:
                            df_final = concat([df_final, df], axis=0)
                            
    df_final.to_excel(excel_writer, float_format = "%.0f")
    excel_writer.save()

def test():
    e = 1
    ea = 0
    rev_smic_chef = 1
    rev_smic_part = 1
    temps_garde ="alternee_pension_non_decl"
    children =  get_children(e, ea, temps_garde)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part)
    
    df = test_case.get_results_dataframe()
     
    print df.to_string()

def test2():
    e = 2
    ea = 0
    rev_smic_chef = 3
    rev_smic_part = 3

    temps_garde ="classique"
    uc_parameters = {'alpha' : 0, 'beta' : .5, 'gamma' : 1}
    df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, pension = None)
    print df.to_string()
    
    
def test3():
    e = 2
    ea = 0
    rev_smic_chef = 3
    rev_smic_part = 3
    temps_garde ="classique"
    uc_parameters = {'alpha' : 0, 'beta' : .5, 'gamma' : 1}
    
    compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = uc_parameters, 
                            criterium = "revdisp")

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
def compute_optimal_pension(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters = None , criterium = None):
    from scipy.optimize import fixed_point, fsolve

    def func_optimal_pension(pension): 
        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde, uc_parameters=uc_parameters, pension=pension)
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
        elif criterium == "same_total_cost_pyc":
            opt_pension = (total_cost_before - public_cost_after_chef - public_cost_after_part)*nivvie_chef_after/(nivvie_chef_after+nivvie_part_after)-private_cost_after_chef        
        elif criterium == "same_total_cost":
            return total_cost_after_chef+total_cost_after_part-total_cost_before
        
        return opt_pension 
    
    if criterium == "same_total_cost":
        optimal_pension, infodict, ier, mesg = fsolve(func_optimal_pension, 10000, xtol = 1e-5)
        print optimal_pension, infodict, ier, mesg
    else:
        optimal_pension = fixed_point(func_optimal_pension, 0, xtol = 1e-5)

    return optimal_pension 

    

    






if __name__ == '__main__':

    test3()
    