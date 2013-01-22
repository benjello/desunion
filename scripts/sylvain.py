# /usr/bin/env python
# -*- coding:utf-8 -*-

'''
Created on 17 janv. 2013

@author: PYC MBJ
'''


COUNTRY = 'france'
DIR = u"C:/Users/Utilisateur/"#Dropbox/CAS/Désunions/"    
YEAR = 2011


from pandas import DataFrame, concat, Series, ExcelWriter
from desunion import DesunionSimulation

def get_children(e, ea, temps_garde = "classique"):
    
    children = dict()
    for i in range(1,e+1):
        name = u"enfant " + str(i)
        children[name] = {'birth' : "2002-01-01", 'temps_garde' : temps_garde, 'non_custodian' : 'chef'}
    for j in range(e+1,e+ea+1):
        name = u"enfant " + str(j)
        children[name] = {'birth' : "1996-01-01", 'temps_garde' : temps_garde, 'non_custodian' : 'chef'}
    return children


def get_test_case(children, sal_chef_smic, sal_part_smic):
    
    desunion = DesunionSimulation()
    desunion.set_config(nmen = 1, year = YEAR)
    desunion.set_param()
    
    sal_chef    = sal_chef_smic*1072*12  # 2011 !! 
    sal_part = sal_part_smic*1072*12
    
    desunion.set_children(children)

    desunion.create_couple(sal_chef, sal_part)
    
    desunion.set_pension()

    
    desunion.break_union()
    
    return desunion




def get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde = "classique" ):
    children =  get_children(e, ea, temps_garde)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part)

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
        for ea in range(0,2+1):            
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
    e = 1
    ea = 0
    rev_smic_chef = 1
    rev_smic_part = 1
    temps_garde ="alternee_pension_non_decl"
    df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde)
    print df.to_string()

if __name__ == '__main__':

    test2()
    