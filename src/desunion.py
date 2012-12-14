# /usr/bin/env python
# -*- coding:utf-8 -*-

'''
Created on 12 oct. 2012

@author: Pyke75, benjello
'''

import sys
from PyQt4.QtGui import QMainWindow, QApplication
from src.widgets.matplotlibwidget import MatplotlibWidget
from pandas import DataFrame

from src.core.simulation import ScenarioSimulation
from src.france.utils import Scenario


from pandas import concat

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        

from datetime import datetime    


class DesunionSimulation(ScenarioSimulation):
    """
    A simulation class for a couple that will get separated 
    """
    def __init__(self):
        super(DesunionSimulation, self).__init__()

        self.scenario_chef = None
        self.scenario_part = None

        self.pension_alimentaire = None
        self.children = dict() # {noi: {'non_custodian': None, 'temps_garde': None, 'pension_alim': None}
        # du point de vue du parent non gardien
        # garde_classique
        # garde_alternée
        # garde_réduite

        self.new_households = dict() # For example { 'chef': { 'so': 1, 'loyer' : 500}}
        

    def break_union(self):

        scenario = self.scenario        
        scenario_chef = Scenario()
        scenario_part = Scenario()
        scenario_chef.year = self.datesim.year
        scenario_part.year = self.datesim.year

        sal_chef = scenario.indiv[0]['sali']   # Could be more general
        scenario_chef.indiv[0].update({'sali': sal_chef })
        
        sal_part = scenario.indiv[1]['sali']   # Could be more general
        scenario_part.indiv[0].update({'sali': sal_part })
        
        # TODO: get more infos from couple scenario

        noi_enf_part = 1
        noi_enf_chef = 1
        alv_chef = 0
        alv_part = 0
        alr_chef = 0
        alr_part = 0
        
        for noi, val in self.children.iteritems():
            non_custodian = val['non_custodian']
            temps_garde = val['temps_garde']
            pension_alim = val['pension_alim']
            birth = scenario.indiv[noi]['birth']


            if temps_garde in ['classique', 'réduite']:

                if non_custodian == 'chef':
                    scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf') 
                    noi_enf_part += 1
                    alv_chef += pension_alim
                    alr_part += pension_alim
                elif non_custodian == 'part':
                    scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf') 
                    noi_enf_chef += 1
                    alv_part += pension_alim
                    alr_chef += pension_alim  
                
            elif temps_garde == 'alternée':# TODO: garde alternée pas de pension alimentaire ?
                                            # garde alternée juridique ou pas
                
                scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf') 
                noi_enf_part += 1
                scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf')
                noi_enf_part += 1
                
                if non_custodian == 'chef':
                    alv_chef += pension_alim
                    alr_part += pension_alim    
                elif non_custodian == 'part':
                    alv_part += pension_alim
                    alr_chef += pension_alim
                    
            else:
                raise Exception('break_union: Error somewhere')
                
        # Updating pension alimentaire
        # Beware : received pension alim. are attributed for individuals
        #          paid pension alim. are "charges déductibes" on foyers' declarations  
            alv_net_chef = alv_chef - alr_chef
            if alv_net_chef >= 0:
                scenario_chef.declar[0].update({'f6gu': alv_net_chef}) # TODO: pas forcément en 6gu 
                scenario_part.indiv[0].update({'alr': alv_net_chef})
            else:
                scenario_chef.indiv[0].update({'alr': -alv_net_chef})
                scenario_part.declar[0].update({'f6gu': -alv_net_chef})
                
        # Updating households
        
        for parent, variables in self.new_households:
            if parent == 'chef':
                for key, val in variables:
                    scenario_chef.menage[0].update({key: val})
            elif parent == 'part':
                for key, val in variables:
                    scenario_part.menage[0].update({key: val})
                
        
        self.scenario_chef = scenario_chef
        self.scenario_part = scenario_part
        self.scenario_chef.nmen = 1
        self.scenario_part.nmen = 1
        
    def set_children(self, children):
        """
        Sets the children involved
        children is a dict of dict of the form 
        {'MyName': {'birth': "2000-01-01", 'non_custodian' : 'chef', 
                    'temps_garde': 'classique', 'pension_alim' : 1000}}
         
        """ 
        self.children = dict()
        noi = 2
        for name, vars_dict in children.iteritems():
            self.children[noi] = vars_dict
            self.children[noi]['birth'] =  datetime.strptime(children[name]['birth'] ,"%Y-%m-%d").date()
            noi += 1
         

    def create_united_couple(self, sal_chef, sal_part, date = None):
        '''
        Construction du couple avant désunion TODO: translate in english
        '''
         
        scenario = self.scenario
        
        scenario.addIndiv(1, datetime.strptime("1975-01-01" ,"%Y-%m-%d").date(), "conj", "part")
            
        for noi, child in self.children.iteritems():
            scenario.addIndiv(noi, child['birth'], "pac", "enf" )  
        
        scenario.indiv[0].update({ 'sali': sal_chef })
        scenario.indiv[1].update({ 'sali': sal_part})
    

    def compute(self, difference):
        """
        Computes data_dict  from scenari
        """
        from src.core.datatable import DataTable
        from src.core.utils import gen_output_data
        
        scenari = { 'couple' : self.scenario, 
                    'chef'   : self.scenario_chef, 
                    'part'   : self.scenario_part }
        datas = dict()
        
        for name, scenario in scenari.iteritems():
            input_table = DataTable(self.InputTable, scenario = scenario, datesim = self.datesim, country = self.country)
            output, output_default = self._preproc(input_table)
        
            data = gen_output_data(output, filename = self.totaux_file)        
            data_default = gen_output_data(output_default, filename = self.totaux_file) # TODO: take gen_output_data form core.utils
            
            if self.reforme:
                output_default.reset()
                data_default = gen_output_data(output_default, filename = self.totaux_file) # TODO: take gen_output_data form core.utils
                if difference:
                    data.difference(data_default)            
            else:
                data_default = data
                
            datas[name] = {'data' : data, 'default': data_default}


        return datas
    
    
    def get_results_dataframe(self, default = False, difference = True, index_by_code = False):
        '''
        Formats data into a dataframe
        '''

        datas = self.compute(difference = difference)
        dfs = dict()
        
        for scenario, dico in datas.iteritems():
            data = dico['data']
            data_default = dico['default']

            data_dict = dict()
            index = []
            
            if default is True:
                data = data_default
            
            for row in data:
                if not row.desc in ('root'):
                    if index_by_code is True:
                        index.append(row.code)
                        data_dict[row.code] = row.vals
                    else:
                        index.append(row.desc)
                        data_dict[row.desc] = row.vals
                    
            df = DataFrame(data_dict).T
            df = df.reindex(index)
            df = df.rename(columns = {0: scenario})
            
            dfs[scenario] = df
        
        first = True

        for df in dfs.itervalues():
            if first:
                df_final = df
                first = False
            else:
                df_final = concat([df_final, df], axis=1, join ="inner")
                
        print "final"
        df_final = df_final
        print df_final.to_string()
        return df_final

if __name__ == '__main__':

    
    app = QApplication(sys.argv)
    win = ApplicationWindow()    

    country = 'france'
    destination_dir = u"C:/Users/Utilisateur/Dropbox/CAS/Désunions/"    
    yr = 2010

    desunion = DesunionSimulation()
    desunion.set_config(nmen = 1, year = yr)
    desunion.set_param()

    
    children =  {'Riri': {'birth': "2000-01-01", 'non_custodian' : 'chef', 
                    'temps_garde': 'classique', 'pension_alim' : 12*500},
                 'Fifi': {'birth': "2002-01-01", 'non_custodian' : 'chef', 
                    'temps_garde': 'classique', 'pension_alim' : 12*500}
                 }

    sal_chef    = 30000 
    sal_part = 15000
    desunion.set_children(children)
    desunion.create_united_couple(sal_chef, sal_part)


    
    
    desunion.break_union()     

    df = desunion.get_results_dataframe()
#    print desunion.scenario_chef
#    print desunion.scenario_part
    print df.to_string()

    df.to_excel(destination_dir + 'file.xlsx', sheet_name='desunion')

    
