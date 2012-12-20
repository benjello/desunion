# /usr/bin/env python
# -*- coding:utf-8 -*-

'''
Created on 12 oct. 2012

@author: Pyke75, benjello
'''

from __future__ import division 
import sys
from PyQt4.QtGui import QMainWindow, QApplication
from src.widgets.matplotlibwidget import MatplotlibWidget
from pandas import DataFrame

from src.core.simulation import ScenarioSimulation



from pandas import concat

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.mplwidget = MatplotlibWidget(self)
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        

from datetime import datetime    

# TODO check the statmarit, quimen, quifam add check consistency



class DesunionSimulation(ScenarioSimulation):
    """
    A simulation class for a couple that will get separated 
    """
    def __init__(self):
        super(DesunionSimulation, self).__init__()

        self.scenario_chef = None # scenario_chef est donc un attribut de la classe DesunionSimulation
        self.scenario_part = None # idem

        self.pension_alimentaire = None
        self.children = dict() # {noi: {'non_custodian': None, 'temps_garde': None, 'pension_alim': None}
        # du point de vue du parent non gardien
        # garde_classique
        # garde_alternée
        # garde_réduite

        self.new_households = dict() # For example { 'chef': { 'so': 1, 'loyer' : 500}}
        self.uc = dict()

    def break_union(self):
        """
        définition d'une méthode qui va changer les attributs d'une instance de Désunion
        """

        scenario = self.scenario # ATTRIBUT DE LA CLASSE ScenarioSimulation et 
        # une INSTANCE de la classe Scenario
        scenario_chef = self.Scenario()
        """
        scenario_chef est donc défini comme une instance de la classe Scenario, une classe d'objet
        dont l'__init__ n'appelle pas d'autre argument que self. Ce qui est bizarre, 
        c'est que cette classe Scenario n'apparaît que dans les utils de france.
        """
        scenario_part = self.Scenario()
        scenario_chef.year = self.datesim.year
        '''
        scenario_chef a un attribut year car toute instance de la classe Scenario peut/ avoir 
        un tel attribut. On lui donne la valeur de l'attribut year de l'attribut datesim 
        de DesunionSimulation. Je ne comprends pas bien ces chaînes d'attributs à moins que ce ne soit
        des sous-classes de classes ??
        '''
        scenario_part.year = self.datesim.year
        """
        datesim est une instance de la classe datetime et c'est aussi un attribut de la classe
        Simulation. datesim.year est un attribut de l'instance datesim
        """

        sal_chef = scenario.indiv[0]['sali']   # Could be more general
        """
        ce que je comprends, c'est qu'on va chercher dans notre scenario, instance de Scenario, 
        l'attribut indiv, qui est un dico de dico, et que l'on cherche le salaire de l'individu 0. 
        sal_chef aura donc pour valeur celle du salaire de cet individu.
        """
        scenario_chef.indiv[0].update({'sali': sal_chef })
        """
        notre scenario_chef, est comme on l'a vu,une instance de la classe Scenario,
        donc il a comme attribut indiv, un dico de dico. Ici, pour l'individu 0 de ce scenario, 
        on attribut pour la clé 'sali', la valeur sal_chef précédemment définie        
        """
        sal_part = scenario.indiv[1]['sali']   # Could be more general
        scenario_part.indiv[0].update({'sali': sal_part })
        """
        même manip, mais cette fois avec le scenario scenario_part, pour lequel on renseigne la
        valeur du salaire de l'individu 0, qui était l'individu 1 dans le scenario d'avant
        la séparation
        """
        # TODO: get more infos from couple scenario

        noi_enf_part = 1 
        noi_enf_chef = 1
        alv_chef = 0
        alv_part = 0
        alr_chef = 0
        alr_part = 0
        
        for noi, val in self.children.iteritems(): 
            """
            self.children est un attribut de ScenarioDesunion qui est un dico de dico. Dans ce dico, on a les caractéristiques
            de l'enfant, dont l'âge, 
            """
            non_custodian = val['non_custodian']
            """
            je définis la valeur non_custodian comme la valeur de la variable qui se trouve en face de la
            clé 'non_custodian' dans mon dico des enfants, pour l'enfant noi. cette variable peut prendre 
            pour valeur 'chef' ou 'part'
            """
            temps_garde = val['temps_garde']
            pension_alim = val['pension_alim']
            """
            Ici on raisonne sur le temps de garde dont bénéficie le parent non gardien et sur le montant de la pension
            qu'il paye pour l'enfant en question
            """
            birth = scenario.indiv[noi]['birth']
            """
            ici, on cherche à récupérer la date de naissance des enfants, qui se trouve dans 
            le dictionnaire des individus de notre scenario de Scenario
            """


            if temps_garde in ['classique', 'reduite']:

                if non_custodian == 'chef':
                    scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf') 
                    """
                    addIndiv est une méthode de la classe Scenario dont scenario_part est
                    une instance. Ici, on ajoute un enfant au scenario_part puisque c'est l'ex
                    partenaire du couple avant séparation qui a la garde.
                    """
                    noi_enf_part += 1
                    """
                    on prépare l'itération suivante de la boucle qui commence à for noi, val
                    """
                    alv_chef += pension_alim
                    alr_part += pension_alim
                elif non_custodian == 'part':
                    scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf') 
                    noi_enf_chef += 1
                    alv_part += pension_alim
                    alr_chef += pension_alim  
                
            elif temps_garde == 'alternee':# garde alternée fiscale = pas de pension alimentaire
                """
                ici, on raisonne en termes fiscaux. La garde alternée se définit par le partage du quotient familial d'où l'ajout 
                d'une personne à charge pour les deux parents et a priori, par l'absence de pension alimentaire. A vérifier, mais
                 il semble bien qu'on ne puisse à la fois bénéficier du partage du QF et de la déduction de la pension 
                 alimentaire du revenu imposable pour celui qui la verse
                """
                scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf')
                scenario_part.indiv[noi_enf_part].update('alt', 1)
                noi_enf_part += 1
                
                scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf')
                scenario_chef.indiv[noi_enf_part].update('alt', 1)
                noi_enf_chef += 1
                
            elif temps_garde == 'alternee juridique':# TODO: garde alternée pas de pension alimentaire ?
                                            # garde alternée juridique ou pas
                """
                ??? ATTENTION : ici, on traite le cas où les ex conjoints décident de déclarer une pension alimentaire. Donc a priori
                on ne doit pas avoir de 'alt' dans l'expression ci-dessous. Il faut que l'on distingue trois cas dans le cas de 
                la garde alternée : un cas où il n'y a effectivement pas de pension versée pour les enfants. Un cas où une pension est
                versée mais non déclarée car les ex parents décident de se partager la pension le QF. Un cas où une pension est versée
                et où les parents décident de ne pas se partager le QF mais de déclarer la pension dans la déclaration d'impôt
                """
                scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf')
                scenario_part.indiv[noi_enf_part].update('alt', 1)
                noi_enf_part += 1
                
                scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf')
                scenario_chef.indiv[noi_enf_part].update('alt', 1)
                noi_enf_chef += 1
                # TODO: modify here
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
            if parent == 'chef': # ??? je ne comprends pas trop : parent est une clé du dico new_households ?
                for key, val in variables:
                    scenario_chef.menage[0].update({key: val}) # ???là non plus je ne comprends pas trop comment ça fonctionne
            elif parent == 'part':
                for key, val in variables:
                    scenario_part.menage[0].update({key: val})
                
        
        self.scenario_chef = scenario_chef
        self.scenario_part = scenario_part
        self.scenario_chef.nmen = 1 # ???
        self.scenario_part.nmen = 1 # ???
        
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

    def _compute(self, difference):
        """
        Computes data_dict  from scenari
        """
        from src.core.datatable import DataTable
        from src.core.utils import gen_output_data
        
        scenari = { 'couple' : self.scenario, # ??? ici on aurait pu écrire juste scenario ou bien s'agissait-il
                   # d'une variable locale valable uniquement dans la définition de la méthode
                   # create_unt 
                    'chef'   : self.scenario_chef,
                    'part'   : self.scenario_part }
        datas = dict()
        
        for name, scenario in scenari.iteritems():
            input_table = DataTable(self.InputTable, scenario = scenario, datesim = self.datesim, country = self.country)
            output, output_default = self._preproc(input_table) # pourquoi cette fois-ci scenario et pas self.scenario ?
        
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
    
    def _compute_nivvie(self):
        """
        Compute nivvie and append it to dataframe
        """

        def _uc(age):
            '''
            Calcule le nombre d'unités de consommation du ménage avec l'échelle de l'insee
            à partir des age en mois des individus
            ??? AGE EN ANNEE PLUTOT NON ? 
            '''
            uc_adt = 0.5
            uc_enf = 0.3
            uc = 0.5
            for ag in age.itervalues():
                adt = (15 <= ag) & (ag <= 150)
                enf = (0  <= ag) & (ag <= 14)
                uc += adt*uc_adt + enf*uc_enf
            return uc
        
        self.uc = dict()
        scenari = { 'couple' : self.scenario, 
                    'chef'   : self.scenario_chef, 
                    'part'   : self.scenario_part }

        for name, scenario in scenari.iteritems():
            age = dict()
            for noi, var in scenario.indiv.iteritems():
                age[noi] = int((self.datesim - var['birth']).days/365.25)
            print name, age, _uc(age)        
            self.uc[name]= _uc(age) # la clé name dans uc[name] renvoie aux trois sous scenario couple, part et chef 
        
    def get_results_dataframe(self, default = False, difference = True, index_by_code = False):
        '''
        Formats data into a dataframe
        '''

        datas = self._compute(difference)
        self._compute_nivvie()
        uc = self.uc
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
                    if row.code == 'revdisp':
                        revdisp = row.vals
                    if index_by_code is True:
                        index.append(row.code)
                        data_dict[row.code] = row.vals
                    else:
                        index.append(row.desc)
                        data_dict[row.desc] = row.vals
            

            df = DataFrame(data_dict).T
            df = df.reindex(index)
            df = df.rename(columns = {0: scenario})
            nivvie = revdisp/uc[scenario] 
            df = df.set_value('nivvie', scenario, nivvie)
            dfs[scenario] = df
            
        
        first = True

        for df in dfs.itervalues():
            if first:
                df_final = df
                first = False
            else:
                df_final = concat([df_final, df], axis=1, join ="inner")
        df_final = df_final # pourquoi rajouter cette ligne ? 
        
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
    print desunion.scenario
    print desunion.scenario_chef
    print desunion.scenario_part
    desunion._compute_nivvie()
    print df
    print df.to_string()

#    df.to_excel(destination_dir + 'file.xlsx', sheet_name='desunion')

    
    def pension_par_enfant(rev_deb, nb_enf, temps_garde):
        """
        Parameters
        ----------
        rev_deb   : revenu du parent débiteur
        nb_enf : nombre d'enfant du parent débiteur qui sont en garde chez le parent créditeur
        temps_garde : amplitude du droit de visite
        
        Returns
        -------
        """
        min_vital = 475
        
        coef = {'1': .18,
                '2': .31,
                '3': .40, 
                '4': .47,
                '5': .53,
                '6': .57}
        
        pension = (rev_deb - 475)
        if temps_garde == "classique":
            pension = pension*coef[str(nb_enf)]*.75 # TODO arrondi au .5 point de pourcentage à faire
            
        elif temps_garde == "reduite":
            pension = pension*coef[str(nb_enf)]
            
        elif temps_garde == "alternee":
            pension = pension*coef[str(nb_enf)]/2