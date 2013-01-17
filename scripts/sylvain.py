# /usr/bin/env python
# -*- coding:utf-8 -*-

'''
Created on 17 janv. 2013

@author: PYC MBJ
'''

COUNTRY = 'france'
DIR = u"C:/Users/Utilisateur/Dropbox/CAS/Désunions/"    
YEAR = 2011

from pandas import DataFrame, concat
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




def test():
    app = QApplication(sys.argv)
    win = ApplicationWindow()

    

#    df = desunion.get_results_dataframe(index_by_code = True)
#    print desunion.scenario
#    print desunion.scenario_chef
#    print desunion.scenario_part


#    print df.to_string()
    
    df1, df2, df3, pub_cost_before, pub_cost_after = desunion.rev_disp(12*500)
    print df1
    print df2
    print df3
    print pub_cost_before
    print pub_cost_after
    
#    df.to_excel(destination_dir + 'file.xlsx', sheet_name='desunion')


def get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde = "classique" ):
    children =  get_children(e, ea, temps_garde)
    test_case = get_test_case(children, rev_smic_chef, rev_smic_part)

    (df_revdisp, df_nivvie, df_rev, df_public, public_cost_before, public_cost_after, parent_cost_before, 
     parent_cost_after, public_cost_after_chef, public_cost_after_part ) = test_case.diag()
#    print df_revdisp.to_string()
#    print df_nivvie
#    print 'public_cost_before :', public_cost_before
#    print 'public_cost_after_chef :', public_cost_after_chef
#    print 'public_cost_after_part :', public_cost_after_part
    df = DataFrame( [df_revdisp, df_nivvie])
    df = df[ ['couple', 'part', 'chef'] ]
    df = df.set_value(u"prise en charge publique de l'enfant", 'couple', public_cost_before)
    df = df.set_value(u"prise en charge publique de l'enfant", 'chef', public_cost_after_chef)
    df = df.set_value(u"prise en charge publique de l'enfant", 'part', public_cost_after_part)

    from pandas import melt, Series
    from numpy import ones
    df = df.T
    df.index.name = u"ménage"
    df = df.reset_index() 
    s= DataFrame( {'enfant de moins de 14 ans' : e*ones(len(df)),
                   'enfant de plus de 14 ans' : ea*ones(len(df)),
                   'rev_smic_chef' :  rev_smic_chef*ones(len(df)),
                   'rev_smic_part' :  rev_smic_part*ones(len(df)),
                   'temps_garde' :  [temps_garde]*len(df) 
                   })
    #print s
    df = concat([df, s], axis = 1) 
#    df = melt(df,id_vars = 'index', value_vars = ['couple', 'part', 'chef'])
#    for household in ['couple', 'chef', 'part']:
#        df = df.set_value(u"Nombre d'enfant de moins de 14 ans", household, e)
#        df = df.set_value(u"Nombre d'enfant de plus de 14 ans", household, ea)


    return df
    
if __name__ == '__main__':

    
    from pandas import Series, ExcelWriter
    
    file = DIR = u"C:/Users/Utilisateur/Dropbox/CAS/Désunions/"  + 'test.xls'  
    excel_writer = ExcelWriter(file)
    
    first = True


    
    for nb_enf in range(1,1+1):
        for ea in range(0,1+1):            
            e = nb_enf - ea
            for temps_garde in ['classique']: #, 'alternee', 'reduite']:
                for rev_smic_chef in range(2):
                    for rev_smic_part in range(2):
                        df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde)
                        if first:
                            df_final = df   
                            first = False
                        else:
                            df_final = concat([df_final, df], axis=0)
                            
    df_final.to_excel(excel_writer, float_format = "%.0f")
    excel_writer.save()

#    nb_enf = 1
#    ea = 0
#    e = 1
#    rev_smic_chef = 1
#    rev_smic_part = 1
#    temps_garde = "classique"
#    df = get_results_df(e, ea, rev_smic_chef, rev_smic_part, temps_garde)
#    print df
#    df_revdisp.concat()